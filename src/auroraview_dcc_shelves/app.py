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

New API Features (AuroraView 0.x.x):
    - load_progress: Monitor page loading progress (0-100)
    - on_navigation_started/completed/failed: Navigation lifecycle events
    - is_loading: Check if page is currently loading
    - stop: Stop current page loading
    - eval_js_async: Async JavaScript execution with callbacks
    - Qt Signals: urlChanged, loadFinished, titleChanged, loadProgress
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

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
    from auroraview_dcc_shelves.config import ShelvesConfig

from auroraview_dcc_shelves.apps import DCCAdapter, get_adapter
from auroraview_dcc_shelves.constants import (
    MAIN_WINDOW_CONFIG,
    SETTINGS_WINDOW_CONFIG,
    IntegrationMode,
)
from auroraview_dcc_shelves.launcher import LaunchError, ToolLauncher
from auroraview_dcc_shelves.managers import WebViewManager, WindowManager
from auroraview_dcc_shelves.styles import FLAT_STYLE_QSS
from auroraview_dcc_shelves.ui.api import ShelfAPI, _config_to_dict

logger = logging.getLogger(__name__)

# Path to the frontend dist directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DIST_DIR = Path(__file__).parent.parent.parent / "dist"


# Note: DCC-specific main window functions have been moved to apps/ adapters
# See: apps/maya.py, apps/houdini.py, apps/nuke.py, apps/max3ds.py, apps/unreal.py

# Note: ShelfAPI class and _config_to_dict have been moved to ui/api.py for better modularity


class ShelfApp:
    """AuroraView-based application for displaying tool shelves.

    This class creates a WebView window displaying the shelf UI and
    handles communication between the frontend and Python backend.

    Integration Modes:
        - "qt": Uses QtWebView for Qt widget integration (recommended).
                Supports QDockWidget docking and automatic resize.
                Uses createWindowContainer for native Qt layout integration.
        - "hwnd": Uses AuroraView with HWND for non-Qt integration.
                Best for Unreal Engine or when Qt integration causes issues.

    Args:
        config: The shelves configuration to display.
        title: Window title. Defaults to "DCC Shelves".
        width: Window width in pixels. Defaults to 800.
        height: Window height in pixels. Defaults to 600.

    Example (Qt mode - recommended)::

        from auroraview_dcc_shelves import ShelfApp, load_config

        config = load_config("shelf_config.yaml")
        app = ShelfApp(config)
        app.show(app="maya", mode="qt")

    Example (Qt mode - dockable panel)::

        from auroraview_dcc_shelves import ShelfApp, load_config

        config = load_config("shelf_config.yaml")
        app = ShelfApp(config)
        app.show(app="maya", mode="qt", dockable=True)

    Example (HWND mode - for Unreal Engine)::

        from auroraview_dcc_shelves import ShelfApp, load_config

        config = load_config("shelf_config.yaml")
        app = ShelfApp(config)
        app.show(app="maya", mode="hwnd")

        # Get HWND for Unreal integration
        hwnd = app.get_hwnd()
        if hwnd:
            import unreal
            unreal.parent_external_window_to_slate(hwnd)
    """

    def __init__(
        self,
        config: ShelvesConfig,
        title: str = "DCC Shelves",
        width: int = 0,
        height: int = 0,
        frameless: bool = False,
    ) -> None:
        self._config = config
        self._title = title
        # Use MAIN_WINDOW_CONFIG defaults if not specified
        self._default_width = width if width > 0 else MAIN_WINDOW_CONFIG["default_width"]
        self._default_height = height if height > 0 else MAIN_WINDOW_CONFIG["default_height"]
        # Window size is now fixed - no longer remembered
        self._width = self._default_width
        self._height = self._default_height
        self._frameless = frameless  # Whether to use frameless window (HTML provides title bar)
        self._launcher: ToolLauncher | None = None
        self._webview: Any = None  # WebView or QtWebView
        self._dialog: Any = None  # QDialog for Qt mode
        self._auroraview: Any = None  # AuroraView wrapper
        self._api: ShelfAPI | None = None
        # Whether we are running inside a DCC host (Qt-based environment)
        # This replaces the old _dcc_mode name for clarity, but the exposed
        # state key remains "dcc_mode" for backward compatibility.
        self._is_dcc_environment = False
        self._current_host = ""
        self._integration_mode: IntegrationMode = "qt"  # Default to Qt mode
        self._child_windows: dict[str, Any] = {}  # Child windows by label
        self._adapter: DCCAdapter | None = None  # DCC adapter instance
        self._dockable = False  # Whether to use dockable mode
        self._dockable_container: Any = None  # Container widget for dockable mode

        # Initialize managers for modular architecture
        self._window_manager = WindowManager()
        self._webview_manager = WebViewManager(dist_dir=DIST_DIR)

        # State tracking for cleanup
        self._placeholder: Any = None
        self._layout: Any = None

    def _cleanup_previous_session(self) -> None:
        """Clean up resources from a previous show() call.

        This is called at the start of show() to ensure a clean state
        when re-opening the window. Prevents delays caused by leftover
        WebView instances or dialog resources.
        """
        logger.debug("Cleaning up previous session...")

        # Clean up WebView
        if self._webview is not None:
            try:
                if hasattr(self._webview, "close"):
                    self._webview.close()
                logger.debug("Closed previous WebView")
            except Exception as e:
                logger.debug(f"WebView cleanup failed: {e}")
            self._webview = None

        # Clean up AuroraView wrapper
        if self._auroraview is not None:
            try:
                if hasattr(self._auroraview, "close"):
                    self._auroraview.close()
                logger.debug("Closed previous AuroraView wrapper")
            except Exception as e:
                logger.debug(f"AuroraView cleanup failed: {e}")
            self._auroraview = None

        # Clean up Dialog
        if self._dialog is not None:
            try:
                if hasattr(self._dialog, "close"):
                    self._dialog.close()
                if hasattr(self._dialog, "deleteLater"):
                    self._dialog.deleteLater()
                logger.debug("Closed previous Dialog")
            except Exception as e:
                logger.debug(f"Dialog cleanup failed: {e}")
            self._dialog = None

        # Clean up placeholder
        if self._placeholder is not None:
            try:
                if hasattr(self._placeholder, "deleteLater"):
                    self._placeholder.deleteLater()
            except Exception as e:
                logger.debug(f"Placeholder cleanup failed: {e}")
            self._placeholder = None

        # Clean up dockable container
        if self._dockable_container is not None:
            try:
                if hasattr(self._dockable_container, "close"):
                    self._dockable_container.close()
            except Exception as e:
                logger.debug(f"Dockable container cleanup failed: {e}")
            self._dockable_container = None

        # Reset API
        self._api = None
        self._layout = None

        # Reset WebViewManager state
        self._webview_manager.cleanup()

        logger.debug("Previous session cleanup complete")

    # =========================================================================
    # JavaScript Execution API
    # =========================================================================

    def eval_js(self, script: str) -> bool:
        """Execute JavaScript in the WebView (thread-safe).

        This method automatically uses WebViewProxy when in HWND mode,
        allowing safe cross-thread JavaScript execution.

        Args:
            script: JavaScript code to execute.

        Returns:
            True if the script was queued/executed successfully.

        Example:
            >>> app.eval_js("console.log('Hello!')")
            >>> app.eval_js("document.title = 'Updated'")
        """
        # Try thread-safe proxy first (for HWND mode)
        if hasattr(self, "_webview_proxy") and self._webview_proxy is not None:
            try:
                self._webview_proxy.eval_js(script)
                return True
            except Exception as e:
                logger.warning(f"WebViewProxy eval_js failed: {e}, trying direct call")

        # Fall back to direct WebView call (for Qt mode or same-thread access)
        if self._webview is None:
            logger.warning("WebView not initialized")
            return False

        try:
            if hasattr(self._webview, "eval_js"):
                self._webview.eval_js(script)
                return True
        except Exception as e:
            logger.error(f"eval_js failed: {e}")
            return False

        return False

    def eval_js_async(
        self,
        script: str,
        callback: Callable[[str | None, Exception | None], None] | None = None,
        timeout_ms: int = 5000,
    ) -> None:
        """Execute JavaScript asynchronously with a callback.

        Args:
            script: JavaScript code to execute.
            callback: Function to call with (result, error) when execution completes.
            timeout_ms: Timeout in milliseconds (default: 5000).

        Example:
            >>> def on_result(result, error):
            ...     if error:
            ...         print(f"Error: {error}")
            ...     else:
            ...         print(f"Result: {result}")
            >>> app.eval_js_async("document.title", on_result)
        """
        if self._webview is None:
            if callback:
                callback(None, RuntimeError("WebView not initialized"))
            return

        # Try thread-safe proxy first (for HWND mode)
        if hasattr(self, "_webview_proxy") and self._webview_proxy is not None:
            try:
                self._webview_proxy.eval_js(script)
                if callback:
                    # Note: Proxy doesn't support result capture yet
                    callback(None, None)
                return
            except Exception as e:
                logger.warning(f"WebViewProxy eval_js failed: {e}, trying direct call")

        if hasattr(self._webview, "eval_js_async"):
            self._webview.eval_js_async(script, callback, timeout_ms)
        elif hasattr(self._webview, "eval_js"):
            # Fallback to sync eval_js
            try:
                result = self._webview.eval_js(script)
                if callback:
                    callback(result, None)
            except Exception as e:
                if callback:
                    callback(None, e)
        else:
            if callback:
                callback(None, RuntimeError("WebView does not support JavaScript execution"))

    # =========================================================================
    # Zoom API
    # =========================================================================

    def set_zoom(self, scale_factor: float) -> bool:
        """Set the zoom level of the WebView content.

        Note: Frontend handles zoom via CSS (useZoom.ts). This method is for
        programmatic control from Python if needed.

        Args:
            scale_factor: Zoom scale factor (1.0 = 100%, 1.5 = 150%).

        Returns:
            True if zoom was set successfully.
        """
        if self._webview is None:
            return False

        try:
            if hasattr(self._webview, "set_zoom"):
                self._webview.set_zoom(scale_factor)
            else:
                # Fallback: CSS zoom
                self._webview.eval_js(f"document.body.style.zoom = '{scale_factor}';")
            logger.debug(f"Zoom set to {scale_factor * 100:.0f}%")
            return True
        except Exception as e:
            logger.error(f"Failed to set zoom: {e}")
            return False

    def _is_dev_mode(self) -> bool:
        """Check if running in development mode (no dist build).

        Result is cached after first call for performance.
        """
        if not hasattr(self, "_dev_mode_cached"):
            dist_index = DIST_DIR / "index.html"
            self._dev_mode_cached = not dist_index.exists()
        return self._dev_mode_cached

    def _get_dcc_parent_window(self, app: str) -> Any:
        """Get the DCC main window based on app type.

        Uses the DCC adapter system to get the appropriate parent window.
        """
        adapter = get_adapter(app)
        parent_window = adapter.get_main_window()

        if parent_window is None:
            raise RuntimeError(f"Could not get {app} main window. Please ensure {app} UI is fully loaded.")
        return parent_window

    def _register_api(self, webview: WebView) -> None:
        """Register Python API methods for the frontend (standalone mode)."""
        self._register_event_handlers(webview)

    def _register_event_handlers(self, view: Any) -> None:
        """Register event handlers for frontend communication.

        This supports the event mode fallback when API mode is not available.
        Used by both standalone mode (WebView) and Qt mode (AuroraView).

        Args:
            view: WebView or AuroraView instance that supports .on() and .emit()
        """
        if not hasattr(view, "on") or not hasattr(view, "emit"):
            logger.warning("View does not support event handlers")
            return

        @view.on("get_config")
        def handle_get_config(data: dict[str, Any]) -> None:
            config_dict = _config_to_dict(self._config, self._current_host)
            view.emit("config_response", config_dict)

        @view.on("launch_tool")
        def handle_launch_tool(data: dict[str, Any]) -> None:
            button_id = data.get("buttonId", "")
            try:
                self._launcher.launch_by_id(button_id)
                view.emit(
                    "launch_result", {"success": True, "message": f"Tool launched: {button_id}", "buttonId": button_id}
                )
            except LaunchError as e:
                logger.error(f"Failed to launch tool {button_id}: {e}")
                view.emit("launch_result", {"success": False, "message": str(e), "buttonId": button_id})

        @view.on("get_tool_path")
        def handle_get_tool_path(data: dict[str, Any]) -> None:
            button_id = data.get("buttonId", "")
            path = ""
            for shelf in self._config.shelves:
                for button in shelf.buttons:
                    if button.id == button_id:
                        path = str(self._launcher.resolve_path(button.tool_path))
                        break
            view.emit("tool_path_response", {"buttonId": button_id, "path": path})

        logger.debug("Event handlers registered for event mode fallback")

    def _show_qt_mode(self, debug: bool, app: str) -> None:
        """Show using QtWebView for Qt-native integration (non-blocking).

        This mode creates a true Qt widget that can be docked, embedded in
        layouts, and managed by Qt's parent-child system.

        Best for: Maya, Houdini, Nuke, 3ds Max

        Uses WindowManager for dialog creation and configuration.
        """
        if not QT_AVAILABLE:
            raise RuntimeError("Qt integration not available. Install with: pip install auroraview[qt]")

        app_lower = app.lower()
        parent_window = self._get_dcc_parent_window(app)

        from qtpy.QtCore import QTimer

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        # Use WindowManager to create and configure dialog
        # start_hidden=True prevents the "white flash" issue by keeping dialog
        # invisible until WebView is fully initialized
        self._dialog = self._window_manager.create_qt_dialog(
            parent=parent_window,
            title=self._title,
            width=self._width,
            height=self._height,
            min_width=MAIN_WINDOW_CONFIG["min_width"],
            min_height=MAIN_WINDOW_CONFIG["min_height"],
            max_width=MAIN_WINDOW_CONFIG["max_width"],
            max_height=MAIN_WINDOW_CONFIG["max_height"],
            frameless=self._frameless,
            style_sheet=FLAT_STYLE_QSS,
            start_hidden=True,  # Prevent white flash
        )
        self._layout = self._window_manager.layout

        logger.info("Qt mode - Dialog created (hidden), initializing WebView...")

        self._init_params = {"debug": debug, "app_lower": app_lower}

        # Use adapter-specific delay for WebView initialization via hook
        init_delay = 10  # Default delay
        if self._adapter:
            init_delay = self._adapter.get_init_delay_ms()
            logger.info(f"{self._adapter.name}: init_delay={init_delay}ms")

        QTimer.singleShot(init_delay, self._init_webview_deferred_qt)

    def _show_dockable_mode(self, debug: bool, app: str) -> None:
        """Show as a dockable panel in the DCC application.

        This mode creates a native dockable panel that can be docked
        into the DCC's panel system (Maya workspaceControl, Nuke panels,
        Houdini Python Panels).

        Best for: Maya, Houdini, Nuke when native docking is desired.

        Uses WindowManager for container creation and docking.
        """
        if not QT_AVAILABLE:
            raise RuntimeError("Qt integration not available. Install with: pip install auroraview[qt]")

        if not self._adapter or not self._adapter.supports_dockable():
            logger.warning(f"Dockable mode not supported for {app}. Falling back to Qt mode.")
            return self._show_qt_mode(debug, app)

        app_lower = app.lower()

        from qtpy.QtCore import QTimer

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        # Use WindowManager to create dockable container
        self._dockable_container = self._window_manager.create_dockable_container(
            app_name=app_lower,
            width=self._width,
            height=self._height,
            min_width=MAIN_WINDOW_CONFIG["min_width"],
            min_height=MAIN_WINDOW_CONFIG["min_height"],
        )
        self._layout = self._window_manager.layout

        # Store params for deferred initialization
        self._init_params = {"debug": debug, "app_lower": app_lower}

        # Use WindowManager to show dockable panel
        object_name = f"auroraview_shelf_{app_lower}"
        success = self._window_manager.show_dockable(
            title=self._title,
            object_name=object_name,
        )

        if success:
            logger.info(f"Dockable mode - Panel created for {app}")
            # Defer WebView initialization
            init_delay = self._adapter.get_init_delay_ms()
            QTimer.singleShot(init_delay, self._init_webview_deferred_dockable)
        else:
            logger.warning(f"Failed to create dockable panel for {app}. Falling back to Qt mode.")
            # Cleanup and fallback
            self._dockable_container.deleteLater()
            self._dockable_container = None
            return self._show_qt_mode(debug, app)

    def _init_webview_deferred_dockable(self) -> None:
        """Initialize WebView in dockable mode (deferred).

        Uses WebViewManager for WebView creation.
        """
        debug = self._init_params["debug"]

        # Get container size from WindowManager
        content_width, content_height = self._window_manager.get_content_rect()
        webview_width = content_width if content_width > 0 else self._width
        webview_height = content_height if content_height > 0 else self._height

        logger.info(f"Dockable mode - Creating WebView: {webview_width}x{webview_height}")

        # Use WebViewManager to create WebView
        self._placeholder = self._webview_manager.create_qt_webview_deferred(
            parent=self._dockable_container,
            width=webview_width,
            height=webview_height,
            debug=debug,
            on_ready=self._on_webview_ready_dockable,
            on_error=self._on_webview_error,
        )
        self._window_manager.add_widget_to_layout(self._placeholder)

    def _on_webview_ready_dockable(self, webview: Any) -> None:
        """Called when QtWebView is ready in dockable mode."""
        self._complete_webview_initialization(
            webview=webview,
            mode="dockable",
            parent_widget=self._dockable_container,
        )

    def _init_webview_deferred_qt(self) -> None:
        """Initialize WebView in Qt mode (deferred).

        Uses WindowManager for dialog adjustments and WebViewManager for WebView creation.
        """
        debug = self._init_params["debug"]

        # Get content rect for WebView sizing
        webview_width = self._width
        webview_height = self._height
        logger.info(f"Qt mode - Creating WebView: {webview_width}x{webview_height}")

        try:
            # Use WebViewManager to create WebView
            self._placeholder = self._webview_manager.create_qt_webview_deferred(
                parent=self._dialog,
                width=webview_width,
                height=webview_height,
                debug=debug,
                on_ready=self._on_webview_ready_qt,
                on_error=self._on_webview_error,
            )
            self._window_manager.add_widget_to_layout(self._placeholder)
            logger.info("Qt mode - WebView creation started (deferred)")
        except Exception as e:
            logger.error(f"Failed to create QtWebView: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _on_webview_ready_qt(self, webview: Any) -> None:
        """Called when QtWebView is ready."""
        self._complete_webview_initialization(
            webview=webview,
            mode="qt",
            parent_widget=self._dialog,
        )

    def _complete_webview_initialization(
        self,
        webview: Any,
        mode: str,
        parent_widget: Any,
    ) -> None:
        """Complete WebView initialization for Qt-based modes.

        This is the unified initialization path for both Qt mode and Dockable mode.
        Extracts common logic to reduce code duplication.

        Anti-Flicker Strategy:
            1. WebView is created but dialog remains hidden
            2. Load content into WebView
            3. Wait for loadFinished or a short timeout
            4. Show dialog only after content is ready

        Args:
            webview: The QtWebView instance that was created.
            mode: Integration mode ("qt" or "dockable").
            parent_widget: The parent widget (dialog or dockable container).
        """
        from qtpy.QtCore import QTimer
        from qtpy.QtWidgets import QApplication

        logger.info(f"{mode.capitalize()} mode - WebView ready, completing initialization...")

        # Step 1: Setup WebView via manager (hidden initially to prevent white flash)
        # Pass parent_widget for SetParent call to prevent WebView from being dragged independently
        self._webview_manager.setup_webview(
            webview=webview,
            min_width=MAIN_WINDOW_CONFIG["min_width"],
            min_height=MAIN_WINDOW_CONFIG["min_height"],
            start_hidden=True,  # Hide until content loads
            parent_widget=parent_widget,  # For SetParent call
        )
        self._webview = self._webview_manager.webview

        # Step 2: Replace placeholder with WebView (but keep dialog hidden)
        if self._placeholder:
            self._placeholder.hide()
            self._window_manager.remove_widget_from_layout(self._placeholder)
            self._webview_manager.cleanup_placeholder()
            self._placeholder = None

        # Step 3: Add WebView to layout (mode-specific)
        if mode == "qt":
            if self._layout:
                self._layout.addWidget(self._webview, 1)
        else:
            self._window_manager.add_widget_to_layout(self._webview)

        # Step 4: Force layout update (critical for Qt6/PySide6)
        if mode == "qt":
            if self._layout:
                self._layout.activate()
                self._layout.update()
            if self._dialog:
                self._dialog.updateGeometry()
            self._webview.updateGeometry()
            if hasattr(self._webview, "_force_container_geometry"):
                self._webview._force_container_geometry()
            QApplication.processEvents()

        # Step 5: Create API and AuroraView wrapper
        self._api = ShelfAPI(self)
        self._auroraview = self._webview_manager.create_auroraview_wrapper(
            parent=parent_widget,
            api=self._api,
            keep_alive_root=parent_widget,
        )

        # Step 6: Register event handlers and signals
        self._register_event_handlers(self._auroraview)
        self._connect_qt_signals()

        # Step 7: Setup state and commands (before content load)
        self._register_window_events()
        self._setup_shared_state()
        self._register_commands()

        # Step 8: Track whether dialog has been shown (for deferred show)
        self._dialog_shown = False

        def _show_dialog_once() -> None:
            """Show dialog only once, after content is ready."""
            if self._dialog_shown:
                return
            self._dialog_shown = True

            logger.info(f"{mode.capitalize()} mode - Content ready, showing dialog...")

            # Show WebView first
            self._webview_manager.show()

            if mode == "qt" and self._dialog:
                # Use smooth fade-in effect to reduce visual jarring
                self._show_dialog_with_fade(self._dialog)
                logger.info("Qt mode - Dialog shown with WebView")

            # Schedule geometry fixes after show
            if mode == "qt":
                self._schedule_geometry_fixes()

            # Call adapter's on_show hook
            if self._adapter:
                self._adapter.on_show(self)

            logger.info(f"{mode.capitalize()} mode - WebView initialization complete!")

        # Step 9: Connect to first_paint event for optimal show timing
        # first_paint is emitted by frontend after React has rendered the first frame
        # This provides the best user experience as content is guaranteed to be visible
        first_paint_connected = False
        if hasattr(self._webview, "on"):
            try:

                @self._webview.on("first_paint")
                def _on_first_paint(data: dict[str, Any]) -> None:
                    """Handle first_paint event from frontend."""
                    paint_time = data.get("time", 0) if data else 0
                    logger.info(f"First paint received: {paint_time:.2f}ms")
                    _show_dialog_once()

                first_paint_connected = True
                logger.debug("Connected first_paint event handler")
            except Exception as e:
                logger.debug(f"Failed to connect first_paint event: {e}")

        # Step 10.5: Fallback to loadFinished if first_paint is not available
        if hasattr(self._webview, "loadFinished"):

            def _on_first_load_finished(success: bool) -> None:
                """Handle first loadFinished to show dialog (fallback)."""
                # Disconnect to avoid repeated calls
                try:
                    self._webview.loadFinished.disconnect(_on_first_load_finished)
                except Exception:
                    pass

                if success:
                    # If first_paint is connected, give it a chance to fire first
                    # Otherwise, show after a small delay for first paint
                    delay = 100 if first_paint_connected else 50
                    QTimer.singleShot(delay, _show_dialog_once)
                else:
                    # Show anyway on failure
                    _show_dialog_once()

            self._webview.loadFinished.connect(_on_first_load_finished)

        # Step 11: Load content (this triggers the async load)
        self._load_content()

        # Step 12: Fallback timer in case neither first_paint nor loadFinished fires
        # This ensures dialog is shown even if something goes wrong
        fallback_delay = 2000  # 2000ms fallback
        if self._adapter:
            # Use adapter's init delay as a hint for fallback
            fallback_delay = max(2000, self._adapter.get_init_delay_ms() * 20)

        QTimer.singleShot(fallback_delay, _show_dialog_once)

        # Step 13: Schedule repeated WebView2 child window fixes for Qt6 compatibility
        # WebView2 creates child windows asynchronously, so we need multiple attempts
        self._schedule_webview2_child_fixes()

    def _connect_qt_signals(self) -> None:
        """Connect Qt signals and AuroraView events for navigation.

        This integrates AuroraView's event system with ShelfApp's
        navigation callback system. QtWebView uses AuroraView events,
        not Qt signals for WebView communication.
        """
        if self._webview is None:
            return

        # Connect Qt signals if available (QWebEngineView compatibility)
        if hasattr(self._webview, "loadStarted"):
            self._webview.loadStarted.connect(self._on_qt_load_started)
            logger.debug("Connected Qt loadStarted signal")

        if hasattr(self._webview, "loadFinished"):
            self._webview.loadFinished.connect(self._on_qt_load_finished)
            logger.debug("Connected Qt loadFinished signal")

        if hasattr(self._webview, "loadProgress"):
            self._webview.loadProgress.connect(self._on_qt_load_progress)
            logger.debug("Connected Qt loadProgress signal")

        if hasattr(self._webview, "urlChanged"):
            self._webview.urlChanged.connect(self._on_qt_url_changed)
            logger.debug("Connected Qt urlChanged signal")

        if hasattr(self._webview, "titleChanged"):
            self._webview.titleChanged.connect(self._on_qt_title_changed)
            logger.debug("Connected Qt titleChanged signal")

        # Connect AuroraView events for page lifecycle (QtWebView uses these)
        if hasattr(self._webview, "on"):

            @self._webview.on("__auroraview_page_loaded")
            def _handle_page_loaded(data: dict[str, Any]) -> None:
                logger.info("AuroraView page loaded event received")
                self._on_qt_load_finished(True)

            @self._webview.on("__auroraview_ready")
            def _handle_ready(data: dict[str, Any]) -> None:
                logger.info("AuroraView ready event received")
                # Re-register API when AuroraView bridge is ready
                self._register_api_after_load()

            logger.debug("Connected AuroraView lifecycle events")

    def _on_qt_load_started(self) -> None:
        """Handle Qt loadStarted signal."""
        self._is_loading = True
        self._load_progress = 0
        logger.debug("Qt loadStarted - navigation starting")
        self._emit_navigation_event("navigation_started", self._current_url)
        # Notify frontend about loading state
        self._notify_frontend_loading_state(True, 0)

    def _on_qt_load_finished(self, success: bool) -> None:
        """Handle Qt loadFinished signal."""
        self._is_loading = False
        self._load_progress = 100 if success else 0
        logger.info(f"Qt loadFinished - success={success}")
        if success:
            self._emit_navigation_event("navigation_completed", self._current_url, True)
            # Register API methods after page load (event-driven)
            self._register_api_after_load()
        else:
            self._emit_navigation_event("navigation_failed", self._current_url, "Load failed")
        # Notify frontend about loading state
        self._notify_frontend_loading_state(False, 100 if success else 0)

    def _register_api_after_load(self) -> None:
        """Register API methods after page load.

        Called by loadFinished signal. bind_api() is idempotent, so multiple
        calls are safe and will be silently skipped after the first binding.
        """
        if self._api is None:
            return

        logger.info("[_register_api_after_load] Starting API registration")

        webview = self._get_webview(for_js_eval=False)
        if webview is None:
            logger.warning("[_register_api_after_load] No webview available")
            return

        # Set loaded state for the webview
        if hasattr(webview, "_set_loaded"):
            webview._set_loaded(True)
            logger.debug("Set webview loaded state to True")

        # Bind API to WebView
        # bind_api() is idempotent - subsequent calls are silently skipped
        # after the first successful binding for a given namespace.
        if hasattr(webview, "bind_api"):
            webview.bind_api(self._api)
            logger.info("API bound successfully")

        # Notify frontend that API is ready
        self._notify_api_ready()
        logger.info("[_register_api_after_load] API registration complete")

    def _get_webview(self, for_js_eval: bool = False) -> Any:
        """Get the appropriate WebView instance.

        Args:
            for_js_eval: If True, returns the underlying view that supports eval_js.
                        If False, returns AuroraView wrapper for API operations.

        Returns:
            WebView instance or None if not initialized.
        """
        if not hasattr(self, "_auroraview") or not self._auroraview:
            return self._webview

        if for_js_eval:
            # For JS execution, need the underlying QtWebView (not the wrapper)
            return getattr(self._auroraview, "view", self._auroraview)

        # For API operations, return the AuroraView wrapper
        return self._auroraview

    def _notify_api_ready(self) -> None:
        """Notify frontend that API is ready and trigger config reload.

        This dispatches a custom event that the frontend can listen to
        and use to reload the configuration after API registration.
        """
        webview = self._get_webview(for_js_eval=True)
        if webview is None:
            return

        js_code = """
(function() {
    console.log('[ShelfAPI] API ready notification received');
    // Dispatch custom event for frontend to listen to
    window.dispatchEvent(new CustomEvent('auroraview-api-ready'));

    // Also try to directly reload config if the hook is available
    if (window.__reloadShelfConfig && typeof window.__reloadShelfConfig === 'function') {
        console.log('[ShelfAPI] Calling __reloadShelfConfig...');
        window.__reloadShelfConfig();
    }
})();
"""
        try:
            if hasattr(webview, "eval_js"):
                webview.eval_js(js_code)
                logger.debug("Notified frontend that API is ready")
            elif hasattr(webview, "evaluate"):
                webview.evaluate(js_code)
                logger.debug("Notified frontend that API is ready (via evaluate)")
            elif hasattr(webview, "page") and hasattr(webview.page(), "runJavaScript"):
                webview.page().runJavaScript(js_code)
                logger.debug("Notified frontend that API is ready (via runJavaScript)")
            else:
                logger.warning("webview does not have eval_js/evaluate/runJavaScript method")
        except Exception as e:
            logger.warning(f"Failed to notify API ready: {e}")

    def _on_qt_load_progress(self, progress: int) -> None:
        """Handle Qt loadProgress signal."""
        self._load_progress = progress
        logger.debug(f"Qt loadProgress: {progress}%")
        self._emit_navigation_event("load_progress", progress)
        # Notify frontend about loading progress
        self._notify_frontend_loading_state(True, progress)

    def _on_qt_url_changed(self, url: str) -> None:
        """Handle Qt urlChanged signal."""
        self._current_url = url
        logger.debug(f"Qt urlChanged: {url}")

    def _on_qt_title_changed(self, title: str) -> None:
        """Handle Qt titleChanged signal."""
        logger.debug(f"Qt titleChanged: {title}")
        # Could update window title here if desired
        if self._dialog and hasattr(self._dialog, "setWindowTitle") and title and title not in ("", "about:blank"):
            pass  # Keep original title for shelf app

    def _notify_frontend_loading_state(self, is_loading: bool, progress: int) -> None:
        """Notify frontend about loading state changes.

        Emits a 'loading_state' event to the frontend with current loading status.
        """
        if self._webview is None:
            return
        try:
            if hasattr(self._webview, "emit"):
                self._webview.emit(
                    "loading_state",
                    {
                        "isLoading": is_loading,
                        "progress": progress,
                    },
                )
        except Exception as e:
            logger.debug(f"Failed to notify frontend loading state: {e}")

    def _show_hwnd_mode(self, debug: bool, _app: str) -> None:
        """Show using AuroraView with HWND integration (non-blocking).

        Creates a standalone WebView window in a background thread,
        freeing the DCC main thread for other operations.

        Args:
            debug: Enable DevTools for debugging.
            _app: DCC application name (unused, kept for API consistency).
        """
        import threading

        logger.info("HWND mode - Starting WebView in background thread...")

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        # Initialize synchronization primitives for thread coordination
        self._hwnd_ready_event = threading.Event()
        self._hwnd_debug = debug  # Store for use in thread

        # Create API (will be bound in background thread)
        self._api = ShelfAPI(self)

        # Start WebView in background thread (daemon so it doesn't block app exit)
        self._webview_thread = threading.Thread(
            target=self._hwnd_thread_main,
            name="AuroraView-HWND",
            daemon=True,
        )
        self._webview_thread.start()

        # Wait briefly for WebView to initialize (improves reliability)
        if self._hwnd_ready_event.wait(timeout=10.0):
            logger.info("HWND mode - WebView initialized successfully!")
        else:
            logger.warning("HWND mode - WebView initialization timeout, proceeding anyway...")

        logger.info("HWND mode - Background thread started, main thread free!")

    def _hwnd_thread_main(self) -> None:
        """Main function for HWND WebView background thread.

        Runs entirely in the background thread:
        1. Creates WebView instance
        2. Binds API for IPC
        3. Loads content
        4. Runs event loop (blocking until window closes)
        """
        try:
            from auroraview import WebView

            dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

            # Create WebView
            webview = WebView(
                title=self._title,
                width=self._width,
                height=self._height,
                debug=self._hwnd_debug,
                context_menu=self._hwnd_debug,
                asset_root=dist_dir,
            )

            self._webview = webview
            self._hwnd_setup_proxy(webview)
            self._hwnd_bind_api(webview)
            self._hwnd_load_content(webview)
            self._hwnd_setup_state(webview)
            self._hwnd_connect_ready_event(webview)

            # Signal that WebView is ready
            self._hwnd_ready_event.set()
            logger.info("HWND thread - WebView ready, signaled main thread")

            # This blocks until the window is closed
            webview.show_blocking()
            logger.info("HWND thread - WebView closed")

        except Exception as e:
            logger.error(f"HWND thread - Error: {e}", exc_info=True)
            self._hwnd_ready_event.set()  # Prevent main thread from waiting forever

    def _hwnd_setup_proxy(self, webview: Any) -> None:
        """Get thread-safe proxy for cross-thread JavaScript execution."""
        try:
            self._webview_proxy = webview.get_proxy()
            logger.debug("HWND thread - WebViewProxy obtained")
        except AttributeError:
            logger.warning("HWND thread - get_proxy() not available")
            self._webview_proxy = None

    def _hwnd_bind_api(self, webview: Any) -> None:
        """Bind API to WebView for IPC."""
        webview.bind_api(self._api)
        logger.debug("HWND thread - API bound")

    def _hwnd_load_content(self, webview: Any) -> None:
        """Load content (dev server or production build)."""
        if self._is_dev_mode():
            webview.load_url("http://localhost:5173")
        else:
            index_path = DIST_DIR / "index.html"
            if index_path.exists():
                from auroraview.utils import get_auroraview_entry_url

                webview.load_url(get_auroraview_entry_url("index.html"))
            else:
                logger.error(f"HWND thread - index.html not found: {index_path}")

    def _hwnd_setup_state(self, webview: Any) -> None:
        """Setup shared state for WebView."""
        with webview.state.batch_update() as batch:
            batch["app_name"] = self._title
            batch["dcc_mode"] = self._is_dcc_environment
            batch["current_host"] = self._current_host
            batch["theme"] = "dark"
            batch["integration_mode"] = self._integration_mode

    def _hwnd_connect_ready_event(self, webview: Any) -> None:
        """Connect to __auroraview_ready event for API re-registration."""
        if not hasattr(webview, "on"):
            return

        @webview.on("__auroraview_ready")
        def _handle_ready(_data: dict[str, Any]) -> None:
            logger.info("HWND thread - AuroraView ready, registering API")
            if self._api is not None and hasattr(webview, "bind_api"):
                webview.bind_api(self._api)

        self._hwnd_ready_handler = _handle_ready  # Prevent GC

    def _inject_api_methods_js(self, webview: Any) -> None:
        """Register API methods using Rust's high-performance register_api_methods.

        This uses the Rust core's register_api_methods which generates optimized
        JavaScript code at compile time via Askama templates.

        Note: This method may be called from a different thread than the WebView
        was created on.
        """
        # Get API method names from the bound API object
        api_methods = []
        if hasattr(self, "_api") and self._api is not None:
            for name in dir(self._api):
                if name.startswith("_"):
                    continue
                attr = getattr(self._api, name, None)
                if callable(attr):
                    api_methods.append(name)

        if not api_methods:
            logger.warning("No API methods found to register")
            return

        # Use Rust's register_api_methods for high-performance registration
        # Try direct method first (HWND mode - webview is Rust AuroraView directly)
        # Then try _core attribute (Qt mode - webview is Python wrapper with Rust core)
        try:
            if hasattr(webview, "register_api_methods"):
                # HWND mode: webview is Rust AuroraView directly
                webview.register_api_methods("api", api_methods)
                logger.info(f"Registered {len(api_methods)} API methods via Rust (direct): {api_methods}")
            else:
                # Qt mode: webview is Python wrapper, access Rust core via _core
                core = getattr(webview, "_core", None)
                if core is not None and hasattr(core, "register_api_methods"):
                    core.register_api_methods("api", api_methods)
                    logger.info(f"Registered {len(api_methods)} API methods via Rust (core): {api_methods}")
                else:
                    logger.warning("Rust register_api_methods not available, API methods not registered")
        except Exception as e:
            logger.error(f"Failed to register API methods via Rust: {e}")

    def _load_content(self) -> None:
        """Load the frontend content into the WebView."""
        logger.info(f"_load_content: DIST_DIR = {DIST_DIR}")
        logger.info(f"_load_content: DIST_DIR.exists() = {DIST_DIR.exists()}")

        if self._is_dev_mode():
            dev_url = "http://localhost:5173"
            logger.info(f"Loading dev URL: {dev_url}")
            self._webview.load_url(dev_url)
        else:
            index_path = DIST_DIR / "index.html"
            logger.info(f"_load_content: index_path = {index_path}")
            logger.info(f"_load_content: index_path.exists() = {index_path.exists()}")

            if index_path.exists():
                resolved_path = str(index_path.resolve())
                logger.info(f"Loading file: {resolved_path}")
                self._webview.load_file(resolved_path)
            else:
                logger.error(f"index.html not found at {index_path}")
                # Try alternative locations
                alt_paths = [
                    Path(__file__).parent / "dist" / "index.html",
                    Path(__file__).parent.parent / "dist" / "index.html",
                ]
                for alt_path in alt_paths:
                    logger.info(f"Trying alternative path: {alt_path} (exists: {alt_path.exists()})")
                    if alt_path.exists():
                        resolved_path = str(alt_path.resolve())
                        logger.info(f"Loading from alternative path: {resolved_path}")
                        self._webview.load_file(resolved_path)
                        return

                raise FileNotFoundError(f"index.html not found at {index_path}")

    def _on_webview_error(self, error_msg: str) -> None:
        """Called if WebView creation fails."""
        logger.error(f"Failed to create WebView: {error_msg}")

    def _show_dialog_with_fade(self, dialog: Any) -> None:
        """Show dialog with a smooth fade-in effect to reduce visual jarring.

        This creates a more polished user experience by avoiding the sudden
        appearance of the window with its title bar and borders.

        Args:
            dialog: The QDialog to show with fade effect.
        """
        from qtpy.QtCore import QPropertyAnimation
        from qtpy.QtWidgets import QApplication

        try:
            # First, ensure the dialog is ready but invisible
            dialog.setWindowOpacity(0.0)
            dialog.show()
            QApplication.processEvents()

            # Create fade-in animation
            animation = QPropertyAnimation(dialog, b"windowOpacity")
            animation.setDuration(150)  # 150ms fade-in
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)

            # Store reference to prevent garbage collection
            self._fade_animation = animation

            def _on_animation_finished() -> None:
                """Cleanup after animation completes."""
                dialog.setWindowOpacity(1.0)
                dialog.update()
                if self._webview:
                    self._webview.update()
                QApplication.processEvents()
                # Clear reference
                self._fade_animation = None

            animation.finished.connect(_on_animation_finished)
            animation.start()

        except Exception as e:
            # Fallback to direct show if animation fails
            logger.debug(f"Fade animation failed, using direct show: {e}")
            dialog.setWindowOpacity(1.0)
            dialog.show()
            dialog.update()
            if self._webview:
                self._webview.update()
            QApplication.processEvents()

    def _schedule_geometry_fixes(self) -> None:
        """Schedule geometry fixes after WebView initialization.

        This ensures the dialog and WebView have the correct size after
        all Qt layout operations have completed.
        """
        from qtpy.QtCore import QTimer
        from qtpy.QtWidgets import QApplication

        fix_count = [0]  # Use list to allow mutation in nested function

        def force_geometry() -> None:
            if not self._dialog or not self._webview:
                return

            fix_count[0] += 1
            current_size = self._dialog.size()
            webview_size = self._webview.size()
            logger.info(
                f"Geometry fix #{fix_count[0]}: dialog={current_size.width()}x{current_size.height()}, "
                f"webview={webview_size.width()}x{webview_size.height()}, "
                f"expected={self._width}x{self._height}"
            )

            # Set minimum sizes from config
            self._dialog.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])
            self._webview.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])

            # ALWAYS enforce the expected size - Qt timing issues can cause wrong sizes
            # even when current size appears correct, the WebView may not have resized
            need_resize = (
                current_size.width() < self._width
                or current_size.height() < self._height
                or webview_size.width() < self._width - 20  # Allow small margin
                or webview_size.height() < self._height - 20
            )

            if need_resize or fix_count[0] == 1:  # Always resize on first fix
                self._dialog.resize(self._width, self._height)
                logger.info(f"Geometry fixed: dialog resized to {self._width}x{self._height}")

            # Force layout to recalculate
            if self._layout:
                self._layout.setContentsMargins(0, 0, 0, 0)
                self._layout.setSpacing(0)
                self._layout.activate()
                self._layout.update()

            # Force WebView to fill the dialog content area
            content_rect = self._dialog.contentsRect()
            if content_rect.width() > 0 and content_rect.height() > 0:
                self._webview.setGeometry(content_rect)
                logger.debug(f"WebView geometry set to: {content_rect.width()}x{content_rect.height()}")

            self._webview.updateGeometry()

            # Force container geometry sync (critical for Qt6 and DCC apps)
            if hasattr(self._webview, "_force_container_geometry"):
                self._webview._force_container_geometry()

            # Also sync WebView2 controller bounds directly if available
            if hasattr(self._webview, "_sync_webview2_controller_bounds"):
                self._webview._sync_webview2_controller_bounds(content_rect.width(), content_rect.height())

            # Process events to apply changes
            QApplication.processEvents()

            # Log final sizes for debugging
            final_dialog = self._dialog.size()
            final_webview = self._webview.size()
            logger.debug(
                f"After fix #{fix_count[0]}: dialog={final_dialog.width()}x{final_dialog.height()}, "
                f"webview={final_webview.width()}x{final_webview.height()}"
            )

        # Schedule multiple geometry fixes to handle different DCC timing
        # First fix at 100ms for fast DCCs, subsequent fixes as fallback
        delays = [100, 500]
        if self._adapter:
            adapter_delays = self._adapter.get_geometry_fix_delays()
            if adapter_delays:
                delays = adapter_delays
            logger.debug(f"{self._adapter.name}: using geometry fix delays={delays}ms")

        for delay in delays:
            QTimer.singleShot(delay, force_geometry)

    def _schedule_webview2_child_fixes(self) -> None:
        """Schedule repeated fixes for WebView2 child windows (Qt6 compatibility).

        WebView2 creates multiple child windows (Chrome_WidgetWin_0, etc.) asynchronously
        during initialization. These child windows may not have proper WS_CHILD styles,
        causing them to be draggable independently from the Qt container.

        This is especially important for Qt6 where createWindowContainer behavior
        differs from Qt5.
        """
        if sys.platform != "win32":
            return

        from qtpy.QtCore import QTimer

        # Get the WebView's HWND - try multiple methods
        webview_hwnd = None
        if self._webview:
            # Method 1: Direct get_hwnd() on QtWebView
            if hasattr(self._webview, "get_hwnd"):
                webview_hwnd = self._webview.get_hwnd()
                logger.debug(f"Got HWND via QtWebView.get_hwnd(): {webview_hwnd}")

            # Method 2: Via _webview attribute (internal AuroraView)
            if not webview_hwnd:
                core = getattr(self._webview, "_webview", None)
                if core and hasattr(core, "get_hwnd"):
                    webview_hwnd = core.get_hwnd()
                    logger.debug(f"Got HWND via _webview.get_hwnd(): {webview_hwnd}")

            # Method 3: Via _core attribute
            if not webview_hwnd:
                core = getattr(self._webview, "_core", None)
                if core and hasattr(core, "get_hwnd"):
                    webview_hwnd = core.get_hwnd()
                    logger.debug(f"Got HWND via _core.get_hwnd(): {webview_hwnd}")

        if not webview_hwnd:
            logger.warning("No WebView HWND available for child window fixes")
            return

        logger.info(f"Scheduling WebView2 child window fixes for HWND=0x{webview_hwnd:X}")

        fix_count = [0]

        def fix_child_windows() -> None:
            """Fix all WebView2 child windows."""
            fix_count[0] += 1
            try:
                import auroraview

                fix_fn = getattr(auroraview, "fix_webview2_child_windows", None)
                if callable(fix_fn):
                    result = fix_fn(webview_hwnd)
                    logger.info(
                        f"WebView2 child fix #{fix_count[0]} applied for HWND=0x{webview_hwnd:X}, result={result}"
                    )
                else:
                    logger.warning("fix_webview2_child_windows not available in auroraview module")
            except Exception as e:
                logger.error(f"WebView2 child fix #{fix_count[0]} failed: {e}")

        # Schedule multiple fixes at different intervals
        # WebView2 creates child windows at various times during initialization
        delays = [50, 100, 200, 500, 1000, 2000, 5000]
        for delay in delays:
            QTimer.singleShot(delay, fix_child_windows)

    def _show_standalone_mode(self, debug: bool) -> None:
        """Show using regular WebView for standalone mode (blocking)."""
        # Window size is fixed - use default values
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

            from auroraview.utils import get_auroraview_entry_url

            auroraview_url = get_auroraview_entry_url("index.html")

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
        dockable: bool = False,
    ) -> None:
        """Show the shelf window.

        For DCC applications (Maya, Houdini, Nuke), pass the `app` parameter to
        enable embedded mode which prevents UI blocking.

        Args:
            debug: Enable debug mode with developer tools (F12 or right-click).
            app: DCC application name for parent integration (e.g., "maya",
                "houdini", "nuke"). If provided, will use non-blocking mode.
            mode: Integration mode for DCC apps:
                - "qt": Uses QtWebView for Qt widget integration (recommended).
                    Supports QDockWidget docking and automatic resize.
                    Uses createWindowContainer for native Qt layout integration.
                - "hwnd": Uses AuroraView with HWND for non-Qt integration.
                    Best for Unreal Engine or when Qt mode causes issues.
            dockable: If True, create a dockable panel in the DCC application.
                Requires DCC-specific support (Maya, Houdini, Nuke).
                When dockable=True, the panel can be docked into the DCC's
                native panel system.

        Example (Qt mode - recommended, floating window)::

            app = ShelfApp(config)
            app.show(app="maya", mode="qt")

        Example (Qt mode - dockable panel)::

            app = ShelfApp(config)
            app.show(app="maya", mode="qt", dockable=True)

        Example (HWND mode - for Unreal Engine)::

            app = ShelfApp(config)
            app.show(app="maya", mode="hwnd")

            # Get HWND for Unreal integration
            hwnd = app.get_hwnd()
        """
        logger.info(f"show() [1] Debug mode: {debug}")
        logger.info(f"show() [2] DCC app: {app}, mode: {mode}")

        # Clean up any existing resources from previous show() calls
        # This prevents delays when re-opening the window
        self._cleanup_previous_session()

        self._current_host = app.lower() if app else ""
        # Store the requested integration mode ("qt" or "hwnd"). This is a
        # DCC-level integration concept and is intentionally named differently
        # from the core WebView parent_mode/EmbedMode used in the Rust layer.
        self._integration_mode = mode
        self._dockable = dockable
        logger.info(f"show() [3] Current host: {self._current_host}")

        # Initialize DCC adapter
        logger.info("show() [4] Getting adapter...")
        self._adapter = get_adapter(app)
        logger.info(f"show() [5] Adapter: {self._adapter.name}, recommended_mode: {self._adapter.recommended_mode}")

        # Configure managers with adapter
        self._window_manager.set_adapter(self._adapter)
        self._webview_manager.set_adapter(self._adapter)

        # Call adapter's on_init hook
        logger.info("show() [6] Calling adapter.on_init...")
        self._adapter.on_init(self)
        logger.info("show() [7] adapter.on_init done")

        # Use adapter's recommended mode if mode is default "qt"
        effective_mode = mode
        if mode == "qt" and self._adapter.recommended_mode != "qt":
            effective_mode = self._adapter.recommended_mode
        logger.info(f"show() [8] effective_mode={effective_mode}")

        # Detect whether we are running inside a DCC host.
        # Desktop/standalone mode is NOT a DCC host - it runs independently.
        # HWND mode does not require Qt at all, so gating this flag
        # on QT_AVAILABLE would incorrectly force DCC apps without Qt extras
        # (or with missing qtpy) into the standalone, blocking code path.
        is_dcc_host = bool(app) and effective_mode != "standalone"

        # Internal flag: whether we are running inside a DCC host. The exposed
        # state key remains "dcc_mode" for backward compatibility.
        self._is_dcc_environment = is_dcc_host
        logger.info(f"show() [9] Creating launcher, dcc_mode={self._is_dcc_environment}")
        self._launcher = ToolLauncher(self._config, dcc_mode=self._is_dcc_environment)
        logger.info("show() [10] Launcher created")

        # Branch by integration mode and environment.
        # - "standalone": Native tao/wry window (desktop mode, no Qt)
        # - "hwnd": AuroraView with HWND for non-Qt apps (Unreal Engine)
        # - "qt": QtWebView for Qt widget integration (Maya, Houdini, Nuke)
        if effective_mode == "standalone":
            # Desktop mode: use native tao/wry window directly
            logger.info("show() [11] Calling _show_standalone_mode (desktop)...")
            self._show_standalone_mode(debug)
            logger.info("show() [12] _show_standalone_mode returned!")
        elif is_dcc_host and effective_mode == "hwnd":
            logger.info("show() [11] Calling _show_hwnd_mode...")
            self._show_hwnd_mode(debug, app)
            logger.info("show() [12] _show_hwnd_mode returned!")
        elif is_dcc_host and QT_AVAILABLE:
            if dockable and self._adapter.supports_dockable():
                logger.info("show() [11] Calling _show_dockable_mode...")
                self._show_dockable_mode(debug, app)
                logger.info("show() [12] _show_dockable_mode returned!")
            else:
                if dockable and not self._adapter.supports_dockable():
                    logger.warning(
                        f"Dockable mode requested but {self._adapter.name} "
                        "does not support docking. Using floating window."
                    )
                logger.info("show() [11] Calling _show_qt_mode...")
                self._show_qt_mode(debug, app)
                logger.info("show() [12] _show_qt_mode returned!")
        else:
            if is_dcc_host and not QT_AVAILABLE and effective_mode != "hwnd":
                logger.warning(
                    f"Qt integration requested for {app} but not available. "
                    "Using standalone mode. Install with: pip install auroraview[qt]"
                )
            logger.info("show() [11] Calling _show_standalone_mode...")
            self._show_standalone_mode(debug)
            logger.info("show() [12] _show_standalone_mode returned!")

        logger.info("show() [DONE] Method complete, returning to caller")

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

    def _load_url_in_webview(self, webview: Any, url: str) -> None:
        """Load a URL in a WebView, handling different URL formats.

        Supports:
        - Dev server URLs (http://localhost:*, http://127.0.0.1:*)
        - AuroraView protocol URLs (https://auroraview.localhost/*, auroraview://*)
        - External HTTP URLs
        - Relative paths (resolved to DIST_DIR)

        Args:
            webview: The WebView instance to load the URL in.
            url: The URL or path to load.
        """
        # Dev server URL - load directly
        if url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
            logger.info(f"Loading dev URL: {url}")
            webview.load_url(url)
            return

        # AuroraView protocol URL - extract path and load as file
        if "auroraview.localhost" in url or url.startswith("auroraview://"):
            if "auroraview.localhost" in url:
                # https://auroraview.localhost/settings.html -> settings.html
                path = url.split("auroraview.localhost/")[-1]
            else:
                # auroraview://settings.html -> settings.html
                path = url.replace("auroraview://", "")
            file_path = DIST_DIR / path
            if file_path.exists():
                logger.info(f"Loading file: {file_path}")
                webview.load_file(str(file_path.resolve()))
            else:
                logger.warning(f"File not found: {file_path}, falling back to URL")
                webview.load_url(url)
            return

        # External HTTP URL
        if url.startswith("http"):
            logger.info(f"Loading external URL: {url}")
            webview.load_url(url)
            return

        # Relative path - resolve to file
        file_path = DIST_DIR / url.lstrip("/")
        if file_path.exists():
            logger.info(f"Loading relative path: {file_path}")
            webview.load_file(str(file_path.resolve()))
        else:
            logger.warning(f"Path not found: {file_path}, falling back to URL")
            webview.load_url(url)

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

        if not self._is_dcc_environment or not QT_AVAILABLE:
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
            # Set window flags based on frameless mode
            if self._frameless:
                # Frameless window - HTML content provides its own title bar
                dialog.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            else:
                # Normal window with system title bar
                dialog.setWindowFlags(Qt.Window)

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

            # Load URL using unified handler
            self._load_url_in_webview(webview, url)

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
        """Register window event handlers for DCC mode.

        Note: Window size is now fixed, so resize events are logged but not saved.
        """
        # Use the AuroraView wrapper for event binding, not the native widget
        if not hasattr(self, "_auroraview") or not self._auroraview:
            logger.debug("AuroraView wrapper not available for event registration")
            return

        # Check if the AuroraView wrapper has the on method
        if not hasattr(self._auroraview, "on"):
            logger.debug("AuroraView wrapper does not support on() method")
            return

        try:

            @self._auroraview.on("window_resize")
            def handle_resize(data: dict[str, Any]) -> None:
                width = data.get("width", 0)
                height = data.get("height", 0)
                # Size is fixed - just log for debugging
                logger.debug(f"Window resize event: {width}x{height}")
        except Exception as e:
            logger.warning(f"Failed to register window_resize event: {e}")

    def _setup_shared_state(self) -> None:
        """Initialize shared state for bidirectional sync."""
        # Use the AuroraView wrapper for state access, not the native widget
        if not hasattr(self, "_auroraview") or not self._auroraview:
            logger.debug("AuroraView wrapper not available for state setup")
            return

        try:
            state = self._auroraview.state
            with state.batch_update() as batch:
                batch["app_name"] = self._title
                # Keep front-end state key name stable while using the clearer
                # internal flag _is_dcc_environment on the Python side.
                batch["dcc_mode"] = self._is_dcc_environment
                batch["current_host"] = self._current_host
                batch["theme"] = "dark"
                batch["integration_mode"] = self._integration_mode

            @state.on_change
            def handle_state_change(key: str, value: Any, old_value: Any):
                logger.debug(f"[State] {key}: {old_value} -> {value}")

            logger.debug("Shared state initialized (batch mode)")
        except Exception as e:
            logger.warning(f"Failed to setup shared state: {e}")

    def _register_commands(self) -> None:
        """Register RPC-style commands callable from JavaScript."""
        # Use the AuroraView wrapper for command registration, not the native widget
        if not hasattr(self, "_auroraview") or not self._auroraview:
            logger.debug("AuroraView wrapper not available for command registration")
            return

        try:

            @self._auroraview.command
            def get_app_info() -> dict[str, Any]:
                return {
                    "title": self._title,
                    # Public API keeps the key name "dcc_mode"; value is
                    # backed by the internal _is_dcc_environment flag.
                    "dcc_mode": self._is_dcc_environment,
                    "current_host": self._current_host,
                    "version": "1.0.0",
                    "integration_mode": self._integration_mode,
                }

            @self._auroraview.command("set_theme")
            def set_theme(theme: str = "dark") -> dict[str, bool]:
                self._auroraview.state["theme"] = theme
                logger.info(f"Theme changed to: {theme}")
                return {"success": True}

            logger.debug("Commands registered")
        except Exception as e:
            logger.warning(f"Failed to register commands: {e}")

    @property
    def config(self) -> ShelvesConfig:
        """Get the current configuration."""
        return self._config
