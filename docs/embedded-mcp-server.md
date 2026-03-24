# Embedded MCP Server Guide

## Overview

AuroraView provides an embedded MCP (Model Context Protocol) Server that allows AI assistants like Claude, Cursor, and Copilot to interact with your WebView applications in real-time.

## Quick Start

### Enable MCP Server

```python
from auroraview import WebView

# Enable with defaults (auto-assign port)
webview = WebView(
    title="My Tool",
    url="http://localhost:3000",
    mcp=True
)

# Enable with custom port
webview = WebView(
    title="My Tool",
    url="http://localhost:3000",
    mcp_port=8765
)

# Enable with full configuration
from auroraview.mcp import McpConfig

config = McpConfig()
config.port = 8765
config.name = "my-tool"
config.auto_expose_api = True

webview = WebView(
    title="My Tool",
    url="http://localhost:3000",
    mcp=config
)
```

### Auto-Expose APIs

All methods registered via `bind_call()` are automatically exposed as MCP tools:

```python
def echo(message: str) -> dict:
    """Echo back the message"""
    return {"echo": message}

def get_data() -> dict:
    """Get current data"""
    return {"items": [...]}

webview.bind_call("api.echo", echo)
webview.bind_call("api.get_data", get_data)

# These will be available as MCP tools:
# - api.echo
# - api.get_data
```

### Connect AI Assistant

After starting your application, the MCP endpoint will be logged:

```
INFO: Embedded MCP Server started on port 8765
INFO: Connect AI assistant to: http://127.0.0.1:8765/sse
```

#### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-tool": {
      "url": "http://127.0.0.1:8765/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

#### Cursor Configuration

Add to Cursor settings:

```json
{
  "mcp.servers": {
    "my-tool": {
      "url": "http://127.0.0.1:8765/sse"
    }
  }
}
```

## Configuration Options

### McpConfig

```python
from auroraview.mcp import McpConfig

config = McpConfig()
config.port = 8765              # Port (0 = auto-assign)
config.host = "127.0.0.1"       # Host (localhost only by default)
config.name = "my-tool"         # Server name
config.version = "1.0.0"        # Server version
config.auto_expose_api = True   # Auto-expose bind_call methods
config.max_connections = 10     # Max concurrent connections
config.heartbeat_interval = 30  # SSE heartbeat interval (seconds)
```

## Built-in Tools

The embedded MCP Server provides built-in tools for common operations:

### Screenshot

```python
# AI can call this tool
result = await mcp.call_tool("take_screenshot", {
    "path": "/path/to/screenshot.png",
    "full_page": False
})
```

### Evaluate JavaScript

```python
result = await mcp.call_tool("evaluate", {
    "script": "document.title"
})
```

### Get Page Info

```python
info = await mcp.call_tool("get_page_info", {})
# Returns: {"title": "...", "url": "...", "ready": true}
```

### Emit Event

```python
await mcp.call_tool("emit_event", {
    "event": "custom_event",
    "data": {"key": "value"}
})
```

## Examples

See `examples/mcp_embedded_demo.py` for a complete working example.

## Troubleshooting

### Port Already in Use

If the specified port is already in use, use auto-assignment:

```python
webview = WebView(mcp=True)  # Auto-assign port
print(f"MCP Server running on port: {webview.mcp_port}")
```

### MCP Server Not Starting

Ensure the Rust MCP feature is enabled during build:

```bash
# Build with MCP support
cargo build --features mcp-server
```

### AI Assistant Can't Connect

1. Check firewall settings
2. Verify the port is correct
3. Ensure the application is running
4. Check the MCP endpoint URL in logs

## API Reference

### WebView Parameters

- `mcp` (bool | dict | McpConfig): Enable MCP Server
- `mcp_port` (int): Shortcut for port configuration
- `mcp_name` (str): Shortcut for server name

### WebView Properties

- `webview.mcp_server`: Get MCP Server instance
- `webview.mcp_port`: Get MCP Server port

### McpServer Methods

- `server.start()`: Start the server (returns port)
- `server.stop()`: Stop the server
- `server.register_tool(name, handler, description)`: Register a tool
- `server.list_tools()`: List all registered tools
