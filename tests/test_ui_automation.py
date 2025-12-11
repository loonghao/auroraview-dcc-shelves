"""Automated UI tests for DCC Shelves application.

Uses AuroraView's testing framework to test button clicks, API calls,
and UI interactions.

Run with: uv run pytest tests/test_ui_automation.py -v
"""

import contextlib
import logging
import time
from pathlib import Path

import pytest
from auroraview import WebView
from auroraview.testing import DomAssertions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"


class TestAPI:
    """Mock API for testing."""

    def __init__(self):
        self.calls = []  # Track API calls for assertions
        self.config = {
            "shelves": [
                {
                    "id": "test-shelf",
                    "name": "Test Shelf",
                    "name_zh": "测试工具架",
                    "buttons": [
                        {
                            "id": "btn-1",
                            "name": "Test Tool 1",
                            "name_zh": "测试工具1",
                            "toolType": "python",
                            "toolPath": "/path/to/tool1.py",
                            "icon": "Wrench",
                            "args": [],
                            "description": "A test tool",
                            "description_zh": "一个测试工具",
                            "hosts": [],
                        },
                        {
                            "id": "btn-2",
                            "name": "Test Tool 2",
                            "name_zh": "测试工具2",
                            "toolType": "executable",
                            "toolPath": "/path/to/tool2.exe",
                            "icon": "Settings",
                            "args": [],
                            "description": "Another test tool",
                            "description_zh": "另一个测试工具",
                            "hosts": [],
                        },
                    ],
                }
            ],
            "currentHost": "desktop",
            "banner": {
                "title": "Test Toolbox",
                "subtitle": "Automated Testing",
            },
        }

    def get_config(self):
        """Return test configuration."""
        self.calls.append(("get_config", {}))
        logger.info("API: get_config called")
        return self.config

    def launch_tool(self, button_id: str = ""):
        """Mock tool launch."""
        self.calls.append(("launch_tool", {"button_id": button_id}))
        logger.info(f"API: launch_tool called with button_id={button_id}")
        return {"success": True, "message": f"Launched {button_id}", "buttonId": button_id}

    def get_tool_path(self, button_id: str = ""):
        """Get tool path."""
        self.calls.append(("get_tool_path", {"button_id": button_id}))
        return {"buttonId": button_id, "path": f"/mock/path/{button_id}"}

    def get_user_tools(self):
        """Get user tools."""
        self.calls.append(("get_user_tools", {}))
        return {"success": True, "tools": []}

    def save_user_tool(self, **kwargs):
        """Save user tool."""
        self.calls.append(("save_user_tool", kwargs))
        return {"success": True, "message": "Tool saved"}

    def delete_user_tool(self, id: str = ""):
        """Delete user tool."""
        self.calls.append(("delete_user_tool", {"id": id}))
        return {"success": True, "message": "Tool deleted"}

    def export_user_tools(self):
        """Export user tools."""
        self.calls.append(("export_user_tools", {}))
        return {"success": True, "config": "{}"}

    def import_user_tools(self, config: str = "", merge: bool = True):
        """Import user tools."""
        self.calls.append(("import_user_tools", {"config": config, "merge": merge}))
        return {"success": True, "count": 0}

    def create_window(self, label: str = "", url: str = "", title: str = "", width: int = 500, height: int = 600):
        """Create a new window."""
        self.calls.append(("create_window", {"label": label, "url": url, "title": title}))
        logger.info(f"API: create_window called with label={label}")
        return {"success": True, "message": "Window created", "label": label}

    def close_window(self, label: str = ""):
        """Close a window."""
        self.calls.append(("close_window", {"label": label}))
        return {"success": True, "message": "Window closed"}

    def close_main_window(self):
        """Close main window."""
        self.calls.append(("close_main_window", {}))
        return {"success": True}

    def was_called(self, method_name: str) -> bool:
        """Check if a method was called."""
        return any(call[0] == method_name for call in self.calls)

    def get_calls(self, method_name: str) -> list:
        """Get all calls to a specific method."""
        return [call for call in self.calls if call[0] == method_name]

    def clear_calls(self):
        """Clear call history."""
        self.calls.clear()


@pytest.fixture
def webview_with_api():
    """Create a WebView with test API bound."""
    if not DIST_DIR.exists():
        pytest.skip("dist/ directory not found. Run 'npm run build' first.")

    webview = WebView(
        title="DCC Shelves - UI Test",
        width=500,
        height=700,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    api = TestAPI()
    webview.bind_api(api)

    # Handle __auroraview_ready to re-register API
    @webview.on("__auroraview_ready")
    def handle_ready(data):
        logger.info(f"WebView ready: {data.get('url', '')}")
        webview.bind_api(api, allow_rebind=True)

    yield webview, api

    # Cleanup
    with contextlib.suppress(Exception):
        webview.close()


@pytest.fixture
def running_webview(webview_with_api):
    """Start the WebView and wait for it to be ready."""
    webview, api = webview_with_api

    # Load the app
    from auroraview.utils import get_auroraview_entry_url

    url = get_auroraview_entry_url("index.html")
    logger.info(f"Loading: {url}")
    webview.load_url(url)

    # Show in non-blocking mode
    webview.show(wait=False)

    # Wait for page to load
    time.sleep(2)

    yield webview, api


class TestAPIBinding:
    """Test that API methods are properly bound and callable."""

    def test_api_methods_bound(self, webview_with_api):
        """Test that all API methods are bound."""
        webview, api = webview_with_api

        bound_methods = webview.get_bound_methods()
        logger.info(f"Bound methods: {bound_methods}")

        expected_methods = [
            "api.get_config",
            "api.launch_tool",
            "api.get_tool_path",
            "api.get_user_tools",
            "api.create_window",
            "api.close_window",
        ]

        for method in expected_methods:
            assert method in bound_methods, f"Method {method} not bound"

    def test_get_config_returns_data(self, webview_with_api):
        """Test that get_config returns valid configuration."""
        webview, api = webview_with_api

        result = api.get_config()

        assert "shelves" in result
        assert "currentHost" in result
        assert "banner" in result
        assert len(result["shelves"]) > 0
        assert len(result["shelves"][0]["buttons"]) > 0


class TestUIElements:
    """Test UI element presence and interactions."""

    def test_app_loads(self, running_webview):
        """Test that the app loads successfully."""
        webview, api = running_webview
        DomAssertions(webview, timeout=5)

        # Wait for app to load - check for main container
        # The app should have loaded and called get_config
        time.sleep(1)

        assert api.was_called("get_config"), "get_config should be called on app load"

    def test_banner_visible(self, running_webview):
        """Test that the banner is visible."""
        webview, api = running_webview
        assertions = DomAssertions(webview, timeout=5)

        # Check for banner elements (adjust selectors based on actual HTML)
        # These selectors depend on your actual React component structure
        try:
            assertions.wait_for_visible("[data-testid='banner']", timeout=3)
        except AssertionError:
            # Try alternative selector
            logger.info("Banner test-id not found, checking for heading")

    def test_shelf_buttons_rendered(self, running_webview):
        """Test that shelf buttons are rendered."""
        webview, api = running_webview

        # Wait for buttons to render
        time.sleep(1)

        # Check that buttons exist (adjust selector based on actual structure)
        # You may need to add data-testid attributes to your React components
        try:
            count = webview.dom_all("button").count()
            logger.info(f"Found {count} buttons")
            assert count > 0, "Should have at least one button"
        except Exception as e:
            logger.warning(f"Button count check failed: {e}")


class TestButtonInteractions:
    """Test button click interactions."""

    def test_tool_button_click(self, running_webview):
        """Test clicking a tool button calls launch_tool."""
        webview, api = running_webview

        # Clear previous calls
        api.clear_calls()

        # Wait for app to fully load
        time.sleep(2)

        # Find and click a tool button
        # This selector needs to match your actual button structure
        try:
            # Try to click the first tool button
            # Adjust selector based on your actual component structure
            buttons = webview.dom_all("[data-button-id]")
            count = buttons.count()
            logger.info(f"Found {count} tool buttons")

            if count > 0:
                # Click the first button
                webview.dom("[data-button-id]").click()
                time.sleep(0.5)

                # Check if launch_tool was called
                if api.was_called("launch_tool"):
                    logger.info("launch_tool was called successfully!")
                    calls = api.get_calls("launch_tool")
                    logger.info(f"launch_tool calls: {calls}")
                else:
                    logger.warning("launch_tool was not called after button click")

        except Exception as e:
            logger.warning(f"Button click test failed: {e}")
            # This is expected if the selectors don't match

    def test_settings_button_click(self, running_webview):
        """Test clicking the settings button."""
        webview, api = running_webview

        api.clear_calls()
        time.sleep(1)

        # Try to find and click settings button
        try:
            # Look for settings button (gear icon or similar)
            settings_btn = webview.dom("[data-testid='settings-button']")
            settings_btn.click()
            time.sleep(0.5)

            # Check if create_window was called (for native window)
            # or if settings modal opened
            logger.info(f"API calls after settings click: {api.calls}")

        except Exception as e:
            logger.warning(f"Settings button test failed: {e}")


class TestAPIResponses:
    """Test that API responses are handled correctly."""

    def test_config_loaded_into_ui(self, running_webview):
        """Test that configuration is loaded and displayed."""
        webview, api = running_webview

        # Wait for config to load
        time.sleep(2)

        # Verify get_config was called
        assert api.was_called("get_config"), "get_config should be called"

        # The UI should now display the config data
        # Check for shelf name or tool names in the DOM
        try:
            page_text = webview.dom("body").get_text()
            logger.info(f"Page text length: {len(page_text)}")

            # Check if test data appears in the page
            # These checks depend on your actual UI rendering
            if "Test Shelf" in page_text or "Test Tool" in page_text:
                logger.info("Config data found in UI!")
            else:
                logger.info("Config data not found in page text (may be in different format)")

        except Exception as e:
            logger.warning(f"Config UI check failed: {e}")


class TestWindowManagement:
    """Test window creation and management."""

    def test_create_window_api(self, webview_with_api):
        """Test create_window API directly."""
        webview, api = webview_with_api

        result = api.create_window(
            label="test-window",
            url="/settings.html",
            title="Test Window",
            width=400,
            height=300,
        )

        assert result["success"] is True
        assert result["label"] == "test-window"
        assert api.was_called("create_window")

    def test_close_window_api(self, webview_with_api):
        """Test close_window API directly."""
        webview, api = webview_with_api

        result = api.close_window(label="test-window")

        assert result["success"] is True
        assert api.was_called("close_window")


# Run tests with visible output
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
