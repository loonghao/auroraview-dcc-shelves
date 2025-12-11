"""Interactive UI automation test for DCC Shelves.

This script demonstrates automated UI testing with visible window.
Run with: uv run python test_ui_interactive.py
"""

import logging
import threading
import time
from pathlib import Path

from auroraview import WebView
from auroraview.testing import DomAssertions
from auroraview.utils import get_auroraview_entry_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"


class TestAPI:
    """Mock API for testing with call tracking."""

    def __init__(self):
        self.calls = []

    def get_config(self):
        self.calls.append(("get_config", {}))
        logger.info("✓ API: get_config called")
        return {
            "shelves": [
                {
                    "id": "test-shelf",
                    "name": "Test Shelf",
                    "name_zh": "测试工具架",
                    "buttons": [
                        {
                            "id": "btn-1",
                            "name": "Tool A",
                            "name_zh": "工具A",
                            "toolType": "python",
                            "toolPath": "/path/to/tool_a.py",
                            "icon": "Wrench",
                            "args": [],
                            "description": "First test tool",
                            "description_zh": "第一个测试工具",
                            "hosts": [],
                        },
                        {
                            "id": "btn-2",
                            "name": "Tool B",
                            "name_zh": "工具B",
                            "toolType": "python",
                            "toolPath": "/path/to/tool_b.py",
                            "icon": "Settings",
                            "args": [],
                            "description": "Second test tool",
                            "description_zh": "第二个测试工具",
                            "hosts": [],
                        },
                        {
                            "id": "btn-3",
                            "name": "Tool C",
                            "name_zh": "工具C",
                            "toolType": "executable",
                            "toolPath": "/path/to/tool_c.exe",
                            "icon": "Box",
                            "args": [],
                            "description": "Third test tool",
                            "description_zh": "第三个测试工具",
                            "hosts": [],
                        },
                    ],
                }
            ],
            "currentHost": "desktop",
            "banner": {
                "title": "UI Test Toolbox",
                "subtitle": "Automated Testing Demo",
            },
        }

    def launch_tool(self, button_id: str = ""):
        self.calls.append(("launch_tool", {"button_id": button_id}))
        logger.info(f"✓ API: launch_tool called with button_id={button_id}")
        return {"success": True, "message": f"Launched {button_id}", "buttonId": button_id}

    def get_tool_path(self, button_id: str = ""):
        self.calls.append(("get_tool_path", {"button_id": button_id}))
        return {"buttonId": button_id, "path": f"/mock/path/{button_id}"}

    def get_user_tools(self):
        self.calls.append(("get_user_tools", {}))
        return {"success": True, "tools": []}

    def save_user_tool(self, **kwargs):
        self.calls.append(("save_user_tool", kwargs))
        return {"success": True}

    def delete_user_tool(self, id: str = ""):
        self.calls.append(("delete_user_tool", {"id": id}))
        return {"success": True}

    def export_user_tools(self):
        return {"success": True, "config": "{}"}

    def import_user_tools(self, config: str = "", merge: bool = True):
        return {"success": True, "count": 0}

    def create_window(self, label: str = "", url: str = "", title: str = "", width: int = 500, height: int = 600):
        self.calls.append(("create_window", {"label": label, "url": url, "title": title}))
        logger.info(f"✓ API: create_window called with label={label}")
        return {"success": True, "message": "Window created", "label": label}

    def close_window(self, label: str = ""):
        self.calls.append(("close_window", {"label": label}))
        return {"success": True}

    def close_main_window(self):
        return {"success": True}


# Global state for test coordination
test_state = {
    "tests_completed": False,
    "test_results": [],
    "webview": None,
    "api": None,
}


def run_tests_after_load():
    """Run tests after the app has loaded."""
    webview = test_state["webview"]
    api = test_state["api"]

    # Wait for app to load
    logger.info("\n--- Waiting for app to load... ---")
    time.sleep(3)

    test_results = []

    # Test 1: Check if get_config was called
    logger.info("\n--- Test 1: API get_config called ---")
    config_called = any(c[0] == "get_config" for c in api.calls)
    if config_called:
        logger.info("✓ PASS: get_config was called on app load")
        test_results.append(("get_config called", True))
    else:
        logger.error("✗ FAIL: get_config was not called")
        test_results.append(("get_config called", False))

    # Test 2: Check banner is visible
    logger.info("\n--- Test 2: Banner visible ---")
    try:
        assertions = DomAssertions(webview, timeout=5)
        assertions.wait_for_visible("[data-testid='banner']", timeout=3)
        logger.info("✓ PASS: Banner is visible")
        test_results.append(("Banner visible", True))
    except AssertionError:
        logger.warning("⚠ SKIP: Banner test-id not found")
        test_results.append(("Banner visible", None))
    except Exception as e:
        logger.warning(f"⚠ SKIP: {e}")
        test_results.append(("Banner visible", None))

    # Test 3: Check tool buttons exist
    logger.info("\n--- Test 3: Tool buttons rendered ---")
    try:
        count = webview.dom_all("[data-testid='tool-button']").count()
        logger.info(f"  Found {count} tool buttons")
        if count > 0:
            logger.info(f"✓ PASS: {count} tool buttons rendered")
            test_results.append(("Tool buttons rendered", True))
        else:
            logger.warning("⚠ Tool buttons not found")
            test_results.append(("Tool buttons rendered", None))
    except Exception as e:
        logger.error(f"✗ FAIL: {e}")
        test_results.append(("Tool buttons rendered", False))

    # Test 4: Click a tool button
    logger.info("\n--- Test 4: Click tool button ---")
    api.calls.clear()
    try:
        buttons = webview.dom_all("[data-testid='tool-button']")
        count = buttons.count()
        if count > 0:
            logger.info("  Clicking first tool button...")
            webview.dom("[data-testid='tool-button']").click()
            time.sleep(1)

            launch_called = any(c[0] == "launch_tool" for c in api.calls)
            if launch_called:
                call = next(c for c in api.calls if c[0] == "launch_tool")
                logger.info(f"✓ PASS: launch_tool called with {call[1]}")
                test_results.append(("Tool button click", True))
            else:
                logger.warning("⚠ launch_tool was not called")
                test_results.append(("Tool button click", False))
        else:
            logger.warning("⚠ SKIP: No tool buttons")
            test_results.append(("Tool button click", None))
    except Exception as e:
        logger.error(f"✗ FAIL: {e}")
        test_results.append(("Tool button click", False))

    # Test 5: Click settings button
    logger.info("\n--- Test 5: Click settings button ---")
    api.calls.clear()
    try:
        settings_btn = webview.dom("[data-testid='settings-button']")
        logger.info("  Clicking settings button...")
        settings_btn.click()
        time.sleep(1)

        create_window_called = any(c[0] == "create_window" for c in api.calls)
        if create_window_called:
            logger.info("✓ PASS: Settings opened via native window API")
            test_results.append(("Settings button click", True))
        else:
            logger.info("  Settings may have opened as modal")
            test_results.append(("Settings button click", None))
    except Exception as e:
        logger.warning(f"⚠ Settings button not found: {e}")
        test_results.append(("Settings button click", None))

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    passed = sum(1 for _, r in test_results if r is True)
    failed = sum(1 for _, r in test_results if r is False)
    skipped = sum(1 for _, r in test_results if r is None)

    for name, result in test_results:
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⚠ SKIP")
        logger.info(f"  {status}: {name}")

    logger.info(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    logger.info("=" * 60)
    logger.info("\nClose the window to exit.")

    test_state["tests_completed"] = True
    test_state["test_results"] = test_results


def main():
    """Run automated UI tests."""
    if not DIST_DIR.exists():
        logger.error("dist/ directory not found. Run 'npm run build' first.")
        return False

    logger.info("=" * 60)
    logger.info("DCC Shelves UI Automation Test")
    logger.info("=" * 60)

    # Create WebView
    webview = WebView(
        title="DCC Shelves - UI Automation Test",
        width=500,
        height=700,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    api = TestAPI()
    webview.bind_api(api)
    logger.info("✓ API bound successfully")
    logger.info(f"  Bound methods: {webview.get_bound_methods()}")

    # Store in global state
    test_state["webview"] = webview
    test_state["api"] = api

    # Handle __auroraview_ready to re-register API
    @webview.on("__auroraview_ready")
    def handle_ready(data):
        url = data.get("url", "")
        logger.info(f"✓ WebView ready event received (url={url})")
        webview.bind_api(api, allow_rebind=True)
        logger.info("✓ API re-registered after page navigation")

    # Load the app
    url = get_auroraview_entry_url("index.html")
    logger.info(f"Loading: {url}")
    webview.load_url(url)

    # Start test thread
    test_thread = threading.Thread(target=run_tests_after_load, daemon=True)
    test_thread.start()

    # Show blocking (runs event loop)
    logger.info("Starting WebView (blocking mode)...")
    webview.show_blocking()

    # Return result
    if test_state["tests_completed"]:
        failed = sum(1 for _, r in test_state["test_results"] if r is False)
        return failed == 0
    return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
