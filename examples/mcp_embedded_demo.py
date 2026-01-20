"""Embedded MCP Server Demo

This example demonstrates how to use the embedded MCP Server feature
to expose WebView APIs to AI assistants like Claude, Cursor, and Copilot.

Usage:
    python examples/mcp_embedded_demo.py

Then connect your AI assistant to the MCP endpoint shown in the console.
"""

from auroraview import WebView
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoTool:
    """Demo tool with embedded MCP Server"""

    def __init__(self):
        # Create WebView with embedded MCP Server enabled
        self.webview = WebView(
            title="MCP Demo Tool",
            width=800,
            height=600,
            url="data:text/html,<h1>MCP Demo Tool</h1><p>Check console for MCP endpoint</p>",
            mcp=True,  # Enable embedded MCP Server
            mcp_port=8765,  # Optional: specify port (default: auto-assign)
            mcp_name="demo-tool",  # Optional: server name
        )

        # Register API methods - these will be automatically exposed as MCP tools
        self.webview.bind_call("api.echo", self.echo)
        self.webview.bind_call("api.get_data", self.get_data)
        self.webview.bind_call("api.process", self.process)
        self.webview.bind_call("api.get_status", self.get_status)

        self.data = {"items": [], "count": 0}

    def echo(self, message: str) -> dict:
        """Echo back the message

        Args:
            message: Message to echo

        Returns:
            dict: Echoed message
        """
        logger.info(f"Echo called with: {message}")
        return {"echo": message, "timestamp": "2025-12-31"}

    def get_data(self) -> dict:
        """Get current data

        Returns:
            dict: Current data state
        """
        logger.info("Get data called")
        return self.data

    def process(self, item: dict) -> dict:
        """Process an item and add to data

        Args:
            item: Item to process (must have 'name' field)

        Returns:
            dict: Processing result
        """
        logger.info(f"Process called with: {item}")
        if not isinstance(item, dict) or "name" not in item:
            return {"status": "error", "message": "Item must have 'name' field"}

        self.data["items"].append(item)
        self.data["count"] += 1

        return {
            "status": "success",
            "item": item,
            "total_count": self.data["count"],
        }

    def get_status(self) -> dict:
        """Get tool status

        Returns:
            dict: Tool status information
        """
        return {
            "status": "running",
            "mcp_enabled": True,
            "mcp_port": self.webview.mcp_port,
            "item_count": self.data["count"],
        }

    def run(self):
        """Run the tool"""
        logger.info("Starting MCP Demo Tool...")
        logger.info(f"MCP Server will start on port: {self.webview.mcp_port or 'auto'}")
        self.webview.show()


def main():
    """Main entry point"""
    tool = DemoTool()
    tool.run()


if __name__ == "__main__":
    main()
