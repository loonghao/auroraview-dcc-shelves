"""Diagnostic script to check API registration status in Houdini.

Run this in Houdini's Python Shell after DCC Shelves is open:
    exec(open(r"C:\\github\auroraview-dcc-shelves\tests\\diagnose_houdini_api.py").read())
"""

import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def diagnose():
    """Diagnose API registration issues."""
    from auroraview_dcc_shelves.app import ShelfApp

    print("=" * 60)
    print("DCC Shelves API Registration Diagnosis")
    print("=" * 60)

    # Get the current ShelfApp instance
    app = getattr(ShelfApp, "_current_instance", None)
    if app is None:
        # Try to find it via global
        import sys

        for name, obj in list(sys.modules.items()):
            if hasattr(obj, "_current_shelf_app"):
                app = obj._current_shelf_app
                break

    if app is None:
        print("[ERROR] No ShelfApp instance found!")
        print("Make sure DCC Shelves is running.")
        return

    print(f"\n[INFO] ShelfApp instance found: {app}")
    print(f"  - _api_registered: {app._api_registered}")
    print(f"  - _api: {app._api}")
    print(f"  - _webview: {app._webview}")
    print(f"  - _is_loading: {app._is_loading}")
    print(f"  - _load_progress: {app._load_progress}")
    print(f"  - _current_url: {app._current_url}")

    # Check WebView signals
    webview = app._webview
    if webview:
        print(f"\n[INFO] WebView type: {type(webview)}")
        print(f"  - hasattr loadFinished: {hasattr(webview, 'loadFinished')}")
        print(f"  - hasattr loadStarted: {hasattr(webview, 'loadStarted')}")

    # Check API object
    api = app._api
    if api:
        print("\n[INFO] ShelfAPI methods:")
        for name in dir(api):
            if not name.startswith("_"):
                print(f"  - {name}")

    # Try to manually register API
    print("\n" + "=" * 60)
    print("Attempting manual API registration...")
    print("=" * 60)

    # Reset registration flag
    app._api_registered = False
    print("[INFO] Reset _api_registered to False")

    # Call registration
    app._register_api_after_load()
    print("[INFO] Called _register_api_after_load()")

    print("\n[INFO] After manual registration:")
    print(f"  - _api_registered: {app._api_registered}")

    # Try to call get_config via WebView
    if webview and hasattr(webview, "eval_js"):
        print("\n" + "=" * 60)
        print("Checking window.auroraview.api in WebView...")
        print("=" * 60)

        js_check = """
        (function() {
            const result = {
                hasAuroraview: typeof window.auroraview !== 'undefined',
                hasApi: typeof window.auroraview?.api !== 'undefined',
                apiKeys: window.auroraview?.api ? Object.keys(window.auroraview.api) : [],
                hasGetConfig: typeof window.auroraview?.api?.get_config === 'function'
            };
            console.log('[Diagnose] API check:', JSON.stringify(result, null, 2));
            return result;
        })();
        """

        try:
            result = webview.eval_js(js_check)
            print(f"[INFO] JavaScript API check result: {result}")
        except Exception as e:
            print(f"[ERROR] Failed to eval JS: {e}")

    print("\n" + "=" * 60)
    print("Diagnosis complete!")
    print("=" * 60)


if __name__ == "__main__":
    diagnose()
else:
    diagnose()
