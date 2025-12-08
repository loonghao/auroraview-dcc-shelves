"""Test API binding."""

import logging

logging.basicConfig(level=logging.DEBUG)

from auroraview import WebView

w = WebView(title="Test", width=400, height=300, debug=True)


class API:
    def create_window(self, label="", url="", title="Win", width=500, height=600):
        print(f"create_window called: {label}, {url}")
        return {"success": True, "label": label}

    def close_window(self, label=""):
        print(f"close_window called: {label}")
        return {"success": True}

    def get_config(self):
        return {"shelves": []}


api = API()
w.bind_api(api)

# Test HTML
html = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body style="background:#1a1a2e;color:#fff;padding:20px;font-family:sans-serif;">
<h2>API Test</h2>
<pre id="log"></pre>
<button onclick="checkAPI()">Check API</button>
<button onclick="testCreate()">Test Create Window</button>
<script>
function log(msg) {
    document.getElementById('log').textContent += msg + '\\n';
    console.log(msg);
}

function checkAPI() {
    log('=== Check API ===');
    log('auroraview: ' + !!window.auroraview);
    log('auroraview.api: ' + !!window.auroraview?.api);
    if (window.auroraview?.api) {
        log('Methods: ' + Object.keys(window.auroraview.api).join(', '));
        log('create_window: ' + typeof window.auroraview.api.create_window);
    }
}

async function testCreate() {
    log('=== Test Create ===');
    if (!window.auroraview?.api?.create_window) {
        log('ERROR: create_window not found!');
        return;
    }
    try {
        const result = await window.auroraview.api.create_window({
            label: 'test',
            url: 'https://example.com',
            title: 'Test Window'
        });
        log('Result: ' + JSON.stringify(result));
    } catch (e) {
        log('Error: ' + e);
    }
}

setTimeout(checkAPI, 500);
</script>
</body>
</html>
"""

w.load_html(html)
print("Starting test...")
w.show_blocking()
