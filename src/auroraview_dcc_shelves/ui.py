"""AuroraView-based UI for DCC tool shelves.

This module provides the ShelfApp class for displaying and interacting
with the tool shelf interface.

Architecture:
    For DCC applications (Maya, Houdini, Nuke), uses AuroraView's layered architecture:

    ShelfApp (Application Layer)
        ↓ uses
    QtWebView (Integration Layer) - For DCC apps
    WebView (Abstraction Layer) - For standalone
        ↓ wraps
    AuroraView (Rust Core Layer)

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
from typing import TYPE_CHECKING, Any

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

from auroraview_dcc_shelves.launcher import LaunchError, ToolLauncher
from auroraview_dcc_shelves.settings import WindowSettingsManager

logger = logging.getLogger(__name__)

# Path to the frontend dist directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DIST_DIR = Path(__file__).parent.parent.parent / "dist"

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
"""


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
                        "icon": button.icon,
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


def _get_maya_main_window() -> Any | None:
    """Get Maya main window as QWidget.

    Uses multiple fallback methods:
    1. shiboken6 (Maya 2024+)
    2. shiboken2 (Maya 2022/2023)
    3. QApplication.activeWindow() fallback
    """
    try:
        from qtpy.QtWidgets import QApplication, QWidget
    except ImportError:
        return None

    # Try to get Maya main window via OpenMayaUI + shiboken
    try:
        import maya.OpenMayaUI as omui

        main_window_ptr = omui.MQtUtil.mainWindow()
        if main_window_ptr:
            # Try shiboken6 first (Maya 2024+)
            try:
                from shiboken6 import wrapInstance

                return wrapInstance(int(main_window_ptr), QWidget)
            except ImportError:
                pass
            # Try shiboken2 (Maya 2022/2023)
            try:
                from shiboken2 import wrapInstance

                return wrapInstance(int(main_window_ptr), QWidget)
            except ImportError:
                pass
    except Exception as e:
        logger.warning(f"OpenMayaUI method failed: {e}")

    # Fallback: Find Maya main window from QApplication
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            if widget.objectName() == "MayaWindow":
                return widget

    return None


def _get_houdini_main_window() -> Any | None:
    """Get Houdini main window as QWidget."""
    try:
        from qtpy.QtWidgets import QApplication
    except ImportError:
        return None

    try:
        import hou

        return hou.qt.mainWindow()
    except Exception as e:
        logger.warning(f"hou.qt.mainWindow() failed: {e}")

    # Fallback: Find Houdini main window from QApplication
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            if "Houdini" in widget.windowTitle():
                return widget

    return None


def _get_nuke_main_window() -> Any | None:
    """Get Nuke main window as QWidget.

    Nuke uses a specific DockMainWindow class from Foundry.
    """
    try:
        from qtpy.QtWidgets import QApplication
    except ImportError:
        return None

    # Find Nuke's DockMainWindow
    for obj in QApplication.topLevelWidgets():
        if obj.inherits("QMainWindow") and obj.metaObject().className() == "Foundry::UI::DockMainWindow":
            return obj

    logger.warning("Could not find Nuke MainWindow instance")
    return None


def _get_3dsmax_main_window() -> Any | None:
    """Get 3ds Max main window as QWidget.

    3ds Max uses MaxPlus or pymxs for Qt integration.
    """
    try:
        from qtpy.QtWidgets import QApplication
    except ImportError:
        return None

    # Try MaxPlus first (older 3ds Max versions)
    try:
        import MaxPlus

        return MaxPlus.GetQMaxMainWindow()
    except Exception:
        pass

    # Try pymxs (newer 3ds Max versions)
    try:
        from pymxs import runtime as rt

        # Get main window handle
        main_hwnd = rt.windows.getMAXHWND()
        if main_hwnd:
            # Find QWidget by window handle
            for widget in QApplication.topLevelWidgets():
                if int(widget.winId()) == main_hwnd:
                    return widget
    except Exception:
        pass

    # Fallback: Find 3ds Max main window from QApplication
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            class_name = widget.metaObject().className()
            if "Max" in widget.windowTitle() or "QmaxMainWindow" in class_name:
                return widget

    logger.warning("Could not find 3ds Max MainWindow instance")
    return None


def _get_unreal_main_window() -> Any | None:
    """Get Unreal Engine main window as QWidget.

    Unreal uses Slate UI, but Python integration uses Qt for tool windows.
    """
    try:
        from qtpy.QtWidgets import QApplication
    except ImportError:
        return None

    # Try unreal module
    try:
        import unreal

        # Get the main frame window
        # Note: Unreal's Python API may vary by version
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        pass

    # Fallback: Find Unreal main window from QApplication
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            title = widget.windowTitle()
            class_name = widget.metaObject().className()
            if "Unreal" in title or "UE" in title or "SWindow" in class_name or "FSlateApplication" in class_name:
                return widget

    logger.warning("Could not find Unreal MainWindow instance")
    return None


class ShelfAPI:
    """API object exposed to JavaScript via auroraview.api.*

    This class contains all the methods that can be called from JavaScript
    when using the QtWebView integration mode.

    AuroraView parameter passing rules:
    - If params is a dict: Python receives **params (keyword arguments)
    - If params is a list: Python receives *params (positional arguments)
    - If params is a single value: Python receives params (single argument)
    - Even with no params, AuroraView may pass an empty dict, so methods
      should accept **kwargs or optional params.
    """

    def __init__(self, shelf_app: ShelfApp):
        self._shelf_app = shelf_app

    def get_config(self, _params: Any = None) -> dict[str, Any]:
        """Return the current configuration as JSON.

        AuroraView calls: func(params) when params is None
        So we accept a positional argument that we ignore.

        Returns:
            Configuration dict with shelves and buttons filtered by current host.
        """
        return _config_to_dict(self._shelf_app._config, self._shelf_app._current_host)

    def launch_tool(self, button_id: str = "", **kwargs: Any) -> dict[str, Any]:
        """Launch a tool by its button ID.

        AuroraView calls: func(**params) when params is a dict
        So we accept button_id as a keyword argument.

        Execution varies by tool type:
        - PYTHON: exec() in DCC mode, subprocess in standalone
        - EXECUTABLE: subprocess.Popen
        - MEL: maya.mel.eval() (Maya only)
        - JAVASCRIPT: Returns script for frontend eval()

        Args:
            button_id: The ID of the button/tool to launch.
            **kwargs: Additional params (ignored).

        Returns:
            Result dict with success, message, buttonId.
            For JavaScript tools, also includes 'javascript' key with script.
        """
        if not button_id:
            return {
                "success": False,
                "message": "No button_id provided",
                "buttonId": "",
            }

        try:
            result = self._shelf_app._launcher.launch_by_id(button_id)

            # Handle JavaScript - return script for frontend to eval()
            if isinstance(result, dict) and result.get("type") == "javascript":
                return {
                    "success": True,
                    "message": f"JavaScript tool ready: {button_id}",
                    "buttonId": button_id,
                    "javascript": result.get("script", ""),
                }

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

    def get_tool_path(self, button_id: str = "", **kwargs: Any) -> dict[str, Any]:
        """Get the resolved path for a tool.

        AuroraView calls: func(**params) when params is a dict
        So we accept button_id as a keyword argument.

        Args:
            button_id: The ID of the button/tool.
            **kwargs: Additional params (ignored).

        Returns:
            Dict with buttonId and resolved path.
        """
        path = ""
        for shelf in self._shelf_app._config.shelves:
            for button in shelf.buttons:
                if button.id == button_id:
                    path = str(self._shelf_app._launcher.resolve_path(button.tool_path))
                    break
        return {"buttonId": button_id, "path": path}


class ShelfApp:
    """AuroraView-based application for displaying tool shelves.

    This class creates a WebView window displaying the shelf UI and
    handles communication between the frontend and Python backend.

    For DCC applications (Maya, Houdini, Nuke), uses QtWebView with
    automatic event processing. For standalone mode, uses regular WebView.

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
        remember_size: bool = True,
    ) -> None:
        self._config = config
        self._title = title
        self._default_width = width
        self._default_height = height
        self._remember_size = remember_size
        # Launcher will be created with dcc_mode in show()
        self._launcher: ToolLauncher | None = None
        self._webview: Any = None  # WebView or QtWebView
        self._dialog: Any = None  # QDialog for DCC mode
        self._auroraview: Any = None  # AuroraView wrapper for DCC mode
        self._api: ShelfAPI | None = None
        self._dcc_mode = False
        self._current_host = ""  # Current DCC host name for filtering tools
        self._settings_manager: WindowSettingsManager | None = None

    def _is_dev_mode(self) -> bool:
        """Check if running in development mode (no dist build)."""
        dist_index = DIST_DIR / "index.html"
        return not dist_index.exists()

    def _register_api(self, webview: WebView) -> None:
        """Register Python API methods for the frontend (standalone mode)."""

        @webview.on("get_config")
        def handle_get_config(data: dict[str, Any]) -> None:
            """Return the current configuration as JSON."""
            config_dict = _config_to_dict(self._config)
            webview.emit("config_response", config_dict)

        @webview.on("launch_tool")
        def handle_launch_tool(data: dict[str, Any]) -> None:
            """Launch a tool by its button ID."""
            button_id = data.get("buttonId", "")
            try:
                self._launcher.launch_by_id(button_id)
                webview.emit(
                    "launch_result",
                    {
                        "success": True,
                        "message": f"Tool launched: {button_id}",
                        "buttonId": button_id,
                    },
                )
            except LaunchError as e:
                logger.error(f"Failed to launch tool {button_id}: {e}")
                webview.emit(
                    "launch_result",
                    {
                        "success": False,
                        "message": str(e),
                        "buttonId": button_id,
                    },
                )

        @webview.on("get_tool_path")
        def handle_get_tool_path(data: dict[str, Any]) -> None:
            """Get the resolved path for a tool."""
            button_id = data.get("buttonId", "")
            path = ""
            for shelf in self._config.shelves:
                for button in shelf.buttons:
                    if button.id == button_id:
                        path = str(self._launcher.resolve_path(button.tool_path))
                        break
            webview.emit("tool_path_response", {"buttonId": button_id, "path": path})

    def _show_dcc_mode(self, debug: bool, app: str) -> None:
        """Show using QtWebView for DCC integration (non-blocking).

        This uses AuroraView's layered architecture with automatic event processing.
        Supports Maya, Houdini, and Nuke.
        """
        if not QT_AVAILABLE:
            raise RuntimeError(
                "Qt integration not available. Install auroraview with Qt support: pip install auroraview[qt]"
            )

        # Get DCC main window based on app type
        app_lower = app.lower()

        if app_lower == "maya":
            parent_window = _get_maya_main_window()
        elif app_lower == "houdini":
            parent_window = _get_houdini_main_window()
        elif app_lower == "nuke":
            parent_window = _get_nuke_main_window()
        elif app_lower == "3dsmax" or app_lower == "max":
            parent_window = _get_3dsmax_main_window()
        elif app_lower == "unreal":
            parent_window = _get_unreal_main_window()
        else:
            # Unknown DCC, try to get active window
            from qtpy.QtWidgets import QApplication

            qt_app = QApplication.instance()
            parent_window = qt_app.activeWindow() if qt_app else None

        if parent_window is None:
            raise RuntimeError(
                f"Could not get {app} main window. Please ensure {app} UI is fully loaded before launching."
            )

        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QDialog, QVBoxLayout

        # Initialize settings manager for window size persistence
        self._settings_manager = WindowSettingsManager(app_lower)

        # Load saved window settings or use defaults
        if self._remember_size:
            settings = self._settings_manager.load()
            self._width = settings.width if settings.width > 0 else self._default_width
            self._height = settings.height if settings.height > 0 else self._default_height
        else:
            self._width = self._default_width
            self._height = self._default_height

        # Create QDialog container with flat Apple-style
        self._dialog = QDialog(parent_window)
        self._dialog.setWindowTitle(self._title)
        self._dialog.setSizeGripEnabled(True)

        # Apply flat style - dark background prevents white flash
        self._dialog.setStyleSheet(FLAT_STYLE_QSS)

        # Set window flags for better integration
        self._dialog.setWindowFlags(
            Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
        )

        # Apply saved or default window size
        self._dialog.resize(self._width, self._height)
        self._dialog.setMinimumSize(400, 300)  # Minimum reasonable size

        # Connect close event to save window size
        if self._remember_size:
            original_close = self._dialog.closeEvent

            def save_on_close(event):
                self._settings_manager.save_from_dialog(self._dialog)
                original_close(event)

            self._dialog.closeEvent = save_on_close

        # Create QtWebView - for Nuke, don't use layout, set geometry directly
        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        # Create QtWebView (AuroraView's WebView2-based Qt widget)
        # Use QVBoxLayout for all DCCs including Nuke
        layout = QVBoxLayout(self._dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._webview = QtWebView(
            self._dialog,
            dev_tools=debug,
            context_menu=False,
            asset_root=dist_dir,
        )

        # Set size policy to ensure WebView2 fills the available space
        from qtpy.QtWidgets import QSizePolicy

        self._webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._webview.setMinimumSize(self._width, self._height)

        layout.addWidget(self._webview)

        # Create API and bind to AuroraView
        self._api = ShelfAPI(self)
        self._auroraview = AuroraView(
            parent=self._dialog,
            api=self._api,
            _view=self._webview,
            _keep_alive_root=self._dialog,
        )

        # Load content
        if self._is_dev_mode():
            dev_url = "http://localhost:5173"
            logger.info(f"DCC mode - Loading dev URL: {dev_url}")
            self._webview.load_url(dev_url)
        else:
            index_path = DIST_DIR / "index.html"
            if index_path.exists():
                logger.info(f"DCC mode - Loading file: {index_path}")
                self._webview.load_file(str(index_path.resolve()))
            else:
                raise FileNotFoundError(f"index.html not found at {index_path}")

        # Show dialog first, then webview
        self._dialog.show()
        self._webview.show()

        # Force geometry update after show - fixes Nuke rendering issues
        # Nuke's Qt environment has issues with WebView2 sizing
        if app_lower == "nuke":
            from qtpy.QtCore import QTimer
            from qtpy.QtWidgets import QApplication

            def force_nuke_geometry():
                """Force WebView geometry in Nuke.

                Nuke has issues with WebView2 sizing. Force the dialog
                and WebView to maintain correct dimensions.
                """
                # Update dialog geometry
                self._dialog.setMinimumSize(self._width, self._height)
                self._dialog.resize(self._width, self._height)

                # Update WebView minimum size
                self._webview.setMinimumSize(self._width, self._height)

                # Force layout update
                self._dialog.updateGeometry()
                self._webview.updateGeometry()

                QApplication.processEvents()
                logger.debug(f"Nuke: Forced geometry {self._width}x{self._height}")

            # Schedule geometry updates at different times
            QTimer.singleShot(100, force_nuke_geometry)
            QTimer.singleShot(500, force_nuke_geometry)
            QTimer.singleShot(1000, force_nuke_geometry)
            QTimer.singleShot(2000, force_nuke_geometry)

        logger.info("DCC mode - ShelfApp started successfully")

    def _show_standalone_mode(self, debug: bool) -> None:
        """Show using regular WebView for standalone mode (blocking)."""
        # Initialize settings manager for standalone mode
        self._settings_manager = WindowSettingsManager("standalone")

        # Load saved window settings or use defaults
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
        self._webview.show()

    def show(self, debug: bool = False, app: str | None = None) -> None:
        """Show the shelf window.

        For DCC applications (Maya, Houdini, Nuke), pass the `app` parameter to
        enable embedded mode which prevents UI blocking.

        Args:
            debug: Enable debug mode with developer tools (F12 or right-click).
            app: DCC application name for parent integration (e.g., "maya", "houdini", "nuke").
                 If provided, will use QtWebView with non-blocking event loop.
        """
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Asset root: {DIST_DIR}")
        logger.info(f"DCC app: {app}")

        # Store current host for tool filtering
        self._current_host = app.lower() if app else ""
        logger.info(f"Current host: {self._current_host}")

        # Determine DCC mode
        self._dcc_mode = bool(app and QT_AVAILABLE)

        # Create launcher with appropriate mode
        # DCC mode: scripts are executed inline using exec()
        # Standalone mode: scripts are launched as subprocesses
        self._launcher = ToolLauncher(self._config, dcc_mode=self._dcc_mode)
        logger.info(f"Launcher created with dcc_mode={self._dcc_mode}")

        if self._dcc_mode:
            # DCC mode: Use QtWebView for non-blocking integration
            self._show_dcc_mode(debug, app)
        else:
            if app and not QT_AVAILABLE:
                logger.warning(
                    f"Qt integration requested for {app} but not available. "
                    "Using standalone mode. Install with: pip install auroraview[qt]"
                )
            # Standalone mode: Use regular WebView
            self._show_standalone_mode(debug)

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
