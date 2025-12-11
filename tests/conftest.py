"""
DCC Shelves UI Test Configuration

This module provides pytest fixtures for testing the actual DCC Shelves frontend.
Tests use the real project frontend (via Vite dev server or dist build).
"""

from __future__ import annotations

import atexit
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Generator

import pytest

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

logger = logging.getLogger(__name__)

# Check if auroraview is available
try:
    from auroraview import WebView
    from auroraview.testing import DomAssertions

    AURORAVIEW_AVAILABLE = True
except ImportError:
    AURORAVIEW_AVAILABLE = False
    WebView = None
    DomAssertions = None


# =============================================================================
# Constants
# =============================================================================

DIST_DIR = PROJECT_ROOT / "dist"
DEV_SERVER_URL = "http://localhost:5173"
SETTINGS_PAGE = "/settings.html"

# Default window configuration
DEFAULT_WIDTH = 380
DEFAULT_HEIGHT = 700
DEFAULT_TITLE = "DCC Shelves Test"

# Track all webviews for cleanup
_active_webviews: list = []


# =============================================================================
# Helper Functions
# =============================================================================


def is_dist_available() -> bool:
    """Check if dist build exists."""
    return (DIST_DIR / "index.html").exists()


def is_dev_server_running() -> bool:
    """Check if Vite dev server is running."""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 5173))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_dev_server() -> subprocess.Popen | None:
    """Start Vite dev server if not running."""
    if is_dev_server_running():
        logger.info("Dev server already running")
        return None

    logger.info("Starting Vite dev server...")
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    # Wait for server to start
    for _ in range(30):  # 30 seconds timeout
        if is_dev_server_running():
            logger.info("Dev server started successfully")
            return process
        time.sleep(1)

    logger.error("Failed to start dev server")
    process.terminate()
    return None


def _cleanup_webviews():
    """Cleanup all active webviews at exit."""
    for wv in _active_webviews:
        try:
            wv.close()
        except Exception:
            pass
    _active_webviews.clear()


# Register cleanup at exit
atexit.register(_cleanup_webviews)


# =============================================================================
# Mock API for Testing
# =============================================================================


class TestShelfAPI:
    """Mock API for testing the DCC Shelves frontend."""

    def get_config(self, **kwargs) -> dict:
        """Return test configuration."""
        return {
            "banner": {
                "title": "Test Shelf",
                "subtitle": "Testing Mode",
                "icon": "Wrench",
            },
            "shelves": [
                {
                    "id": "test-shelf",
                    "name": "Test Tools",
                    "name_zh": "测试工具",
                    "buttons": [
                        {
                            "id": "test-tool-1",
                            "name": "Test Tool 1",
                            "name_zh": "测试工具1",
                            "icon": "Wrench",
                            "description": "A test tool for testing",
                            "description_zh": "一个用于测试的工具",
                            "tool_type": "python",
                            "tool_path": "test.py",
                        },
                        {
                            "id": "test-tool-2",
                            "name": "Test Tool 2",
                            "name_zh": "测试工具2",
                            "icon": "Settings",
                            "description": "Another test tool",
                            "description_zh": "另一个测试工具",
                            "tool_type": "python",
                            "tool_path": "test2.py",
                        },
                        {
                            "id": "test-tool-3",
                            "name": "Test Tool 3",
                            "name_zh": "测试工具3",
                            "icon": "Folder",
                            "description": "Third test tool",
                            "description_zh": "第三个测试工具",
                            "tool_type": "python",
                            "tool_path": "test3.py",
                        },
                    ],
                },
            ],
            "dcc_mode": "desktop",
        }

    def launch_tool(self, button_id: str = "") -> dict:
        """Mock tool launch."""
        logger.info(f"Mock launch_tool called: {button_id}")
        return {"success": True, "message": f"Launched {button_id}", "buttonId": button_id}

    def get_user_tools(self, **kwargs) -> dict:
        """Return empty user tools."""
        return {"success": True, "tools": []}

    def save_user_tool(self, **kwargs) -> dict:
        """Mock save user tool."""
        return {"success": True, "message": "Tool saved"}

    def delete_user_tool(self, id: str = "") -> dict:
        """Mock delete user tool."""
        return {"success": True, "message": "Tool deleted"}

    def create_window(self, **kwargs) -> dict:
        """Mock create window."""
        return {"success": True, "label": kwargs.get("label", "")}

    def close_window(self, **kwargs) -> dict:
        """Mock close window."""
        return {"success": True}


# =============================================================================
# Pytest Hooks
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "ui: mark test as UI test (requires display)")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "headless: mark test as headless (no display required)")
    config.addinivalue_line("markers", "requires_dev_server: mark test as requiring Vite dev server")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def dist_dir() -> Path:
    """Get dist directory."""
    return DIST_DIR


@pytest.fixture(scope="session")
def dev_server_url() -> str:
    """Get dev server URL."""
    return DEV_SERVER_URL


@pytest.fixture(scope="session")
def ensure_frontend(project_root: Path) -> str | None:
    """Ensure frontend is available (dev server or dist build).

    Returns the base URL to use for loading the frontend, or None for dist mode.
    """
    # Prefer dev server for faster iteration
    if is_dev_server_running():
        logger.info("Using existing dev server")
        return DEV_SERVER_URL

    # Check if dist exists
    if is_dist_available():
        logger.info("Using dist build")
        return None  # Will use auroraview:// protocol

    pytest.skip("No frontend available (dev server not running and dist not built)")


@pytest.fixture(scope="module")
def shelf_webview(ensure_frontend: str | None) -> Generator[WebView, None, None]:
    """Create a WebView with the actual DCC Shelves frontend loaded.

    This fixture uses module scope to reuse the same WebView across tests
    in the same module, which is more efficient and avoids close/reopen issues.

    This fixture:
    1. Creates a WebView window
    2. Loads the actual project frontend (dev server or dist)
    3. Waits for the app to be ready
    4. Yields the WebView for testing
    5. Does NOT close the WebView (let process exit handle it)
    """
    if not AURORAVIEW_AVAILABLE:
        pytest.skip("auroraview not available")

    # Determine asset root and URL
    if ensure_frontend:
        # Dev server mode
        asset_root = None
        load_url = ensure_frontend
    else:
        # Dist mode
        asset_root = str(DIST_DIR)
        from auroraview.utils import get_auroraview_entry_url

        load_url = get_auroraview_entry_url("index.html")

    # Create WebView
    webview = WebView(
        title=DEFAULT_TITLE,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        debug=True,
        context_menu=True,
        asset_root=asset_root,
        decorations=True,
    )

    # Track for cleanup
    _active_webviews.append(webview)

    # Track ready state
    ready_event = threading.Event()

    @webview.on("__auroraview_ready")
    def on_ready(data):
        url = data.get("url", "")
        logger.info(f"WebView ready: {url}")
        # Re-bind API on page navigation
        webview.bind_api(api, allow_rebind=True)
        ready_event.set()

    # Create and bind mock API
    api = TestShelfAPI()
    webview.bind_api(api)

    # Load URL
    webview.load_url(load_url)

    # Show window (non-blocking for tests)
    webview.show(wait=False)

    # Wait for ready with timeout
    if not ready_event.wait(timeout=15):
        logger.warning("WebView did not become ready within timeout, continuing anyway")

    # Additional delay for React to render
    time.sleep(1.0)

    yield webview

    # Don't close here - let atexit handler deal with it
    # This avoids the panic issue during test cleanup


@pytest.fixture(scope="function")
def dom(shelf_webview: WebView) -> DomAssertions:
    """Create DomAssertions helper for the shelf WebView."""
    if not AURORAVIEW_AVAILABLE:
        pytest.skip("auroraview not available")
    return DomAssertions(shelf_webview)


@pytest.fixture(scope="module")
def settings_webview(ensure_frontend: str | None) -> Generator[WebView, None, None]:
    """Create a WebView with the settings page loaded."""
    if not AURORAVIEW_AVAILABLE:
        pytest.skip("auroraview not available")

    # Determine URL for settings page
    if ensure_frontend:
        load_url = f"{ensure_frontend}/settings.html"
        asset_root = None
    else:
        from auroraview.utils import get_auroraview_entry_url

        load_url = get_auroraview_entry_url("settings.html")
        asset_root = str(DIST_DIR)

    webview = WebView(
        title="Settings Test",
        width=500,
        height=600,
        debug=True,
        context_menu=True,
        asset_root=asset_root,
    )

    # Track for cleanup
    _active_webviews.append(webview)

    ready_event = threading.Event()

    @webview.on("__auroraview_ready")
    def on_ready(data):
        ready_event.set()

    webview.load_url(load_url)
    webview.show(wait=False)

    # Wait for ready
    ready_event.wait(timeout=15)
    time.sleep(1.0)

    yield webview

    # Don't close here - let atexit handler deal with it
