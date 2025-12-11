"""Test script to debug settings window creation."""

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    from pathlib import Path

    from auroraview import WebView
    from auroraview.utils import get_auroraview_entry_url

    DIST_DIR = Path(__file__).parent / "dist"

    # Create main WebView
    webview = WebView(
        title="Test - DCC Shelves",
        width=400,
        height=600,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    # Store child windows
    child_windows = {}

    # Bind create_window API
    @webview.bind_api("api")
    def create_window(
        label: str = "",
        url: str = "",
        title: str = "Window",
        width: int = 800,
        height: int = 600,
    ) -> dict:
        """Create a new child window."""
        logger.info(f"create_window called: label={label}, url={url}, title={title}")

        if not label:
            return {"success": False, "message": "No label provided"}
        if not url:
            return {"success": False, "message": "No URL provided"}

        if label in child_windows:
            logger.info(f"Window '{label}' already exists")
            return {"success": True, "message": "Window already exists", "label": label}

        try:
            # Resolve URL for production
            if url.startswith("http://") or url.startswith("https://"):
                load_url = url
            else:
                entry_file = url.lstrip("/")
                load_url = get_auroraview_entry_url(entry_file)

            logger.info(f"Creating child window with URL: {load_url}")

            # Create child WebView
            child = WebView(
                title=title,
                width=width,
                height=height,
                debug=True,
                context_menu=True,
                asset_root=str(DIST_DIR),
            )
            child.load_url(load_url)
            child_windows[label] = child
            child.show(wait=False)

            logger.info(f"Child window '{label}' created successfully")
            return {"success": True, "message": "Window created", "label": label}

        except Exception as e:
            logger.error(f"Failed to create window: {e}")
            return {"success": False, "message": str(e), "label": label}

    @webview.bind_api("api")
    def close_window(label: str = "") -> dict:
        """Close a child window."""
        if label in child_windows:
            try:
                child_windows[label].close()
                del child_windows[label]
                return {"success": True, "message": "Window closed"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        return {"success": False, "message": "Window not found"}

    # Load test HTML that will check API availability
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Test</title>
        <style>
            body { font-family: sans-serif; padding: 20px; background: #1a1a2e; color: #eee; }
            button { padding: 10px 20px; margin: 10px; cursor: pointer; }
            pre { background: #0f0f23; padding: 10px; overflow: auto; }
            .success { color: #4ade80; }
            .error { color: #f87171; }
        </style>
    </head>
    <body>
        <h1>AuroraView API Test</h1>
        <div id="status"></div>
        <button onclick="checkAPI()">Check API</button>
        <button onclick="testCreateWindow()">Test Create Window</button>
        <pre id="log"></pre>

        <script>
            function log(msg, isError) {
                const pre = document.getElementById('log');
                const span = document.createElement('span');
                span.className = isError ? 'error' : '';
                span.textContent = msg + '\\n';
                pre.appendChild(span);
                console.log(msg);
            }

            function checkAPI() {
                log('=== API Check ===');
                log('window.auroraview: ' + (window.auroraview ? 'exists' : 'undefined'));

                if (window.auroraview) {
                    log('window.auroraview.api: ' + (window.auroraview.api ? 'exists' : 'undefined'));

                    if (window.auroraview.api) {
                        const methods = Object.keys(window.auroraview.api);
                        log('API methods: ' + methods.join(', '));

                        log('create_window type: ' + typeof window.auroraview.api.create_window);
                        log('close_window type: ' + typeof window.auroraview.api.close_window);
                    }
                }

                log('hasNativeWindowAPI: ' + Boolean(window.auroraview?.api?.create_window));
            }

            async function testCreateWindow() {
                log('=== Test Create Window ===');

                if (!window.auroraview?.api?.create_window) {
                    log('ERROR: create_window not available!', true);
                    return;
                }

                try {
                    log('Calling create_window...');
                    const result = await window.auroraview.api.create_window({
                        label: 'test_settings',
                        url: 'https://auroraview.localhost/settings.html',
                        title: 'Test Settings Window',
                        width: 520,
                        height: 650
                    });
                    log('Result: ' + JSON.stringify(result));

                    if (result.success) {
                        log('SUCCESS: Window created!', false);
                    } else {
                        log('FAILED: ' + result.message, true);
                    }
                } catch (e) {
                    log('ERROR: ' + e.message, true);
                }
            }

            // Auto-check on load
            window.addEventListener('load', () => {
                setTimeout(checkAPI, 500);
            });
        </script>
    </body>
    </html>
    """

    webview.load_html(test_html)

    logger.info("Starting test window...")
    webview.show_blocking()

    # Cleanup
    for label, child in child_windows.items():
        try:
            child.close()
        except:
            pass


if __name__ == "__main__":
    main()
