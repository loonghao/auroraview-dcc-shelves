"""ShelfAPI - JavaScript API interface for DCC Shelves.

This module provides the ShelfAPI class that exposes Python methods
to JavaScript via the AuroraView bridge (window.auroraview.api.*).

Architecture (Qt-Style Pattern):
    - Signal definitions: Python → JavaScript notifications
    - API methods: JavaScript → Python calls with return values
    - Event handlers (on_ prefix): JavaScript → Python events (fire-and-forget)
    - setup_connections(): Signal-slot connections like Qt

Example:
    >>> from auroraview_dcc_shelves.ui.api import ShelfAPI
    >>>
    >>> # Signals are emitted to notify JavaScript
    >>> api.tool_launched.emit({"tool_id": "my_tool", "success": True})
    >>>
    >>> # API methods are called from JavaScript
    >>> result = api.launch_tool(button_id="my_tool")
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from auroraview import Signal

if TYPE_CHECKING:
    from auroraview_dcc_shelves.app import ShelfApp
    from auroraview_dcc_shelves.user_tools import UserToolsManager

from auroraview_dcc_shelves.launcher import LaunchError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def api_method(func: F) -> F:
    """Decorator for API methods to handle AuroraView params argument.

    AuroraView calls API methods with a single positional `params` dict argument.
    This decorator unpacks the params dict into keyword arguments, allowing
    methods to have typed parameters instead of **kwargs.

    Example:
        @api_method
        def launch_tool(self, button_id: str = "") -> dict:
            ...

        # Can be called as:
        # - launch_tool({"button_id": "my_tool"})  # From AuroraView
        # - launch_tool(button_id="my_tool")       # From Python
    """

    @functools.wraps(func)
    def wrapper(self: Any, params: Any = None, **kwargs: Any) -> Any:
        # If params is a dict, merge it with kwargs (params takes precedence)
        if isinstance(params, dict):
            # Get the function's parameter names (excluding 'self')
            sig = inspect.signature(func)
            valid_params = {k: v for k, v in params.items() if k in sig.parameters and k != "self"}
            # Merge: kwargs provides defaults, params overrides
            merged = {**kwargs, **valid_params}
            return func(self, **merged)
        # If params is not a dict (None or other), just pass kwargs
        return func(self, **kwargs)

    return wrapper  # type: ignore[return-value]


def _config_to_dict(config: Any, current_host: str = "") -> dict[str, Any]:
    """Convert ShelvesConfig to a dictionary for JSON serialization.

    Args:
        config: The shelves configuration.
        current_host: Current DCC host name for filtering tools.

    Returns:
        Dictionary suitable for JSON serialization.
    """
    from auroraview_dcc_shelves.utils import resolve_icon_path

    # Filter buttons by host if current_host is specified
    def is_available(button: Any) -> bool:
        if not current_host:
            return True
        return button.is_available_for_host(current_host)

    # Get base path for resolving relative icon paths
    base_path = config.base_path

    result: dict[str, Any] = {
        "shelves": [
            {
                "id": shelf.id,
                "name": shelf.name,
                "name_zh": shelf.name_zh,
                "buttons": [
                    {
                        "id": button.id,
                        "name": button.name,
                        "name_zh": button.name_zh,
                        "toolType": button.tool_type.value,
                        "toolPath": button.tool_path,
                        "icon": resolve_icon_path(button.icon, base_path),
                        "args": button.args,
                        "description": button.description,
                        "description_zh": button.description_zh,
                        "hosts": button.hosts,
                    }
                    for button in shelf.buttons
                    if is_available(button)
                ],
            }
            for shelf in config.shelves
        ],
        "currentHost": current_host or "standalone",
    }

    # Remove empty shelves after filtering
    result["shelves"] = [s for s in result["shelves"] if s["buttons"]]

    # Add banner config if not default
    if config.banner:
        banner_dict: dict[str, str] = {}
        if config.banner.title != "Toolbox":
            banner_dict["title"] = config.banner.title
        if config.banner.title_zh:
            banner_dict["title_zh"] = config.banner.title_zh
        if config.banner.subtitle != "Production Tools & Scripts":
            banner_dict["subtitle"] = config.banner.subtitle
        if config.banner.subtitle_zh:
            banner_dict["subtitle_zh"] = config.banner.subtitle_zh
        if config.banner.image:
            banner_dict["image"] = config.banner.image
        if config.banner.gradient_from:
            banner_dict["gradientFrom"] = config.banner.gradient_from
        if config.banner.gradient_to:
            banner_dict["gradientTo"] = config.banner.gradient_to
        if banner_dict:
            result["banner"] = banner_dict

    return result


class ShelfAPI:
    """API object exposed to JavaScript via auroraview.api.*

    This class provides methods that can be called from JavaScript
    through the AuroraView bridge. All methods should return dicts
    with a 'success' key for consistent error handling.

    Qt-Style Architecture:
        - Signals (Python → JS): Notifications about state changes
        - API methods (JS → Python): Request-response with return values
        - Event handlers (on_ prefix): Fire-and-forget events from JS

    Signals:
        tool_launched: Emitted when a tool is successfully launched
        tool_failed: Emitted when a tool launch fails
        config_updated: Emitted when configuration changes
        user_tools_changed: Emitted when user tools are modified
        window_created: Emitted when a child window is created
        window_closed: Emitted when a child window is closed
    """

    # ═══════════════════════════════════════════════════════════════════
    # Signal Definitions (Python → JavaScript notifications)
    # ═══════════════════════════════════════════════════════════════════
    # These signals notify JavaScript about state changes in Python.
    # JavaScript can listen via: auroraview.on("signal_name", handler)

    tool_launched = Signal(name="tool_launched")  # {tool_id, success, message}
    tool_failed = Signal(name="tool_failed")  # {tool_id, error}
    config_updated = Signal(name="config_updated")  # {config}
    user_tools_changed = Signal(name="user_tools_changed")  # {action, tool}
    window_created = Signal(name="window_created")  # {label, title}
    window_closed = Signal(name="window_closed")  # {label}

    def __init__(self, shelf_app: ShelfApp):
        self._shelf_app = shelf_app
        self._user_tools_manager: UserToolsManager | None = None
        self.setup_connections()

    # ═══════════════════════════════════════════════════════════════════
    # Signal Connections (Qt-style setup)
    # ═══════════════════════════════════════════════════════════════════

    def setup_connections(self) -> None:
        """Setup signal-slot connections.

        This method is called during initialization to connect signals
        to their handlers, similar to Qt's pattern.
        """
        # Connect internal signals to logging handlers
        self.tool_launched.connect(self._on_tool_launched)
        self.tool_failed.connect(self._on_tool_failed)
        self.user_tools_changed.connect(self._on_user_tools_changed)

    def _on_tool_launched(self, data: dict) -> None:
        """Internal handler for tool launch events."""
        logger.info(f"Tool launched: {data.get('tool_id')}")

    def _on_tool_failed(self, data: dict) -> None:
        """Internal handler for tool failure events."""
        logger.warning(f"Tool failed: {data.get('tool_id')} - {data.get('error')}")

    def _on_user_tools_changed(self, data: dict) -> None:
        """Internal handler for user tools changes."""
        logger.info(f"User tools changed: {data.get('action')}")

    # ═══════════════════════════════════════════════════════════════════
    # Private Helpers
    # ═══════════════════════════════════════════════════════════════════

    def _get_user_tools_manager(self) -> UserToolsManager:
        """Get or create the user tools manager."""
        if self._user_tools_manager is None:
            from auroraview_dcc_shelves.user_tools import UserToolsManager

            self._user_tools_manager = UserToolsManager()
        return self._user_tools_manager

    # ═══════════════════════════════════════════════════════════════════
    # API Methods (JavaScript → Python, with return values)
    # ═══════════════════════════════════════════════════════════════════
    # These methods are called from JavaScript via:
    #   await auroraview.api.method_name({param: value})

    @api_method
    def get_config(self) -> dict[str, Any]:
        """Return the current configuration as JSON."""
        return _config_to_dict(self._shelf_app._config, self._shelf_app._current_host)

    @api_method
    def launch_tool(self, button_id: str = "") -> dict[str, Any]:
        """Launch a tool by its button ID.

        Emits:
            tool_launched: On successful launch
            tool_failed: On launch failure
        """
        if not button_id:
            return {"success": False, "message": "No button_id provided", "buttonId": ""}

        try:
            result = self._shelf_app._launcher.launch_by_id(button_id)
            if isinstance(result, dict) and result.get("type") == "javascript":
                response = {
                    "success": True,
                    "message": f"JavaScript tool ready: {button_id}",
                    "buttonId": button_id,
                    "javascript": result.get("script", ""),
                }
                self.tool_launched.emit({"tool_id": button_id, "type": "javascript"})
                return response

            # Emit success signal
            self.tool_launched.emit({"tool_id": button_id, "success": True})
            return {"success": True, "message": f"Tool launched: {button_id}", "buttonId": button_id}
        except LaunchError as e:
            logger.error(f"Failed to launch tool {button_id}: {e}")
            # Emit failure signal
            self.tool_failed.emit({"tool_id": button_id, "error": str(e)})
            return {"success": False, "message": str(e), "buttonId": button_id}

    @api_method
    def get_tool_path(self, button_id: str = "") -> dict[str, Any]:
        """Get the resolved path for a tool."""
        path = ""
        for shelf in self._shelf_app._config.shelves:
            for button in shelf.buttons:
                if button.id == button_id:
                    path = str(self._shelf_app._launcher.resolve_path(button.tool_path))
                    break
        return {"buttonId": button_id, "path": path}

    @api_method
    def create_window(
        self,
        label: str = "",
        url: str = "",
        title: str = "Window",
        width: int = 500,
        height: int = 600,
    ) -> dict[str, Any]:
        """Create a new native window with WebView content.

        This allows JavaScript to request opening a new Qt dialog window,
        useful for settings panels or other secondary UI in DCC environments.

        Args:
            label: Unique identifier for the window.
            url: URL to load in the new window.
            title: Window title.
            width: Window width in pixels.
            height: Window height in pixels.

        Emits:
            window_created: On successful window creation

        Returns:
            Dict with success status and window label.
        """
        if not label:
            return {"success": False, "message": "No label provided", "label": ""}

        try:
            result = self._shelf_app.create_child_window(
                label=label,
                url=url,
                title=title,
                width=width,
                height=height,
            )
            if result.get("success"):
                # Emit signal for window creation
                self.window_created.emit({"label": label, "title": title, "url": url})
            return result
        except Exception as e:
            logger.error(f"Failed to create window {label}: {e}")
            return {"success": False, "message": str(e), "label": label}

    @api_method
    def close_window(self, label: str = "") -> dict[str, Any]:
        """Close a child window by its label.

        Args:
            label: The window label to close.

        Emits:
            window_closed: On successful window close

        Returns:
            Dict with success status.
        """
        if not label:
            return {"success": False, "message": "No label provided"}

        try:
            result = self._shelf_app.close_child_window(label)
            if result.get("success"):
                # Emit signal for window close
                self.window_closed.emit({"label": label})
            return result
        except Exception as e:
            logger.error(f"Failed to close window {label}: {e}")
            return {"success": False, "message": str(e)}

    # =========================================================================
    # User Tools Management API
    # =========================================================================

    @api_method
    def get_user_tools(self) -> dict[str, Any]:
        """Get all user-created tools.

        Returns:
            Dict with success status and list of tools.
        """
        logger.info("get_user_tools called")
        try:
            manager = self._get_user_tools_manager()
            tools = manager.to_button_configs()
            logger.info(f"get_user_tools: returning {len(tools)} tools")
            return {"success": True, "tools": tools}
        except Exception as e:
            logger.error(f"Failed to get user tools: {e}")
            return {"success": False, "message": str(e), "tools": []}

    @api_method
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
        args: list[str] | None = None,
        hosts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save a user tool (create or update).

        Args:
            id: Tool ID (empty for new tool).
            name: Tool display name (required).
            toolType: Tool type (python or executable).
            toolPath: Path to the tool script or executable (required).
            icon: Icon name.
            name_zh: Chinese name.
            description: Description.
            description_zh: Chinese description.
            args: Command line arguments.
            hosts: List of supported DCC hosts.

        Returns:
            Dict with success status and saved tool data.
        """
        logger.info(f"save_user_tool called: name={name}, toolType={toolType}, toolPath={toolPath}")

        if not name:
            return {"success": False, "message": "Name is required"}
        if not toolPath:
            return {"success": False, "message": "Tool path is required"}

        try:
            manager = self._get_user_tools_manager()
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
                # Update existing tool
                tool = manager.update_tool(id, tool_data)
                if tool:
                    # Emit signal for tool update
                    self.user_tools_changed.emit({"action": "updated", "tool": tool.to_dict()})
                    return {"success": True, "message": "Tool updated", "tool": tool.to_dict()}
                return {"success": False, "message": "Tool not found"}
            else:
                # Create new tool
                tool = manager.add_tool(tool_data)
                # Emit signal for tool creation
                self.user_tools_changed.emit({"action": "created", "tool": tool.to_dict()})
                return {"success": True, "message": "Tool created", "tool": tool.to_dict()}
        except Exception as e:
            logger.error(f"Failed to save user tool: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {"success": False, "message": str(e)}

    @api_method
    def delete_user_tool(self, id: str = "") -> dict[str, Any]:
        """Delete a user tool.

        Args:
            id: Tool ID to delete.

        Emits:
            user_tools_changed: On successful deletion

        Returns:
            Dict with success status.
        """
        logger.info(f"delete_user_tool called: id={id}")

        if not id:
            return {"success": False, "message": "Tool ID is required"}

        try:
            manager = self._get_user_tools_manager()
            if manager.delete_tool(id):
                # Emit signal for tool deletion
                self.user_tools_changed.emit({"action": "deleted", "tool_id": id})
                return {"success": True, "message": "Tool deleted"}
            return {"success": False, "message": "Tool not found"}
        except Exception as e:
            logger.error(f"Failed to delete user tool: {e}")
            return {"success": False, "message": str(e)}

    @api_method
    def export_user_tools(self) -> dict[str, Any]:
        """Export all user tools as JSON.

        Returns:
            Dict with success status and JSON string.
        """
        logger.info("export_user_tools called")
        try:
            manager = self._get_user_tools_manager()
            json_config = manager.export_tools()
            return {"success": True, "config": json_config}
        except Exception as e:
            logger.error(f"Failed to export user tools: {e}")
            return {"success": False, "message": str(e)}

    @api_method
    def import_user_tools(
        self,
        config: str = "",
        merge: bool = True,
    ) -> dict[str, Any]:
        """Import user tools from JSON config.

        Args:
            config: JSON configuration string.
            merge: If True, merge with existing tools.

        Returns:
            Dict with success status and import count.
        """
        logger.info(f"import_user_tools called: config_len={len(config)}, merge={merge}")

        if not config:
            return {"success": False, "message": "Config is required"}

        try:
            manager = self._get_user_tools_manager()
            count = manager.import_tools(config, merge)
            return {"success": True, "message": f"Imported {count} tools", "count": count}
        except Exception as e:
            logger.error(f"Failed to import user tools: {e}")
            return {"success": False, "message": str(e)}

    # =========================================================================
    # Window Control API
    # =========================================================================

    @api_method
    def start_drag(self) -> dict[str, Any]:
        """Start window dragging for frameless window.

        This is called from the HTML title bar to initiate window drag.

        Strategy:
        1. Always use the Qt dialog's HWND for dragging
        2. This allows dragging the DCC Shelves window independently
        3. For embedded WebView, we need to release capture first

        Returns:
            Dict with success status.
        """
        try:
            dialog = self._shelf_app._dialog
            if dialog is None:
                return {"success": False, "message": "No dialog available"}

            import sys

            if sys.platform == "win32":
                import ctypes

                # Get Win32 APIs
                user32 = ctypes.windll.user32
                ReleaseCapture = user32.ReleaseCapture
                SendMessageW = user32.SendMessageW
                PostMessageW = user32.PostMessageW

                # Constants
                WM_NCLBUTTONDOWN = 0x00A1
                WM_SYSCOMMAND = 0x0112
                SC_MOVE = 0xF010
                HTCAPTION = 2

                # Get HWND from Qt dialog (the shelf window itself)
                hwnd = int(dialog.winId())
                if not hwnd:
                    return {"success": False, "message": "Could not get HWND"}

                logger.debug(f"[ShelfAPI] Starting drag for dialog HWND=0x{hwnd:X}")

                # Method 1: ReleaseCapture + WM_NCLBUTTONDOWN
                # This is the standard way to initiate window drag
                ReleaseCapture()
                result = SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)

                if result == 0:
                    logger.debug("[ShelfAPI] Window drag initiated via WM_NCLBUTTONDOWN")
                    return {"success": True}

                # Method 2: Fallback to WM_SYSCOMMAND + SC_MOVE
                # This can work better in some embedded scenarios
                logger.debug("[ShelfAPI] Trying fallback SC_MOVE method")
                PostMessageW(hwnd, WM_SYSCOMMAND, SC_MOVE | HTCAPTION, 0)
                return {"success": True}
            else:
                # Non-Windows: not implemented yet
                return {"success": False, "message": "Window dragging not supported on this platform"}

        except Exception as e:
            logger.error(f"Failed to start window drag: {e}")
            return {"success": False, "message": str(e)}

    @api_method
    def close_main_window(self) -> dict[str, Any]:
        """Close the main shelf window.

        Returns:
            Dict with success status.
        """
        try:
            self._shelf_app.close()
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to close window: {e}")
            return {"success": False, "message": str(e)}
