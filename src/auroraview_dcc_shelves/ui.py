"""AuroraView-based UI for DCC tool shelves.

This module provides the ShelfApp class for displaying and interacting
with the tool shelf interface.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from auroraview import AuroraView

if TYPE_CHECKING:
    from auroraview_dcc_shelves.config import ShelvesConfig

from auroraview_dcc_shelves.launcher import LaunchError, ToolLauncher

logger = logging.getLogger(__name__)

# Path to the frontend dist directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DIST_DIR = Path(__file__).parent.parent.parent / "dist"


def _config_to_dict(config: ShelvesConfig) -> dict[str, Any]:
    """Convert ShelvesConfig to a dictionary for JSON serialization."""
    return {
        "shelves": [
            {
                "id": shelf.id,
                "name": shelf.name,
                "buttons": [
                    {
                        "id": button.id,
                        "name": button.name,
                        "toolType": button.tool_type.value,
                        "toolPath": button.tool_path,
                        "icon": button.icon,
                        "args": button.args,
                        "description": button.description,
                    }
                    for button in shelf.buttons
                ],
            }
            for shelf in config.shelves
        ]
    }


class ShelfApp:
    """AuroraView-based application for displaying tool shelves.

    This class creates a WebView window displaying the shelf UI and
    handles communication between the frontend and Python backend.

    Args:
        config: The shelves configuration to display.
        title: Window title. Defaults to "DCC Shelves".
        width: Window width in pixels. Defaults to 800.
        height: Window height in pixels. Defaults to 600.
    """

    def __init__(
        self,
        config: ShelvesConfig,
        title: str = "DCC Shelves",
        width: int = 800,
        height: int = 600,
    ) -> None:
        self._config = config
        self._title = title
        self._width = width
        self._height = height
        self._launcher = ToolLauncher(config)
        self._webview: AuroraView | None = None

    def _get_html_path(self) -> str:
        """Get the path to the frontend HTML file."""
        # Try dist directory first (production)
        dist_index = DIST_DIR / "index.html"
        if dist_index.exists():
            return str(dist_index)

        # Fall back to development server URL
        return "http://localhost:5173"

    def _register_api(self, webview: AuroraView) -> None:
        """Register Python API methods for the frontend."""

        @webview.expose
        def get_config() -> dict[str, Any]:
            """Return the current configuration as JSON."""
            return _config_to_dict(self._config)

        @webview.expose
        def launch_tool(button_id: str) -> dict[str, Any]:
            """Launch a tool by its button ID."""
            try:
                self._launcher.launch_by_id(button_id)
                return {
                    "success": True,
                    "message": f"Tool launched: {button_id}",
                    "buttonId": button_id,
                }
            except LaunchError as e:
                logger.error(f"Failed to launch tool {button_id}: {e}")
                return {
                    "success": False,
                    "message": str(e),
                    "buttonId": button_id,
                }

        @webview.expose
        def get_tool_path(button_id: str) -> str:
            """Get the resolved path for a tool."""
            for shelf in self._config.shelves:
                for button in shelf.buttons:
                    if button.id == button_id:
                        return str(self._launcher.resolve_path(button.tool_path))
            return ""

    def show(self, debug: bool = False) -> None:
        """Show the shelf window.

        Args:
            debug: Enable debug mode with developer tools.
        """
        html_path = self._get_html_path()
        logger.info(f"Loading UI from: {html_path}")

        self._webview = AuroraView(
            title=self._title,
            width=self._width,
            height=self._height,
            debug=debug,
        )

        self._register_api(self._webview)
        self._webview.load(html_path)
        self._webview.run()

    def update_config(self, config: ShelvesConfig) -> None:
        """Update the configuration and notify the frontend.

        Args:
            config: The new configuration.
        """
        self._config = config
        self._launcher = ToolLauncher(config)

        if self._webview:
            config_dict = _config_to_dict(config)
            self._webview.emit("config_updated", config_dict)

    @property
    def config(self) -> ShelvesConfig:
        """Get the current configuration."""
        return self._config
