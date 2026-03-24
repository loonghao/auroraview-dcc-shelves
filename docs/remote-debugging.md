# Remote Debugging with Chrome DevTools Protocol (CDP)

## Overview

AuroraView DCC Shelves supports the Chrome DevTools Protocol (CDP) through the `remote_debugging_port` parameter. This enables powerful automation and debugging capabilities, allowing tools like MCP, Playwright, and Puppeteer to control the WebView.

## Quick Start

### Enable Remote Debugging in DCC Mode

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config, remote_debugging_port=9222)
app.show(app="maya", mode="qt")

# Connect via:
# - chrome://inspect
# - MCP (http://127.0.0.1:9222 or ws://127.0.0.1:9222)
# - Playwright
# - Puppeteer
```

### Enable Remote Debugging in Desktop Mode

```python
from auroraview_dcc_shelves.apps.desktop import run_desktop

run_desktop(
    config_path="shelf_config.yaml",
    debug=True,
    remote_debugging_port=9222
)
```

## Connecting to the WebView

Once the WebView is running with `remote_debugging_port` enabled, you can connect using various tools:

### Chrome DevTools

1. Open Chrome/Edge browser
2. Navigate to `chrome://inspect`
3. Click "Configure..." and add `localhost:9222`
4. The WebView will appear under "Remote Target"
5. Click "inspect" to open DevTools

### MCP (Model Context Protocol)

Connect your AI assistant to control the WebView:

```json
{
  "mcpServers": {
    "dcc-shelves": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-puppeteer"],
      "env": {
        "CDP_URL": "http://127.0.0.1:9222"
      }
    }
  }
}
```

### Playwright

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    page = context.pages[0]

    # Automate the WebView
    page.click('[data-testid="tool-button"]')
```

### Puppeteer

```javascript
const puppeteer = require('puppeteer-core');

(async () => {
    const browser = await puppeteer.connect({
        browserURL: 'http://127.0.0.1:9222'
    });

    const pages = await browser.pages();
    const page = pages[0];

    // Automate the WebView
    await page.click('[data-testid="tool-button"]');
})();
```

## Use Cases

### 1. UI Automation Testing

```python
# pytest test file
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def shelf_app():
    """Start ShelfApp with remote debugging."""
    from auroraview_dcc_shelves import ShelfApp, load_config

    config = load_config("shelf_config.yaml")
    app = ShelfApp(config, remote_debugging_port=9222)
    app.show(app="maya", mode="qt")
    yield app
    app.close()

def test_tool_launch(shelf_app):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = browser.contexts[0].pages[0]

        # Click a tool button
        page.click('text="Poly Reduce"')

        # Verify tool launched
        assert page.locator('.toast-success').is_visible()
```

### 2. AI-Assisted Workflows

Enable AI tools to interact with your DCC shelf:

```python
# In your DCC startup script
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(
    config,
    remote_debugging_port=9222  # Enable MCP control
)
app.show(app="maya", mode="qt")

print("CDP ready at http://127.0.0.1:9222")
print("AI assistants can now control the shelf!")
```

### 3. Remote Debugging Production Issues

```python
# Enable debugging temporarily for troubleshooting
from auroraview_dcc_shelves import ShelfApp, load_config
import os

# Enable only when SHELF_DEBUG is set
debug_port = int(os.environ.get("SHELF_DEBUG_PORT", 0)) or None

config = load_config("shelf_config.yaml")
app = ShelfApp(config, remote_debugging_port=debug_port)
app.show(app="maya", mode="qt")
```

## API Reference

### ShelfApp Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `remote_debugging_port` | `int \| None` | `None` | Port for CDP. When set, enables remote debugging. |

### ShelfApp Properties

| Property | Type | Description |
|----------|------|-------------|
| `remote_debugging_port` | `int \| None` | Get the configured CDP port. |

## Common Ports

| Port | Usage |
|------|-------|
| 9222 | Chrome DevTools default |
| 9223 | Alternative for multiple instances |
| 9333 | Another common alternative |

## Security Considerations

⚠️ **Important**: Remote debugging exposes full control of the WebView. Consider these security practices:

1. **Use only on localhost** - The default binding is `127.0.0.1`
2. **Close the port in production** - Only enable when needed
3. **Use firewall rules** - Block external access to the debug port
4. **Don't expose sensitive data** - Be aware that all page content is accessible

## Troubleshooting

### Port Already in Use

```python
# Use a different port
app = ShelfApp(config, remote_debugging_port=9333)
```

### Connection Refused

1. Ensure the ShelfApp is running and WebView is initialized
2. Check if the port is correct
3. Verify no firewall is blocking the connection

### DevTools Shows Blank Page

1. Wait for the WebView to fully load
2. Refresh the DevTools connection
3. Check the console for JavaScript errors
