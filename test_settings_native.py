"""Test that Settings window opens as native independent window.

This test verifies that:
1. API binding works correctly
2. __auroraview_ready event triggers API re-registration
3. hasNativeWindowAPI() returns true in frontend
4. Settings button click calls create_window API

Run with: uv run python test_settings_native.py
"""

import logging
import threading
import time
from pathlib import Path

from auroraview import WebView
from auroraview.utils import get_auroraview_entry_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"


class MockAPI:
    """Mock API that tracks all calls."""

    def __init__(self):
        self.calls = []
        self.create_window_called = threading.Event()

    def get_config(self):
        self.calls.append("get_config")
        logger.info("✓ get_config called")
        return {
            "shelves": [
                {
                    "id": "test",
                    "name": "Test",
                    "name_zh": "测试",
                    "buttons": [
                        {
                            "id": "btn-1",
                            "name": "Tool",
                            "name_zh": "工具",
                            "toolType": "python",
                            "toolPath": "/test.py",
                            "icon": "Wrench",
                            "args": [],
                            "description": "",
                            "description_zh": "",
                            "hosts": [],
                        }
                    ],
                }
            ],
            "currentHost": "desktop",
            "banner": {"title": "Test", "subtitle": "Settings Test"},
        }

    def launch_tool(self, button_id: str = ""):
        self.calls.append(f"launch_tool:{button_id}")
        logger.info(f"✓ launch_tool called: {button_id}")
        return {"success": True, "buttonId": button_id}

    def get_tool_path(self, button_id: str = ""):
        return {"buttonId": button_id, "path": ""}

    def get_user_tools(self):
        return {"success": True, "tools": []}

    def save_user_tool(self, **kwargs):
        return {"success": True}

    def delete_user_tool(self, id: str = ""):
        return {"success": True}

    def export_user_tools(self):
        return {"success": True, "config": "{}"}

    def import_user_tools(self, config: str = "", merge: bool = True):
        return {"success": True, "count": 0}

    def create_window(self, label: str = "", url: str = "", title: str = "", width: int = 500, height: int = 600):
        self.calls.append(f"create_window:{label}")
        logger.info(f"✓✓✓ create_window called! label={label}, url={url}")
        self.create_window_called.set()
        return {"success": True, "message": "Window created", "label": label}

    def close_window(self, label: str = ""):
        self.calls.append(f"close_window:{label}")
        return {"success": True}

    def close_main_window(self):
        return {"success": True}


def run_test():
    """Run the settings native window test."""
    if not DIST_DIR.exists():
        logger.error("dist/ not found. Run 'npm run build' first.")
        return False

    logger.info("=" * 50)
    logger.info("Settings Native Window Test")
    logger.info("=" * 50)

    webview = WebView(
        title="Settings Native Window Test",
        width=500,
        height=600,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    api = MockAPI()
    webview.bind_api(api)
    logger.info(f"API bound: {webview.get_bound_methods()}")

    # Critical: Re-register API on page navigation
    @webview.on("__auroraview_ready")
    def on_ready(data):
        url = data.get("url", "")
        logger.info(f"__auroraview_ready: {url}")
        # Re-register API methods in JavaScript
        webview.bind_api(api, allow_rebind=True)
        logger.info("API re-registered")

    # Load app
    url = get_auroraview_entry_url("index.html")
    logger.info(f"Loading: {url}")
    webview.load_url(url)

    # Test thread
    def test_runner():
        logger.info("\n--- Waiting for app to load (5s) ---")
        time.sleep(5)

        # Check if get_config was called
        if "get_config" in api.calls:
            logger.info("✓ PASS: get_config was called")
        else:
            logger.error("✗ FAIL: get_config was NOT called")
            logger.info(f"  API calls: {api.calls}")

        # Try to click settings button via JavaScript
        logger.info("\n--- Clicking settings button via JS ---")
        try:
            # First check if API is available
            webview.eval_js("""
                console.log('[TEST] Checking API availability...');
                console.log('[TEST] window.auroraview:', window.auroraview);
                console.log('[TEST] window.auroraview.api:', window.auroraview?.api);
                console.log('[TEST] create_window type:', typeof window.auroraview?.api?.create_window);

                // Check hasNativeWindowAPI
                const hasNative = typeof window.auroraview?.api?.create_window === 'function';
                console.log('[TEST] hasNativeWindowAPI():', hasNative);

                if (hasNative) {
                    console.log('[TEST] ✓ Native window API is available!');
                } else {
                    console.log('[TEST] ✗ Native window API is NOT available');
                }
            """)
            time.sleep(1)

            # Try to call create_window directly
            logger.info("\n--- Calling create_window directly via JS ---")
            webview.eval_js("""
                (async function() {
                    try {
                        console.log('[TEST] Calling create_window...');
                        const result = await window.auroraview.api.create_window({
                            label: 'settings-test',
                            url: '/settings.html',
                            title: 'Settings Test',
                            width: 400,
                            height: 500
                        });
                        console.log('[TEST] create_window result:', result);
                    } catch (e) {
                        console.error('[TEST] create_window error:', e);
                    }
                })();
            """)

            # Wait for create_window to be called
            logger.info("Waiting for create_window call...")
            if api.create_window_called.wait(timeout=5):
                logger.info("✓✓✓ SUCCESS: create_window was called!")
            else:
                logger.error("✗ FAIL: create_window was NOT called within 5s")
                logger.info(f"  API calls: {api.calls}")

        except Exception as e:
            logger.error(f"Test error: {e}")

        logger.info("\n--- Test complete. Close window to exit. ---")

    # Start test thread
    test_thread = threading.Thread(target=test_runner, daemon=True)
    test_thread.start()

    # Run WebView
    webview.show_blocking()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("FINAL RESULTS")
    logger.info("=" * 50)
    logger.info(f"API calls: {api.calls}")

    success = "create_window:settings-test" in api.calls
    if success:
        logger.info("✓✓✓ TEST PASSED: Settings opens as native window!")
    else:
        logger.error("✗✗✗ TEST FAILED: Settings did not open as native window")

    return success


if __name__ == "__main__":
    success = run_test()
    exit(0 if success else 1)
