"""Test API registration timing and frontend detection."""

import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from pathlib import Path

from auroraview import WebView

DIST_DIR = Path(__file__).parent / "dist"


def main():
    webview = WebView(
        title="API Timing Test",
        width=700,
        height=500,
        debug=True,
        context_menu=True,
        asset_root=str(DIST_DIR),
    )

    class TestAPI:
        """Test API class."""

        def get_config(self):
            logger.info(">>> get_config called from JavaScript!")
            return {"shelves": [], "currentHost": "desktop", "banner": {"title": "Test"}}

        def create_window(self, label="", url="", title="Window", width=500, height=600):
            logger.info(f">>> create_window called from JavaScript! label={label}")
            return {"success": True, "label": label, "message": "Window created"}

        def close_window(self, label=""):
            logger.info(f">>> close_window called from JavaScript! label={label}")
            return {"success": True}

    # Bind API BEFORE loading content
    api = TestAPI()
    webview.bind_api(api)
    logger.info("API bound successfully")
    logger.info(f"Bound methods: {webview.get_bound_methods()}")

    # Handle __auroraview_ready event to re-register API after page navigation
    @webview.on("__auroraview_ready")
    def handle_ready(data):
        url = data.get("url", "")
        logger.info(f">>> __auroraview_ready event received! url={url}")
        # Re-register API methods when page navigates
        logger.info(">>> Re-registering API methods...")
        webview.bind_api(api, allow_rebind=True)
        logger.info(">>> API re-registered successfully")

    # Create test HTML
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Timing Test</title>
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                padding: 20px;
                background: #1a1a2e;
                color: #eee;
            }
            .status { margin: 10px 0; padding: 10px; border-radius: 4px; font-family: monospace; }
            .success { background: #2d5a27; }
            .error { background: #5a2727; }
            .info { background: #27425a; }
            .warning { background: #5a4a27; }
            pre { background: #0d0d1a; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 300px; }
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
            h2 { margin-top: 20px; border-bottom: 1px solid #333; padding-bottom: 5px; }
        </style>
    </head>
    <body>
        <h1>AuroraView API Timing Test</h1>

        <div id="results"></div>

        <h2>Test Actions</h2>
        <button onclick="testGetConfig()">Call get_config()</button>
        <button onclick="testCreateWindow()">Call create_window()</button>
        <button onclick="refreshCheck()">Re-check API</button>
        <button onclick="waitAndCheck()">Wait 1s & Check</button>

        <h2>Console Log</h2>
        <pre id="console"></pre>

        <script>
            const results = document.getElementById('results');
            const consoleEl = document.getElementById('console');
            let logCount = 0;

            function log(msg, type = 'info') {
                logCount++;
                const timestamp = new Date().toISOString().substr(11, 12);
                const line = `[${logCount.toString().padStart(3, '0')}] ${timestamp} ${msg}`;
                consoleEl.textContent += line + '\\n';
                consoleEl.scrollTop = consoleEl.scrollHeight;
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
                    log('FAIL: window.auroraview is undefined');
                    return false;
                }
                log('OK: window.auroraview exists');
                addResult('✓ window.auroraview exists', 'success');

                // Check _ready flag
                log('window.auroraview._ready = ' + window.auroraview._ready);
                if (window.auroraview._ready) {
                    addResult('✓ Bridge is ready (_ready=true)', 'success');
                } else {
                    addResult('⚠ Bridge not ready yet (_ready=false)', 'warning');
                }

                // Check window.auroraview.api
                if (typeof window.auroraview.api === 'undefined') {
                    addResult('❌ window.auroraview.api is undefined', 'error');
                    log('FAIL: window.auroraview.api is undefined');
                    return false;
                }
                log('OK: window.auroraview.api exists');
                addResult('✓ window.auroraview.api exists', 'success');

                // List all properties on api
                const apiProps = Object.keys(window.auroraview.api);
                log('API properties: ' + JSON.stringify(apiProps));

                if (apiProps.length === 0) {
                    addResult('⚠ window.auroraview.api is empty!', 'warning');
                } else {
                    addResult('API methods: ' + apiProps.join(', '), 'info');
                }

                // Check specific methods
                const methods = ['get_config', 'create_window', 'close_window'];
                let allFound = true;
                methods.forEach(method => {
                    const methodType = typeof window.auroraview.api[method];
                    const exists = methodType === 'function';
                    if (exists) {
                        addResult('✓ api.' + method + ' is a function', 'success');
                        log('OK: api.' + method + ' is a function');
                    } else {
                        addResult('❌ api.' + method + ' is NOT a function (type: ' + methodType + ')', 'error');
                        log('FAIL: api.' + method + ' type=' + methodType);
                        allFound = false;
                    }
                });

                // Check _boundMethods
                if (window.auroraview._boundMethods) {
                    const boundKeys = Object.keys(window.auroraview._boundMethods);
                    log('_boundMethods: ' + JSON.stringify(boundKeys));
                    addResult('Bound methods registry: ' + boundKeys.join(', '), 'info');
                } else {
                    log('_boundMethods is not defined');
                }

                // Check hasNativeWindowAPI equivalent
                const hasNative = typeof window.auroraview?.api?.create_window === 'function';
                log('hasNativeWindowAPI() = ' + hasNative);
                addResult('hasNativeWindowAPI(): ' + hasNative, hasNative ? 'success' : 'error');

                return allFound;
            }

            async function testGetConfig() {
                log('\\n=== Testing get_config() ===');
                try {
                    if (typeof window.auroraview?.api?.get_config !== 'function') {
                        log('ERROR: get_config is not a function');
                        addResult('get_config() not available', 'error');
                        return;
                    }
                    log('Calling window.auroraview.api.get_config()...');
                    const result = await window.auroraview.api.get_config();
                    log('Result: ' + JSON.stringify(result));
                    addResult('✓ get_config() returned: ' + JSON.stringify(result).substring(0, 100), 'success');
                } catch (e) {
                    log('Error: ' + e.message);
                    addResult('get_config() error: ' + e.message, 'error');
                }
            }

            async function testCreateWindow() {
                log('\\n=== Testing create_window() ===');
                try {
                    if (typeof window.auroraview?.api?.create_window !== 'function') {
                        log('ERROR: create_window is not a function');
                        addResult('create_window() not available', 'error');
                        return;
                    }
                    log('Calling window.auroraview.api.create_window()...');
                    const result = await window.auroraview.api.create_window({
                        label: 'settings',
                        url: '/settings.html',
                        title: 'Settings Window',
                        width: 500,
                        height: 600
                    });
                    log('Result: ' + JSON.stringify(result));
                    addResult('✓ create_window() returned: ' + JSON.stringify(result), 'success');
                } catch (e) {
                    log('Error: ' + e.message);
                    addResult('create_window() error: ' + e.message, 'error');
                }
            }

            function refreshCheck() {
                results.innerHTML = '';
                consoleEl.textContent = '';
                logCount = 0;
                checkAPI();
            }

            function waitAndCheck() {
                log('Waiting 1 second...');
                setTimeout(() => {
                    results.innerHTML = '';
                    checkAPI();
                }, 1000);
            }

            // Immediate check
            log('=== IMMEDIATE CHECK (script execution) ===');
            checkAPI();

            // Check on DOMContentLoaded
            document.addEventListener('DOMContentLoaded', () => {
                log('\\n=== DOMContentLoaded event ===');
                checkAPI();
            });

            // Check on load
            window.addEventListener('load', () => {
                log('\\n=== window.load event ===');
                checkAPI();
            });

            // Listen for auroraview-api-ready event
            window.addEventListener('auroraview-api-ready', () => {
                log('\\n=== auroraview-api-ready event received! ===');
                checkAPI();
            });

            // Check after a delay
            setTimeout(() => {
                log('\\n=== Delayed check (500ms) ===');
                checkAPI();
            }, 500);
        </script>
    </body>
    </html>
    """

    webview.load_html(test_html)

    logger.info("Starting webview...")
    webview.show_blocking()


if __name__ == "__main__":
    main()
