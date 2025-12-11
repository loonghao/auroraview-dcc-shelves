"""Test API detection in frontend JavaScript."""

import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from pathlib import Path

from auroraview import WebView

DIST_DIR = Path(__file__).parent / "dist"


def main():
    webview = WebView(
        title="API Detection Test",
        width=600,
        height=400,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    class TestAPI:
        """Test API class."""

        def get_config(self):
            logger.info("get_config called")
            return {"test": "config"}

        def create_window(self, label="", url="", title="Window", width=500, height=600):
            logger.info(f"create_window called: label={label}")
            return {"success": True, "label": label}

        def close_window(self, label=""):
            logger.info(f"close_window called: {label}")
            return {"success": True}

    # Bind API
    api = TestAPI()
    webview.bind_api(api)
    logger.info("API bound successfully")
    logger.info(f"Bound methods: {webview.get_bound_methods()}")

    # Create test HTML that checks for API availability
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Detection Test</title>
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                padding: 20px;
                background: #1a1a2e;
                color: #eee;
            }
            .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
            .success { background: #2d5a27; }
            .error { background: #5a2727; }
            .info { background: #27425a; }
            pre { background: #0d0d1a; padding: 10px; border-radius: 4px; overflow-x: auto; }
            button {
                padding: 8px 16px;
                margin: 5px;
                background: #4a4a8a;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover { background: #5a5a9a; }
        </style>
    </head>
    <body>
        <h1>AuroraView API Detection Test</h1>

        <div id="results"></div>

        <h2>Actions</h2>
        <button onclick="testGetConfig()">Test get_config()</button>
        <button onclick="testCreateWindow()">Test create_window()</button>
        <button onclick="refreshCheck()">Refresh Check</button>

        <h2>Console Output</h2>
        <pre id="console"></pre>

        <script>
            const results = document.getElementById('results');
            const consoleEl = document.getElementById('console');

            function log(msg) {
                consoleEl.textContent += msg + '\\n';
                console.log(msg);
            }

            function addResult(text, type) {
                const div = document.createElement('div');
                div.className = 'status ' + type;
                div.textContent = text;
                results.appendChild(div);
            }

            function checkAPI() {
                log('=== Checking API availability ===');

                // Check window.auroraview
                if (typeof window.auroraview === 'undefined') {
                    addResult('❌ window.auroraview is undefined', 'error');
                    log('window.auroraview: undefined');
                    return;
                }
                addResult('✓ window.auroraview exists', 'success');
                log('window.auroraview: ' + typeof window.auroraview);

                // Check window.auroraview.api
                if (typeof window.auroraview.api === 'undefined') {
                    addResult('❌ window.auroraview.api is undefined', 'error');
                    log('window.auroraview.api: undefined');
                    return;
                }
                addResult('✓ window.auroraview.api exists', 'success');
                log('window.auroraview.api: ' + typeof window.auroraview.api);

                // List all properties on api
                const apiProps = Object.keys(window.auroraview.api);
                log('API properties: ' + JSON.stringify(apiProps));
                addResult('API methods: ' + apiProps.join(', '), 'info');

                // Check specific methods
                const methods = ['get_config', 'create_window', 'close_window'];
                methods.forEach(method => {
                    const exists = typeof window.auroraview.api[method] === 'function';
                    if (exists) {
                        addResult('✓ api.' + method + ' is a function', 'success');
                    } else {
                        addResult('❌ api.' + method + ' is NOT a function (type: ' +
                            typeof window.auroraview.api[method] + ')', 'error');
                    }
                    log('api.' + method + ': ' + typeof window.auroraview.api[method]);
                });

                // Check hasNativeWindowAPI equivalent
                const hasNative = typeof window.auroraview?.api?.create_window === 'function';
                log('hasNativeWindowAPI(): ' + hasNative);
                addResult('hasNativeWindowAPI(): ' + hasNative, hasNative ? 'success' : 'error');
            }

            async function testGetConfig() {
                log('\\n=== Testing get_config() ===');
                try {
                    const result = await window.auroraview.api.get_config();
                    log('Result: ' + JSON.stringify(result));
                    addResult('get_config() returned: ' + JSON.stringify(result), 'success');
                } catch (e) {
                    log('Error: ' + e.message);
                    addResult('get_config() error: ' + e.message, 'error');
                }
            }

            async function testCreateWindow() {
                log('\\n=== Testing create_window() ===');
                try {
                    const result = await window.auroraview.api.create_window({
                        label: 'test',
                        url: '/settings.html',
                        title: 'Test Window',
                        width: 400,
                        height: 300
                    });
                    log('Result: ' + JSON.stringify(result));
                    addResult('create_window() returned: ' + JSON.stringify(result), 'success');
                } catch (e) {
                    log('Error: ' + e.message);
                    addResult('create_window() error: ' + e.message, 'error');
                }
            }

            function refreshCheck() {
                results.innerHTML = '';
                consoleEl.textContent = '';
                checkAPI();
            }

            // Run check on load
            window.addEventListener('load', () => {
                log('Page loaded, waiting 500ms for API initialization...');
                setTimeout(checkAPI, 500);
            });

            // Also check immediately
            log('Immediate check:');
            checkAPI();
        </script>
    </body>
    </html>
    """

    webview.load_html(test_html)

    logger.info("Starting webview...")
    webview.show_blocking()


if __name__ == "__main__":
    main()
