"""AuroraView-based UI for DCC tool shelves.

This module provides the ShelfApp class for displaying and interacting
with the tool shelf interface.

Architecture:
    For DCC applications (Maya, Houdini, Nuke), uses AuroraView's layered architecture:

    ShelfApp (Application Layer)
        ↓ uses
    QtWebView (Integration Layer) - For DCC apps with Qt docking support
    AuroraView (HWND Layer) - For DCC apps without Qt or Unreal Engine
    WebView (Abstraction Layer) - For standalone
        ↓ wraps
    AuroraView (Rust Core Layer)

Integration Modes:
    - "qt": Uses QtWebView for native Qt widget integration (supports QDockWidget)
    - "hwnd": Uses AuroraView with HWND for non-Qt apps (e.g., Unreal Engine)

Best Practices:
    - Uses QtWebView with automatic event processing for DCC apps
    - No manual process_events() calls needed
    - No scriptJob required for event handling
    - Clean integration with DCC's Qt event loop
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

# Import WebView for standalone mode
from auroraview import WebView

# Try to import Qt components for DCC integration
QT_AVAILABLE = False
try:
    from auroraview import AuroraView, QtWebView

    QT_AVAILABLE = True
except ImportError:
    AuroraView = None  # type: ignore
    QtWebView = None  # type: ignore

if TYPE_CHECKING:
    from auroraview_dcc_shelves.config import ButtonConfig, ShelvesConfig

from auroraview_dcc_shelves.apps import DCCAdapter, get_adapter
from auroraview_dcc_shelves.launcher import LaunchError, ToolLauncher
from auroraview_dcc_shelves.settings import WindowSettingsManager

logger = logging.getLogger(__name__)

# Path to the frontend dist directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DIST_DIR = Path(__file__).parent.parent.parent / "dist"

# =============================================================================
# Window Configuration
# Keep in sync with frontend CSS (App.tsx: min-w-[280px] max-w-[480px])
# =============================================================================
MAIN_WINDOW_CONFIG = {
    "min_width": 280,
    "min_height": 300,
    "max_width": 480,
    "max_height": 0,  # 0 = no limit
    "default_width": 400,
    "default_height": 600,
}

SETTINGS_WINDOW_CONFIG = {
    "min_width": 400,
    "min_height": 500,
    "max_width": 600,
    "max_height": 800,
    "default_width": 520,
    "default_height": 650,
}

# Type alias for integration mode
IntegrationMode = Literal["qt", "hwnd"]

# DCC-specific timer optimization settings
# DEPRECATED: Timer settings are now managed by DCC adapters (apps/*.py)
# This dict is kept for backward compatibility only.
# Use: get_adapter(app_name).timer_interval_ms instead
DCC_TIMER_SETTINGS: dict[str, dict[str, int]] = {
    "maya": {"interval_ms": 16},      # Maya: 60 FPS, responsive UI
    "houdini": {"interval_ms": 50},   # Houdini: 20 FPS, reduced overhead
    "nuke": {"interval_ms": 32},      # Nuke: 30 FPS, balanced
    "3dsmax": {"interval_ms": 32},    # 3ds Max: 30 FPS
    "max": {"interval_ms": 32},       # Alias for 3ds Max
    "unreal": {"interval_ms": 16},    # Unreal: 60 FPS
    "default": {"interval_ms": 16},   # Default: 60 FPS
}

# Flat Apple-style QSS - deep dark background matching WebView content
# Uses the same gradient colors as frontend to prevent white flash
FLAT_STYLE_QSS = """
/* Main dialog - dark background matching WebView content */
/* This prevents white flash during WebView initialization */
QDialog {
    background-color: #0d0d0d;
    border: none;
}

/* Frame with transparent background */
QFrame {
    background-color: transparent;
    border: none;
}

/* Scrollbar - minimal Apple-style */
QScrollBar:vertical {
    background-color: transparent;
    width: 6px;
    margin: 4px 2px 4px 2px;
    border: none;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.12);
    min-height: 30px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(255, 255, 255, 0.20);
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    background: transparent;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

/* Horizontal scrollbar */
QScrollBar:horizontal {
    background-color: transparent;
    height: 6px;
    margin: 2px 4px 2px 4px;
    border: none;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(255, 255, 255, 0.12);
    min-width: 30px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(255, 255, 255, 0.20);
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
    background: transparent;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* Tooltip styling */
QToolTip {
    background-color: #2d2d44;
    color: #ffffff;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Size grip - subtle */
QSizeGrip {
    background-color: transparent;
    width: 16px;
    height: 16px;
}

/* Loading indicator */
QLabel#loadingLabel {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    font-weight: 500;
}
"""

# Loading indicator style for deferred initialization
LOADING_STYLE_QSS = """
QDialog {
    background-color: #0d0d0d;
    border: none;
}
QLabel {
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    font-weight: 500;
}
"""


def _is_local_icon_path(icon: str) -> bool:
    """Check if an icon string is a local file path (not a Lucide icon name).

    Args:
        icon: The icon string to check.

    Returns:
        True if it's a local file path, False if it's an icon name.
    """
    if not icon:
        return False
    # Check for file extensions commonly used for icons
    extensions = [".svg", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp"]
    if any(icon.lower().endswith(ext) for ext in extensions):
        return True
    # Check for relative path indicators
    if icon.startswith("./") or icon.startswith("../") or icon.startswith("icons/"):
        return True
    # Check if it contains path separators
    return "/" in icon or "\\" in icon


def _resolve_icon_path(icon: str, base_path: Path | None) -> str:
    """Resolve icon path to absolute path if it is a local file.

    Args:
        icon: The icon string (could be Lucide name or local path).
        base_path: Base path of the config file for resolving relative paths.

    Returns:
        Resolved absolute path for local icons, or original icon name.
    """
    if not _is_local_icon_path(icon) or not base_path:
        return icon

    # Resolve relative path against config base path
    icon_path = Path(icon)
    if not icon_path.is_absolute():
        icon_path = (base_path / icon).resolve()

    # Return as normalized path string with forward slashes
    return str(icon_path).replace("\\", "/")


def _config_to_dict(config: ShelvesConfig, current_host: str = "") -> dict[str, Any]:
    """Convert ShelvesConfig to a dictionary for JSON serialization.

    Args:
        config: The shelves configuration.
        current_host: Current DCC host name for filtering tools.

    Returns:
        Dictionary suitable for JSON serialization.
    """

    # Filter buttons by host if current_host is specified
    def is_available(button: ButtonConfig) -> bool:
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
                        "icon": _resolve_icon_path(button.icon, base_path),
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
        if config.banner.subtitle != "Production Tools & Scripts":
            banner_dict["subtitle"] = config.banner.subtitle
        if config.banner.image:
            banner_dict["image"] = config.banner.image
        if config.banner.gradient_from:
            banner_dict["gradientFrom"] = config.banner.gradient_from
        if config.banner.gradient_to:
            banner_dict["gradientTo"] = config.banner.gradient_to
        if banner_dict:
            result["banner"] = banner_dict

    return result


# Note: DCC-specific main window functions have been moved to apps/ adapters
# See: apps/maya.py, apps/houdini.py, apps/nuke.py, apps/max3ds.py, apps/unreal.py


class ShelfAPI:
    """API object exposed to JavaScript via auroraview.api.*"""

    def __init__(self, shelf_app: ShelfApp):
        self._shelf_app = shelf_app

    def get_config(self, _params: Any = None) -> dict[str, Any]:
        """Return the current configuration as JSON."""
        return _config_to_dict(self._shelf_app._config, self._shelf_app._current_host)

    def launch_tool(self, button_id: str = "", **kwargs: Any) -> dict[str, Any]:
        """Launch a tool by its button ID."""
        if not button_id:
            return {"success": False, "message": "No button_id provided", "buttonId": ""}

        try:
            result = self._shelf_app._launcher.launch_by_id(button_id)
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

    def get_tool_path(self, button_id: str = "", **kwargs: Any) -> dict[str, Any]:
        """Get the resolved path for a tool."""
        path = ""
        for shelf in self._shelf_app._config.shelves:
            for button in shelf.buttons:
                if button.id == button_id:
                    path = str(self._shelf_app._launcher.resolve_path(button.tool_path))
                    break
        return {"buttonId": button_id, "path": path}

    def create_window(
        self,
        label: str = "",
        url: str = "",
        title: str = "Window",
        width: int = 500,
        height: int = 600,
        **kwargs: Any,
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
            return result
        except Exception as e:
            logger.error(f"Failed to create window {label}: {e}")
            return {"success": False, "message": str(e), "label": label}

    def close_window(self, label: str = "", **kwargs: Any) -> dict[str, Any]:
        """Close a child window by its label.

        Args:
            label: The window label to close.

        Returns:
            Dict with success status.
        """
        if not label:
            return {"success": False, "message": "No label provided"}

        try:
            result = self._shelf_app.close_child_window(label)
            return result
        except Exception as e:
            logger.error(f"Failed to close window {label}: {e}")
            return {"success": False, "message": str(e)}


class ShelfApp:
    """AuroraView-based application for displaying tool shelves.

    This class creates a WebView window displaying the shelf UI and
    handles communication between the frontend and Python backend.

    Integration Modes:
        - "qt": Uses QtWebView for native Qt widget integration
                Best for Maya, Houdini, Nuke - supports QDockWidget docking
        - "hwnd": Uses AuroraView with HWND for non-Qt integration
                Best for Unreal Engine or when Qt integration causes issues

    Args:
        config: The shelves configuration to display.
        title: Window title. Defaults to "DCC Shelves".
        width: Window width in pixels. Defaults to 800.
        height: Window height in pixels. Defaults to 600.

    Example (Qt mode - default)::

        from auroraview_dcc_shelves import ShelfApp, load_config

        config = load_config("shelf_config.yaml")
        app = ShelfApp(config)
        app.show(app="maya", mode="qt")

    Example (HWND mode)::

        from auroraview_dcc_shelves import ShelfApp, load_config

        config = load_config("shelf_config.yaml")
        app = ShelfApp(config)
        app.show(app="maya", mode="hwnd")

        # Get HWND for external integration (e.g., Unreal Engine)
        hwnd = app.get_hwnd()
        if hwnd:
            import unreal
            unreal.parent_external_window_to_slate(hwnd)
    """

    def __init__(
        self,
        config: ShelvesConfig,
        title: str = "DCC Shelves",
        width: int = 800,
        height: int = 600,
        remember_size: bool = True,
    ) -> None:
        self._config = config
        self._title = title
        self._default_width = width
        self._default_height = height
        self._remember_size = remember_size
        self._launcher: ToolLauncher | None = None
        self._webview: Any = None  # WebView or QtWebView
        self._dialog: Any = None  # QDialog for Qt mode
        self._auroraview: Any = None  # AuroraView wrapper
        self._api: ShelfAPI | None = None
        self._dcc_mode = False
        self._current_host = ""
        self._settings_manager: WindowSettingsManager | None = None
        self._integration_mode: IntegrationMode = "qt"  # Default to Qt mode
        self._child_windows: dict[str, Any] = {}  # Child windows by label
        self._adapter: DCCAdapter | None = None  # DCC adapter instance

    def _is_dev_mode(self) -> bool:
        """Check if running in development mode (no dist build)."""
        dist_index = DIST_DIR / "index.html"
        return not dist_index.exists()

    def _get_dcc_parent_window(self, app: str) -> Any:
        """Get the DCC main window based on app type.

        Uses the DCC adapter system to get the appropriate parent window.
        """
        adapter = get_adapter(app)
        parent_window = adapter.get_main_window()

        if parent_window is None:
            raise RuntimeError(
                f"Could not get {app} main window. Please ensure {app} UI is fully loaded."
            )
        return parent_window


    def _register_api(self, webview: WebView) -> None:
        """Register Python API methods for the frontend (standalone mode)."""

        @webview.on("get_config")
        def handle_get_config(data: dict[str, Any]) -> None:
            config_dict = _config_to_dict(self._config, self._current_host)
            webview.emit("config_response", config_dict)

        @webview.on("launch_tool")
        def handle_launch_tool(data: dict[str, Any]) -> None:
            button_id = data.get("buttonId", "")
            try:
                self._launcher.launch_by_id(button_id)
                webview.emit("launch_result", {
                    "success": True, "message": f"Tool launched: {button_id}", "buttonId": button_id
                })
            except LaunchError as e:
                logger.error(f"Failed to launch tool {button_id}: {e}")
                webview.emit("launch_result", {
                    "success": False, "message": str(e), "buttonId": button_id
                })

        @webview.on("get_tool_path")
        def handle_get_tool_path(data: dict[str, Any]) -> None:
            button_id = data.get("buttonId", "")
            path = ""
            for shelf in self._config.shelves:
                for button in shelf.buttons:
                    if button.id == button_id:
                        path = str(self._launcher.resolve_path(button.tool_path))
                        break
            webview.emit("tool_path_response", {"buttonId": button_id, "path": path})


    def _show_qt_mode(self, debug: bool, app: str) -> None:
        """Show using QtWebView for Qt-native integration (non-blocking).

        This mode creates a true Qt widget that can be docked, embedded in
        layouts, and managed by Qt's parent-child system.

        Best for: Maya, Houdini, Nuke, 3ds Max
        """
        if not QT_AVAILABLE:
            raise RuntimeError(
                "Qt integration not available. Install with: pip install auroraview[qt]"
            )

        app_lower = app.lower()
        parent_window = self._get_dcc_parent_window(app)

        from qtpy.QtCore import Qt, QTimer
        from qtpy.QtWidgets import QDialog, QVBoxLayout

        self._settings_manager = WindowSettingsManager(app_lower)

        if self._remember_size:
            settings = self._settings_manager.load()
            self._width = settings.width if settings.width > 0 else self._default_width
            self._height = settings.height if settings.height > 0 else self._default_height
        else:
            self._width = self._default_width
            self._height = self._default_height

        self._dialog = QDialog(parent_window)
        self._dialog.setWindowTitle(self._title)
        self._dialog.setSizeGripEnabled(True)
        self._dialog.setStyleSheet(LOADING_STYLE_QSS)
        self._dialog.setWindowFlags(
            Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
        )
        self._dialog.resize(self._width, self._height)
        # Apply size constraints from config
        self._dialog.setMinimumSize(
            MAIN_WINDOW_CONFIG["min_width"],
            MAIN_WINDOW_CONFIG["min_height"]
        )
        if MAIN_WINDOW_CONFIG["max_width"] > 0:
            self._dialog.setMaximumWidth(MAIN_WINDOW_CONFIG["max_width"])
        if MAIN_WINDOW_CONFIG["max_height"] > 0:
            self._dialog.setMaximumHeight(MAIN_WINDOW_CONFIG["max_height"])

        if self._remember_size:
            original_close = self._dialog.closeEvent
            def save_on_close(event):
                self._settings_manager.save_from_dialog(self._dialog)
                original_close(event)
            self._dialog.closeEvent = save_on_close

        self._layout = QVBoxLayout(self._dialog)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._dialog.show()
        logger.info("Qt mode - Dialog shown, deferring WebView initialization...")

        self._init_params = {"debug": debug, "app_lower": app_lower}
        QTimer.singleShot(10, self._init_webview_deferred_qt)


    def _init_webview_deferred_qt(self) -> None:
        """Initialize WebView in Qt mode (deferred)."""
        debug = self._init_params["debug"]
        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        self._dialog.setStyleSheet(FLAT_STYLE_QSS)

        self._placeholder = QtWebView.create_deferred(
            parent=self._dialog,
            dev_tools=debug,
            context_menu=False,
            asset_root=dist_dir,
            embed_mode="owner",
            on_ready=self._on_webview_ready_qt,
            on_error=self._on_webview_error,
        )
        self._layout.addWidget(self._placeholder)

    def _on_webview_ready_qt(self, webview: "QtWebView") -> None:
        """Called when QtWebView is ready."""
        from qtpy.QtWidgets import QSizePolicy

        logger.info("Qt mode - WebView ready, completing initialization...")
        self._webview = webview
        self._webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._webview.setMinimumSize(self._width, self._height)

        self._layout.removeWidget(self._placeholder)
        self._placeholder.deleteLater()
        self._placeholder = None
        self._layout.addWidget(self._webview)

        self._api = ShelfAPI(self)
        self._auroraview = AuroraView(
            parent=self._dialog,
            api=self._api,
            _view=self._webview,
            _keep_alive_root=self._dialog,
        )

        self._load_content()
        self._register_window_events()
        self._setup_shared_state()
        self._register_commands()
        self._webview.show()
        self._schedule_geometry_fixes()

        # Call adapter's on_show hook
        if self._adapter:
            self._adapter.on_show(self)

        logger.info("Qt mode - WebView initialization complete!")


    def _show_hwnd_mode(self, debug: bool, app: str) -> None:
        """Show using AuroraView with HWND integration (non-blocking).

        This mode creates a standalone WebView window that can be embedded
        using HWND APIs. The window follows the parent but is not a true
        Qt child widget.

        Best for: Unreal Engine, non-Qt applications, or when Qt mode
        causes issues with the DCC main thread.
        """
        import threading

        app_lower = app.lower()
        self._settings_manager = WindowSettingsManager(f"{app_lower}_hwnd")

        if self._remember_size:
            settings = self._settings_manager.load()
            self._width = settings.width if settings.width > 0 else self._default_width
            self._height = settings.height if settings.height > 0 else self._default_height
        else:
            self._width = self._default_width
            self._height = self._default_height

        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        logger.info("HWND mode - Starting WebView in background thread...")

        self._api = ShelfAPI(self)

        def _create_webview_thread():
            """Create WebView in background thread (STA-compatible)."""
            try:
                # Import WebView directly for thread-safe creation
                from auroraview import WebView

                logger.info("HWND thread - Creating WebView...")

                # Create WebView directly (not AuroraView wrapper)
                # This runs the WebView event loop in this thread
                webview = WebView(
                    title=self._title,
                    width=self._width,
                    height=self._height,
                    debug=debug,
                    context_menu=False,
                    asset_root=dist_dir,
                )

                # Store for cross-thread access
                self._webview = webview

                # Bind API
                webview.bind_api(self._api)

                # Load content
                if self._is_dev_mode():
                    dev_url = "http://localhost:5173"
                    logger.info(f"HWND thread - Loading dev URL: {dev_url}")
                    webview.load_url(dev_url)
                else:
                    index_path = DIST_DIR / "index.html"
                    if index_path.exists():
                        logger.info(f"HWND thread - Loading file: {index_path}")
                        webview.load_file(str(index_path.resolve()))

                # Setup shared state
                state = webview.state
                with state.batch_update() as batch:
                    batch["app_name"] = self._title
                    batch["dcc_mode"] = self._dcc_mode
                    batch["current_host"] = self._current_host
                    batch["theme"] = "dark"
                    batch["integration_mode"] = self._integration_mode

                logger.info("HWND thread - Starting WebView event loop (blocking this thread)...")

                # This blocks until the window is closed
                webview.show_blocking()

                logger.info("HWND thread - WebView closed")

            except Exception as e:
                logger.error(f"HWND thread - Error: {e}", exc_info=True)

        # Start WebView in background thread (daemon so it doesn't block app exit)
        self._webview_thread = threading.Thread(
            target=_create_webview_thread,
            name="AuroraView-HWND",
            daemon=True,
        )
        self._webview_thread.start()

        logger.info("HWND mode - Background thread started, main thread free!")


    def _load_content(self) -> None:
        """Load the frontend content into the WebView."""
        if self._is_dev_mode():
            dev_url = "http://localhost:5173"
            logger.info(f"Loading dev URL: {dev_url}")
            self._webview.load_url(dev_url)
        else:
            index_path = DIST_DIR / "index.html"
            if index_path.exists():
                logger.info(f"Loading file: {index_path}")
                self._webview.load_file(str(index_path.resolve()))
            else:
                raise FileNotFoundError(f"index.html not found at {index_path}")

    def _on_webview_error(self, error_msg: str) -> None:
        """Called if WebView creation fails."""
        logger.error(f"Failed to create WebView: {error_msg}")

    def _schedule_geometry_fixes(self) -> None:
        """Schedule geometry fixes for DCC apps (especially Nuke)."""
        from qtpy.QtCore import QTimer
        from qtpy.QtWidgets import QApplication

        def force_geometry():
            if not self._dialog or not self._webview:
                return
            self._dialog.setMinimumSize(self._width, self._height)
            self._dialog.resize(self._width, self._height)
            self._webview.setMinimumSize(self._width, self._height)
            self._dialog.updateGeometry()
            self._webview.updateGeometry()
            QApplication.processEvents()
            logger.debug(f"Forced geometry {self._width}x{self._height}")

        for delay in [100, 500, 1000, 2000]:
            QTimer.singleShot(delay, force_geometry)


    def _show_standalone_mode(self, debug: bool) -> None:
        """Show using regular WebView for standalone mode (blocking)."""
        self._settings_manager = WindowSettingsManager("standalone")

        if self._remember_size:
            settings = self._settings_manager.load()
            self._width = settings.width if settings.width > 0 else self._default_width
            self._height = settings.height if settings.height > 0 else self._default_height
        else:
            self._width = self._default_width
            self._height = self._default_height

        create_params: dict[str, Any] = {
            "title": self._title,
            "width": self._width,
            "height": self._height,
            "debug": debug,
        }

        if self._is_dev_mode():
            dev_url = "http://localhost:5173"
            logger.info(f"Standalone mode - Loading dev URL: {dev_url}")
            create_params["url"] = dev_url
            self._webview = WebView.create(**create_params)
        else:
            logger.info("Standalone mode - Loading production build")
            create_params["asset_root"] = str(DIST_DIR)
            self._webview = WebView.create(**create_params)

            if sys.platform == "win32":
                auroraview_url = "https://auroraview.localhost/index.html"
            else:
                auroraview_url = "auroraview://index.html"

            logger.info(f"Loading URL: {auroraview_url}")
            self._webview.load_url(auroraview_url)

        self._register_api(self._webview)
        self._setup_shared_state()
        self._register_commands()
        self._webview.show()

        # Call adapter's on_show hook
        if self._adapter:
            self._adapter.on_show(self)


    def show(
        self,
        debug: bool = False,
        app: str | None = None,
        mode: IntegrationMode = "qt",
    ) -> None:
        """Show the shelf window.

        For DCC applications (Maya, Houdini, Nuke), pass the `app` parameter to
        enable embedded mode which prevents UI blocking.

        Args:
            debug: Enable debug mode with developer tools (F12 or right-click).
            app: DCC application name for parent integration (e.g., "maya",
                "houdini", "nuke"). If provided, will use non-blocking mode.
            mode: Integration mode for DCC apps:
                - "qt": Uses QtWebView for native Qt widget integration.
                    Best for Maya, Houdini, Nuke - supports QDockWidget docking.
                - "hwnd": Uses AuroraView with HWND for non-Qt integration.
                    Best for Unreal Engine or when Qt mode causes issues.

        Example (Qt mode - supports docking)::

            app = ShelfApp(config)
            app.show(app="maya", mode="qt")

        Example (HWND mode - standalone window)::

            app = ShelfApp(config)
            app.show(app="maya", mode="hwnd")

            # Get HWND for Unreal integration
            hwnd = app.get_hwnd()
        """
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Asset root: {DIST_DIR}")
        logger.info(f"DCC app: {app}")
        logger.info(f"Integration mode: {mode}")

        self._current_host = app.lower() if app else ""
        self._integration_mode = mode
        logger.info(f"Current host: {self._current_host}")

        # Initialize DCC adapter
        self._adapter = get_adapter(app)
        logger.info(f"Using DCC adapter: {self._adapter.name} "
                    f"(timer: {self._adapter.timer_interval_ms}ms, "
                    f"recommended mode: {self._adapter.recommended_mode})")

        # Call adapter's on_init hook
        self._adapter.on_init(self)

        self._dcc_mode = bool(app and QT_AVAILABLE)
        self._launcher = ToolLauncher(self._config, dcc_mode=self._dcc_mode)
        logger.info(f"Launcher created with dcc_mode={self._dcc_mode}")

        if self._dcc_mode:
            if mode == "hwnd":
                self._show_hwnd_mode(debug, app)
            else:
                self._show_qt_mode(debug, app)
        else:
            if app and not QT_AVAILABLE:
                logger.warning(
                    f"Qt integration requested for {app} but not available. "
                    "Using standalone mode. Install with: pip install auroraview[qt]"
                )
            self._show_standalone_mode(debug)


    def get_hwnd(self) -> int | None:
        """Get the native window handle (HWND) of the WebView.

        This is primarily used for HWND mode integration with applications
        like Unreal Engine that can embed windows via HWND.

        Returns:
            int: The native window handle (HWND on Windows), or None if
                not available (e.g., before show() is called).

        Example (Unreal Engine)::

            app = ShelfApp(config)
            app.show(app="unreal", mode="hwnd")

            hwnd = app.get_hwnd()
            if hwnd:
                import unreal
                unreal.parent_external_window_to_slate(hwnd)
        """
        if self._auroraview and hasattr(self._auroraview, "get_hwnd"):
            return self._auroraview.get_hwnd()
        if self._webview and hasattr(self._webview, "get_hwnd"):
            return self._webview.get_hwnd()
        return None

    def update_config(self, config: ShelvesConfig) -> None:
        """Update the configuration and notify the frontend."""
        self._config = config
        self._launcher = ToolLauncher(config)
        if self._webview:
            config_dict = _config_to_dict(config, self._current_host)
            self._webview.emit("config_updated", config_dict)

    def create_child_window(
        self,
        label: str,
        url: str,
        title: str = "Window",
        width: int = 500,
        height: int = 600,
    ) -> dict[str, Any]:
        """Create a new child window with WebView content.

        Creates a Qt dialog with a WebView for displaying secondary UI
        like settings panels. Only works in DCC (Qt) mode.

        Args:
            label: Unique identifier for the window.
            url: URL to load in the new window.
            title: Window title.
            width: Window width in pixels.
            height: Window height in pixels.

        Returns:
            Dict with success status and window label.
        """
        # Check if window already exists
        if label in self._child_windows:
            existing = self._child_windows[label]
            if existing.get("dialog") and existing["dialog"].isVisible():
                existing["dialog"].raise_()
                existing["dialog"].activateWindow()
                return {"success": True, "message": "Window focused", "label": label}

        if not self._dcc_mode or not QT_AVAILABLE:
            return {
                "success": False,
                "message": "Child windows only supported in DCC Qt mode",
                "label": label,
            }

        try:
            from qtpy.QtCore import Qt
            from qtpy.QtWidgets import QDialog, QVBoxLayout

            # Create dialog with main window as parent
            parent = self._dialog if self._dialog else None
            dialog = QDialog(parent)
            dialog.setWindowTitle(title)
            dialog.setStyleSheet(FLAT_STYLE_QSS)
            dialog.setWindowFlags(
                Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
            )

            # Get window config based on label (default to settings config)
            window_config = SETTINGS_WINDOW_CONFIG if label == "settings" else SETTINGS_WINDOW_CONFIG

            # Apply size from config, respecting passed width/height as hints
            effective_width = width if width > 0 else window_config["default_width"]
            effective_height = height if height > 0 else window_config["default_height"]
            dialog.resize(effective_width, effective_height)

            # Apply size constraints
            dialog.setMinimumSize(window_config["min_width"], window_config["min_height"])
            if window_config["max_width"] > 0:
                dialog.setMaximumWidth(window_config["max_width"])
            if window_config["max_height"] > 0:
                dialog.setMaximumHeight(window_config["max_height"])

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Create QtWebView for the child window
            dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None
            webview = QtWebView(
                dialog,
                dev_tools=False,
                context_menu=False,
                asset_root=dist_dir,
            )
            layout.addWidget(webview)

            # Load URL - handle different URL formats
            if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
                # Dev server URL - load directly
                logger.info(f"Child window loading dev URL: {url}")
                webview.load_url(url)
            elif "auroraview.localhost" in url or url.startswith("auroraview://"):
                # AuroraView protocol URL - extract path and load as file
                # (same approach as main window in production mode)
                if "auroraview.localhost" in url:
                    # https://auroraview.localhost/settings.html -> settings.html
                    path = url.split("auroraview.localhost/")[-1]
                else:
                    # auroraview://settings.html -> settings.html
                    path = url.replace("auroraview://", "")
                file_path = DIST_DIR / path
                if file_path.exists():
                    logger.info(f"Child window loading file: {file_path}")
                    webview.load_file(str(file_path.resolve()))
                else:
                    logger.warning(f"Child window file not found: {file_path}")
                    webview.load_url(url)
            elif url.startswith("http"):
                # External HTTP URL
                logger.info(f"Child window loading external URL: {url}")
                webview.load_url(url)
            else:
                # Relative path - resolve to file
                file_path = DIST_DIR / url.lstrip("/")
                if file_path.exists():
                    logger.info(f"Child window loading relative path: {file_path}")
                    webview.load_file(str(file_path.resolve()))
                else:
                    logger.warning(f"Child window path not found: {file_path}")
                    webview.load_url(url)

            # Store reference
            self._child_windows[label] = {
                "dialog": dialog,
                "webview": webview,
            }

            # Clean up on close
            def on_close():
                if label in self._child_windows:
                    del self._child_windows[label]

            dialog.finished.connect(on_close)

            # Show the dialog
            dialog.show()
            logger.info(f"Created child window: {label}")

            return {"success": True, "message": "Window created", "label": label}

        except Exception as e:
            logger.error(f"Failed to create child window {label}: {e}")
            return {"success": False, "message": str(e), "label": label}

    def close_child_window(self, label: str) -> dict[str, Any]:
        """Close a child window by its label.

        Args:
            label: The window label to close.

        Returns:
            Dict with success status.
        """
        if label not in self._child_windows:
            return {"success": False, "message": f"Window '{label}' not found"}

        try:
            window_data = self._child_windows[label]
            dialog = window_data.get("dialog")
            if dialog:
                dialog.close()
            del self._child_windows[label]
            logger.info(f"Closed child window: {label}")
            return {"success": True, "message": "Window closed"}
        except Exception as e:
            logger.error(f"Failed to close child window {label}: {e}")
            return {"success": False, "message": str(e)}

    def _register_window_events(self) -> None:
        """Register window event handlers for DCC mode."""
        if not self._webview:
            return

        @self._webview.on("window_resize")
        def handle_resize(data: dict[str, Any]) -> None:
            width = data.get("width", 0)
            height = data.get("height", 0)
            if width > 0 and height > 0 and self._settings_manager:
                self._settings_manager.save(width, height)
                logger.debug(f"Window resized to {width}x{height}")

    def _setup_shared_state(self) -> None:
        """Initialize shared state for bidirectional sync."""
        if not self._webview:
            return

        state = self._webview.state
        with state.batch_update() as batch:
            batch["app_name"] = self._title
            batch["dcc_mode"] = self._dcc_mode
            batch["current_host"] = self._current_host
            batch["theme"] = "dark"
            batch["integration_mode"] = self._integration_mode

        @state.on_change
        def handle_state_change(key: str, value: Any, old_value: Any):
            logger.debug(f"[State] {key}: {old_value} -> {value}")

        logger.debug("Shared state initialized (batch mode)")

    def _register_commands(self) -> None:
        """Register RPC-style commands callable from JavaScript."""
        if not self._webview:
            return

        @self._webview.command
        def get_app_info() -> dict[str, Any]:
            return {
                "title": self._title,
                "dcc_mode": self._dcc_mode,
                "current_host": self._current_host,
                "version": "1.0.0",
                "integration_mode": self._integration_mode,
            }

        @self._webview.command("set_theme")
        def set_theme(theme: str = "dark") -> dict[str, bool]:
            self._webview.state["theme"] = theme
            logger.info(f"Theme changed to: {theme}")
            return {"success": True}

        logger.debug("Commands registered")

    @property
    def config(self) -> ShelvesConfig:
        """Get the current configuration."""
        return self._config
