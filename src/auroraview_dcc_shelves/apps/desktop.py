"""Desktop (Standalone) Adapter.

This module provides an adapter for running the shelf as a standalone desktop
application without any DCC software. It uses tao/wry native window directly
without Qt dependency.

Features:
    - Native tao/wry window (no Qt required)
    - System tray integration (optional)
    - Taskbar icon
    - Standalone event loop
    - No DCC dependencies

Usage:
    # Via CLI
    python -m auroraview_dcc_shelves --config shelf_config.yaml

    # Via Python
    from auroraview_dcc_shelves.apps.desktop import run_desktop
    run_desktop("shelf_config.yaml", debug=True)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, register_adapter

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_adapter
class DesktopAdapter(DCCAdapter):
    """Adapter for standalone desktop mode.

    This adapter creates a native tao/wry window that runs independently
    of any DCC software. It does NOT use Qt - the WebView manages its own
    event loop via show_blocking().

    Attributes:
        name: "Desktop"
        aliases: ["standalone", "desktop", "native"]
        timer_interval_ms: 16 (60 FPS)
        recommended_mode: "standalone" (uses native WebView, not Qt)
    """

    name = "Desktop"
    aliases = ["standalone", "desktop", "native"]
    timer_interval_ms = 16  # 60 FPS for smooth animations
    recommended_mode = "standalone"  # Use native WebView, not Qt

    def __init__(self) -> None:
        """Initialize the desktop adapter."""
        super().__init__()

    def get_main_window(self) -> Any | None:
        """Get the main window for desktop mode.

        In desktop mode, there is no parent window - we create
        a top-level native window.

        Returns:
            None - desktop windows are top-level.
        """
        return None

    # ========================================
    # Lifecycle Hooks
    # ========================================

    def on_init(self, shelf_app: Any) -> None:
        """Initialize desktop mode.

        Desktop mode doesn't need Qt initialization.

        Args:
            shelf_app: The ShelfApp instance.
        """
        logger.info("Desktop: Adapter initialized (native mode, no Qt)")

    def on_show(self, shelf_app: Any) -> None:
        """Called after the shelf window is shown.

        Args:
            shelf_app: The ShelfApp instance.
        """
        logger.debug("Desktop: Window shown")

    def on_close(self, shelf_app: Any) -> None:
        """Called when the shelf window is closed.

        Args:
            shelf_app: The ShelfApp instance.
        """
        logger.debug("Desktop: Window closed")

    # ========================================
    # Dockable Hooks
    # ========================================

    def supports_dockable(self) -> bool:
        """Desktop mode doesn't support docking.

        Returns:
            False - no docking in desktop mode.
        """
        return False


def run_desktop(
    config_path: str | None = None,
    debug: bool = False,
    width: int = 0,
    height: int = 0,
    title: str = "DCC Shelves",
) -> int:
    """Run the shelf as a standalone desktop application.

    This is the main entry point for desktop mode. It uses tao/wry
    native window directly without Qt dependency.

    Args:
        config_path: Path to the YAML configuration file.
            If None, uses a default configuration.
        debug: Enable debug mode with developer tools.
        width: Window width (0 for default).
        height: Window height (0 for default).
        title: Window title.

    Returns:
        Exit code (0 for success).

    Example:
        >>> from auroraview_dcc_shelves.apps.desktop import run_desktop
        >>> run_desktop("shelf_config.yaml", debug=True)
    """
    from auroraview import WebView

    from auroraview_dcc_shelves.config import load_config
    from auroraview_dcc_shelves.constants import MAIN_WINDOW_CONFIG
    from auroraview_dcc_shelves.launcher import LaunchError, ToolLauncher
    from auroraview_dcc_shelves.ui.api import _config_to_dict
    from auroraview_dcc_shelves.user_tools import UserToolsManager

    # Determine paths
    DIST_DIR = Path(__file__).parent.parent.parent.parent / "dist"

    def is_dev_mode() -> bool:
        """Check if running in development mode."""
        return not (DIST_DIR / "index.html").exists()

    # Load configuration
    if config_path:
        config = load_config(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
    else:
        # Create minimal default configuration
        from auroraview_dcc_shelves.config import BannerConfig, ShelvesConfig

        config = ShelvesConfig(
            banner=BannerConfig(
                title=title,
                subtitle="Desktop Mode",
            ),
            shelves=[],
        )
        logger.info("Using default configuration")

    # Determine window size
    effective_width = width if width > 0 else MAIN_WINDOW_CONFIG["default_width"]
    effective_height = height if height > 0 else MAIN_WINDOW_CONFIG["default_height"]

    # Create launcher
    launcher = ToolLauncher(config, dcc_mode=False)

    # Create user tools manager
    user_tools_manager = UserToolsManager()

    # Create WebView with native window
    dist_dir = str(DIST_DIR) if not is_dev_mode() else None

    webview = WebView(
        title=title,
        width=effective_width,
        height=effective_height,
        debug=debug,
        context_menu=debug,
        asset_root=dist_dir,
    )

    # Store child windows
    child_windows: dict[str, WebView] = {}

    # Create a comprehensive API class for desktop mode
    class DesktopShelfAPI:
        """Full-featured API for desktop mode."""

        def __init__(self, config, launcher, user_tools_manager):
            self._config = config
            self._launcher = launcher
            self._user_tools_manager = user_tools_manager

        def get_config(self, **kwargs) -> dict:
            """Get shelf configuration."""
            return _config_to_dict(self._config, "desktop")

        def launch_tool(self, button_id: str = "") -> dict:
            """Launch a tool by button ID."""
            if not button_id:
                return {"success": False, "message": "No button_id provided", "buttonId": ""}
            try:
                result = self._launcher.launch_by_id(button_id)
                if isinstance(result, dict) and result.get("type") == "javascript":
                    return {
                        "success": True,
                        "message": f"JavaScript tool ready: {button_id}",
                        "buttonId": button_id,
                        "javascript": result.get("script", ""),
                    }
                return {"success": True, "message": f"Tool launched: {button_id}", "buttonId": button_id}
            except LaunchError as e:
                logger.error(f"Failed to launch tool {button_id}: {e}")
                return {"success": False, "message": str(e), "buttonId": button_id}

        def get_tool_path(self, button_id: str = "") -> dict:
            """Get the resolved path for a tool."""
            for shelf in self._config.shelves:
                for button in shelf.buttons:
                    if button.id == button_id:
                        path = str(self._launcher.resolve_path(button.tool_path))
                        return {"buttonId": button_id, "path": path}
            return {"buttonId": button_id, "path": ""}

        # =========================================================================
        # User Tools Management API
        # =========================================================================

        def get_user_tools(self, **kwargs) -> dict:
            """Get all user-created tools."""
            try:
                tools = self._user_tools_manager.to_button_configs()
                return {"success": True, "tools": tools}
            except Exception as e:
                logger.error(f"Failed to get user tools: {e}")
                return {"success": False, "message": str(e), "tools": []}

        def save_user_tool(
            self,
            id: str = "",
            name: str = "",
            toolType: str = "python",
            toolPath: str = "",
            icon: str = "Wrench",
            name_zh: str = "",
            description: str = "",
            description_zh: str = "",
            args: list = None,
            hosts: list = None,
        ) -> dict:
            """Save a user tool (create or update)."""
            if not name:
                return {"success": False, "message": "Name is required"}
            if not toolPath:
                return {"success": False, "message": "Tool path is required"}

            try:
                tool_data = {
                    "id": id,
                    "name": name,
                    "tool_type": toolType,
                    "tool_path": toolPath,
                    "icon": icon,
                    "name_zh": name_zh,
                    "description": description,
                    "description_zh": description_zh,
                    "args": args or [],
                    "hosts": hosts or [],
                }

                if id:
                    tool = self._user_tools_manager.update_tool(id, tool_data)
                    if tool:
                        return {"success": True, "message": "Tool updated", "tool": tool.to_dict()}
                    return {"success": False, "message": "Tool not found"}
                else:
                    tool = self._user_tools_manager.add_tool(tool_data)
                    return {"success": True, "message": "Tool created", "tool": tool.to_dict()}
            except Exception as e:
                logger.error(f"Failed to save user tool: {e}")
                return {"success": False, "message": str(e)}

        def delete_user_tool(self, id: str = "") -> dict:
            """Delete a user tool."""
            if not id:
                return {"success": False, "message": "Tool ID is required"}
            try:
                if self._user_tools_manager.delete_tool(id):
                    return {"success": True, "message": "Tool deleted"}
                return {"success": False, "message": "Tool not found"}
            except Exception as e:
                logger.error(f"Failed to delete user tool: {e}")
                return {"success": False, "message": str(e)}

        def export_user_tools(self, **kwargs) -> dict:
            """Export all user tools as JSON."""
            try:
                json_config = self._user_tools_manager.export_tools()
                return {"success": True, "config": json_config}
            except Exception as e:
                logger.error(f"Failed to export user tools: {e}")
                return {"success": False, "message": str(e)}

        def import_user_tools(self, config: str = "", merge: bool = True) -> dict:
            """Import user tools from JSON config."""
            if not config:
                return {"success": False, "message": "Config is required"}
            try:
                count = self._user_tools_manager.import_tools(config, merge)
                return {"success": True, "message": f"Imported {count} tools", "count": count}
            except Exception as e:
                logger.error(f"Failed to import user tools: {e}")
                return {"success": False, "message": str(e)}

        # =========================================================================
        # Window Control API
        # =========================================================================

        def close_main_window(self, **kwargs) -> dict:
            """Close the main shelf window."""
            # In desktop mode, closing is handled by the native window
            return {"success": True}

        def create_window(
            self,
            label: str = "",
            url: str = "",
            title: str = "Window",
            width: int = 500,
            height: int = 600,
        ) -> dict:
            """Create a new native window with WebView content.

            This allows JavaScript to request opening a new native window,
            useful for settings panels or other secondary UI.

            Args:
                label: Unique identifier for the window.
                url: URL to load in the new window.
                title: Window title.
                width: Window width in pixels.
                height: Window height in pixels.

            Returns:
                Dict with success status and window label.
            """
            if not label:
                return {"success": False, "message": "No label provided", "label": ""}

            # Check if window already exists
            if label in child_windows:
                # Focus existing window
                logger.info(f"Window '{label}' already exists, focusing")
                return {"success": True, "message": "Window already exists", "label": label}

            try:
                # Resolve URL
                if url.startswith("http://") or url.startswith("https://"):
                    load_url = url
                elif is_dev_mode():
                    # Dev mode: use Vite dev server
                    load_url = f"http://localhost:5173{url}"
                else:
                    # Production: use auroraview protocol
                    from auroraview.utils import get_auroraview_entry_url

                    # Strip leading slash for entry URL
                    entry_file = url.lstrip("/")
                    load_url = get_auroraview_entry_url(entry_file)

                logger.info(f"Creating child window '{label}' with URL: {load_url}")

                # Create new WebView for child window
                child_webview = WebView(
                    title=title,
                    width=width,
                    height=height,
                    url=load_url,
                    debug=debug,
                    context_menu=debug,
                    asset_root=dist_dir,
                )

                # Store reference
                child_windows[label] = child_webview

                # Show window in non-blocking mode
                child_webview.show(wait=False)

                logger.info(f"Created child window: {label}")
                return {"success": True, "message": "Window created", "label": label}

            except Exception as e:
                logger.error(f"Failed to create child window {label}: {e}")
                return {"success": False, "message": str(e), "label": label}

        def close_window(self, label: str = "") -> dict:
            """Close a child window by its label.

            Args:
                label: The window label to close.

            Returns:
                Dict with success status.
            """
            if not label:
                return {"success": False, "message": "No label provided"}

            if label not in child_windows:
                return {"success": False, "message": f"Window '{label}' not found"}

            try:
                child_webview = child_windows.pop(label)
                child_webview.close()
                logger.info(f"Closed child window: {label}")
                return {"success": True, "message": "Window closed"}
            except Exception as e:
                logger.error(f"Failed to close window {label}: {e}")
                return {"success": False, "message": str(e)}

    # Create and bind API
    api = DesktopShelfAPI(config, launcher, user_tools_manager)
    webview.bind_api(api)

    # Register event handlers for backward compatibility
    @webview.on("get_config")
    def handle_get_config(data: dict[str, Any]) -> None:
        config_dict = _config_to_dict(config, "desktop")
        webview.emit("config_response", config_dict)

    @webview.on("launch_tool")
    def handle_launch_tool(data: dict[str, Any]) -> None:
        button_id = data.get("buttonId", "")
        try:
            launcher.launch_by_id(button_id)
            webview.emit(
                "launch_result",
                {"success": True, "message": f"Tool launched: {button_id}", "buttonId": button_id},
            )
        except LaunchError as e:
            logger.error(f"Failed to launch tool {button_id}: {e}")
            webview.emit("launch_result", {"success": False, "message": str(e), "buttonId": button_id})

    @webview.on("get_tool_path")
    def handle_get_tool_path(data: dict[str, Any]) -> None:
        button_id = data.get("buttonId", "")
        path = ""
        for shelf in config.shelves:
            for button in shelf.buttons:
                if button.id == button_id:
                    path = str(launcher.resolve_path(button.tool_path))
                    break
        webview.emit("tool_path_response", {"buttonId": button_id, "path": path})

    # Register lifecycle event handlers
    @webview.on("__auroraview_ready")
    def handle_ready(data: dict[str, Any]) -> None:
        url = data.get("url", "")
        logger.info(f"Desktop: WebView ready (url={url})")
        # Re-register API methods when page navigates (JS environment is reset)
        # This is necessary because the event_bridge.js reinitializes window.auroraview
        # but the API methods need to be re-registered via register_api_methods
        logger.info("Desktop: Re-registering API methods after page navigation")
        webview.bind_api(api, allow_rebind=True)

    @webview.on("first_paint")
    def handle_first_paint(data: dict[str, Any]) -> None:
        logger.debug(f"Desktop: First paint at {data.get('time', 'unknown')}ms")

    # Setup shared state
    if webview.state is not None:
        with webview.state.batch_update() as batch:
            batch["app_name"] = title
            batch["dcc_mode"] = False
            batch["current_host"] = "desktop"
            batch["theme"] = "dark"
            batch["integration_mode"] = "standalone"

    # Load content
    if is_dev_mode():
        dev_url = "http://localhost:5173"
        logger.info(f"Loading dev URL: {dev_url}")
        webview.load_url(dev_url)
    else:
        from auroraview.utils import get_auroraview_entry_url

        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            auroraview_url = get_auroraview_entry_url("index.html")
            logger.info(f"Loading URL: {auroraview_url}")
            webview.load_url(auroraview_url)
        else:
            logger.error(f"index.html not found at {index_path}")
            return 1

    logger.info("Desktop: Starting native event loop (blocking)...")

    # Show window and run event loop (blocking)
    webview.show_blocking()

    # Cleanup: close all child windows
    logger.info(f"Desktop: Cleaning up {len(child_windows)} child windows...")
    for label, child in list(child_windows.items()):
        try:
            child.close()
            logger.debug(f"Closed child window: {label}")
        except Exception as e:
            logger.warning(f"Error closing child window {label}: {e}")
    child_windows.clear()

    logger.info("Desktop: Window closed")
    return 0
