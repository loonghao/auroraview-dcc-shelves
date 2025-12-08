#!/usr/bin/env python
"""
Simple UI Test Script for DCC Shelves

This script can be run directly to test the UI without pytest.
It creates a WebView, loads the frontend, and runs basic assertions.

Usage:
    python tests/test_ui_simple.py
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

DIST_DIR = PROJECT_ROOT / "dist"


def run_tests():
    """Run UI tests."""
    from auroraview import WebView
    from auroraview.utils import get_auroraview_entry_url

    logger.info("=" * 60)
    logger.info("DCC Shelves UI Test")
    logger.info("=" * 60)

    # Check if dist exists
    if not (DIST_DIR / "index.html").exists():
        logger.error(f"dist/index.html not found at {DIST_DIR}")
        logger.error("Please run 'npm run build' first")
        return 1

    # Create mock API
    class TestShelfAPI:
        def get_config(self, **kwargs) -> dict:
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
                                "description": "A test tool",
                                "description_zh": "一个测试工具",
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
                        ],
                    },
                ],
                "dcc_mode": "desktop",
            }

        def launch_tool(self, button_id: str = "") -> dict:
            logger.info(f"launch_tool called: {button_id}")
            return {"success": True, "message": f"Launched {button_id}", "buttonId": button_id}

        def get_user_tools(self, **kwargs) -> dict:
            return {"success": True, "tools": []}

        def save_user_tool(self, **kwargs) -> dict:
            return {"success": True, "message": "Tool saved"}

        def delete_user_tool(self, id: str = "") -> dict:
            return {"success": True, "message": "Tool deleted"}

        def create_window(self, **kwargs) -> dict:
            return {"success": True, "label": kwargs.get("label", "")}

        def close_window(self, **kwargs) -> dict:
            return {"success": True}

    # Create WebView
    logger.info("Creating WebView...")
    webview = WebView(
        title="DCC Shelves Test",
        width=380,
        height=700,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    # Track ready state
    ready_event = threading.Event()
    test_results = {"passed": 0, "failed": 0, "errors": []}

    @webview.on("__auroraview_ready")
    def on_ready(data):
        url = data.get("url", "")
        logger.info(f"WebView ready: {url}")
        webview.bind_api(api, allow_rebind=True)
        ready_event.set()

    # Bind API
    api = TestShelfAPI()
    webview.bind_api(api)

    # Load URL
    load_url = get_auroraview_entry_url("index.html")
    logger.info(f"Loading URL: {load_url}")
    webview.load_url(load_url)

    def run_assertions():
        """Run test assertions after WebView is ready."""
        nonlocal test_results

        # Wait for ready
        logger.info("Waiting for WebView to be ready...")
        if not ready_event.wait(timeout=15):
            logger.error("Timeout waiting for WebView to be ready")
            test_results["failed"] += 1
            test_results["errors"].append("WebView not ready")
            return

        # Additional delay for React to render
        time.sleep(2.0)

        logger.info("\n" + "=" * 60)
        logger.info("Running Tests...")
        logger.info("=" * 60 + "\n")

        def assert_test(name: str, condition: bool, message: str = ""):
            if condition:
                logger.info(f"✓ PASS: {name}")
                test_results["passed"] += 1
            else:
                logger.error(f"✗ FAIL: {name} - {message}")
                test_results["failed"] += 1
                test_results["errors"].append(f"{name}: {message}")

        # Test 1: Root element exists
        result = webview.eval_js("document.getElementById('root') !== null")
        assert_test("Root element exists", result is True)

        # Test 2: App is rendered
        result = webview.eval_js("document.getElementById('root').children.length > 0")
        assert_test("App is rendered", result is True)

        # Test 3: Banner title is displayed
        result = webview.eval_js("""
            const title = document.querySelector('h1, .text-lg.font-semibold');
            title ? title.textContent : null;
        """)
        assert_test("Banner title displayed", result is not None, f"Got: {result}")

        # Test 4: Search input exists
        result = webview.eval_js("document.querySelector('input[type=\"text\"]') !== null")
        assert_test("Search input exists", result is True)

        # Test 5: Tool buttons are rendered
        result = webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const toolBtns = Array.from(buttons).filter(btn => btn.querySelector('svg'));
            toolBtns.length;
        """)
        assert_test("Tool buttons rendered", result and result > 0, f"Found {result} buttons")

        # Test 6: Bottom panel tabs exist
        result = webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Detail') || text.includes('详情');
        """)
        assert_test("Detail tab exists", result is True)

        result = webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Console') || text.includes('控制台');
        """)
        assert_test("Console tab exists", result is True)

        # Test 7: User Tools section exists
        result = webview.eval_js("""
            const text = document.body.innerText;
            text.includes('User Tools') || text.includes('用户工具');
        """)
        assert_test("User Tools section exists", result is True)

        # Test 8: No React errors
        result = webview.eval_js("""
            const text = document.body.innerText;
            !text.includes('Something went wrong') && !text.includes('Error boundary');
        """)
        assert_test("No React errors", result is True)

        # Test 9: Search functionality
        webview.eval_js("""
            const input = document.querySelector('input[type="text"]');
            if (input) {
                input.value = 'test';
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        """)
        time.sleep(0.5)
        result = webview.eval_js("document.querySelector('input[type=\"text\"]').value")
        assert_test("Search input accepts text", result == "test", f"Got: {result}")

        # Clear search
        webview.eval_js("""
            const input = document.querySelector('input[type="text"]');
            if (input) {
                input.value = '';
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        """)

        # Test 10: Tool button click
        result = webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const toolBtn = Array.from(buttons).find(btn => {
                const hasIcon = btn.querySelector('svg');
                const text = btn.textContent.trim();
                return hasIcon && text.length > 0;
            });
            if (toolBtn) {
                toolBtn.click();
                true;
            } else {
                false;
            }
        """)
        assert_test("Tool button clickable", result is True)

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        logger.info(f"Passed: {test_results['passed']}")
        logger.info(f"Failed: {test_results['failed']}")

        if test_results["errors"]:
            logger.info("\nErrors:")
            for error in test_results["errors"]:
                logger.info(f"  - {error}")

        logger.info("=" * 60)

        # Close after tests
        time.sleep(1)
        logger.info("Tests complete. Closing window...")
        webview.close()

    # Run assertions in a separate thread
    test_thread = threading.Thread(target=run_assertions, daemon=True)
    test_thread.start()

    # Show window and run event loop
    logger.info("Starting WebView...")
    webview.show_blocking()

    # Wait for test thread to finish
    test_thread.join(timeout=5)

    return 0 if test_results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
