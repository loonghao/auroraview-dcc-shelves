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
from typing import TYPE_CHECKING, Any, Callable, Optional

# Import WebView for standalone mode
import auroraview
from auroraview import WebView

# Try to import Qt components for DCC integration
QT_AVAILABLE = False
try:
    from auroraview import AuroraView, QtWebView

    QT_AVAILABLE = True
except ImportError:
    AuroraView = None  # type: ignore
    QtWebView = None  # type: ignore

# Warmup API availability check
WARMUP_AVAILABLE = hasattr(auroraview, "start_warmup")

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
from auroraview_dcc_shelves.styles import FLAT_STYLE_QSS, LOADING_STYLE_QSS
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

        # Loading state tracking (new API features)
        self._is_loading = False
        self._load_progress = 0
        self._current_url = ""
        self._navigation_callbacks: dict[str, list[Callable[..., None]]] = {
            "navigation_started": [],
            "navigation_completed": [],
            "navigation_failed": [],
            "load_progress": [],
            "warmup_progress": [],
        }

        # Zoom state tracking
        self._current_zoom = 1.0  # Default zoom level (100%)
        self._auto_zoom_enabled = True  # Whether to auto-detect optimal zoom

        # API registration state tracking (防止重复注册)
        self._api_registered = False  # Whether API has been registered

    # =========================================================================
    # WebView2 Warmup API (New AuroraView Features)
    # =========================================================================
    # These APIs allow pre-initializing WebView2 environment before showing UI,
    # which significantly reduces the perceived startup time in DCC applications.

    @staticmethod
    def start_warmup() -> bool:
        """Start WebView2 warmup in background (non-blocking).

        Call this early in DCC startup to pre-initialize WebView2 environment.
        This runs in a background thread and doesn't block the main thread.

        Returns:
            True if warmup started successfully, False if not available.

        Example:
            >>> # In DCC startup script (e.g., userSetup.py for Maya)
            >>> from auroraview_dcc_shelves import ShelfApp
            >>> ShelfApp.start_warmup()  # Non-blocking, starts background init
        """
        if not WARMUP_AVAILABLE:
            logger.debug("Warmup API not available in this version of AuroraView")
            return False
        try:
            auroraview.start_warmup()
            logger.info("WebView2 warmup started in background")
            return True
        except Exception as e:
            logger.warning(f"Failed to start warmup: {e}")
            return False

    @staticmethod
    def warmup_sync(timeout_ms: int = 30000) -> bool:
        """Synchronously wait for WebView2 warmup to complete (blocking).

        This blocks the current thread until warmup completes or times out.
        Use this when you need to ensure WebView2 is ready before proceeding.

        Args:
            timeout_ms: Maximum time to wait in milliseconds (default: 30000).

        Returns:
            True if warmup completed successfully, False otherwise.

        Example:
            >>> # Wait for WebView2 to be fully ready
            >>> if ShelfApp.warmup_sync(timeout_ms=10000):
            ...     print("WebView2 ready!")
            ... else:
            ...     print("Warmup timed out or failed")
        """
        if not WARMUP_AVAILABLE:
            logger.debug("Warmup API not available")
            return False
        try:
            auroraview.warmup_sync(timeout_ms)
            logger.info(f"WebView2 warmup completed (timeout={timeout_ms}ms)")
            return True
        except Exception as e:
            logger.warning(f"Warmup sync failed: {e}")
            return False

    @staticmethod
    def is_warmup_complete() -> bool:
        """Check if WebView2 warmup has completed.

        Returns:
            True if warmup is complete and WebView2 is ready.

        Example:
            >>> if ShelfApp.is_warmup_complete():
            ...     print("WebView2 is ready!")
        """
        if not WARMUP_AVAILABLE:
            return False
        try:
            return auroraview.is_warmup_complete()
        except Exception:
            return False

    @staticmethod
    def get_warmup_progress() -> int:
        """Get the current warmup progress (0-100).

        Returns:
            Progress percentage (0-100), or 0 if not available.

        Example:
            >>> progress = ShelfApp.get_warmup_progress()
            >>> print(f"Warmup progress: {progress}%")
        """
        if not WARMUP_AVAILABLE:
            return 0
        try:
            return auroraview.get_warmup_progress()
        except Exception:
            return 0

    @staticmethod
    def get_warmup_stage() -> str:
        """Get the current warmup stage description.

        Returns:
            Human-readable stage description.

        Example:
            >>> stage = ShelfApp.get_warmup_stage()
            >>> print(f"Current stage: {stage}")
            "Creating WebView2 environment..."
        """
        if not WARMUP_AVAILABLE:
            return "Warmup not available"
        try:
            return auroraview.get_warmup_stage()
        except Exception:
            return "Unknown"

    @staticmethod
    def get_warmup_status() -> dict[str, Any]:
        """Get complete warmup status information.

        Returns:
            Dictionary with warmup status:
            - initiated: bool - Whether warmup has been started
            - complete: bool - Whether warmup is complete
            - progress: int - Progress percentage (0-100)
            - stage: str - Current stage description
            - duration_ms: int - Time elapsed since warmup started
            - error: Optional[str] - Error message if failed
            - user_data_folder: Optional[str] - WebView2 data folder path

        Example:
            >>> status = ShelfApp.get_warmup_status()
            >>> print(f"Progress: {status['progress']}%")
            >>> print(f"Stage: {status['stage']}")
        """
        if not WARMUP_AVAILABLE:
            return {
                "initiated": False,
                "complete": False,
                "progress": 0,
                "stage": "Warmup API not available",
                "duration_ms": 0,
                "error": None,
                "user_data_folder": None,
            }
        try:
            return auroraview.get_warmup_status()
        except Exception as e:
            return {
                "initiated": False,
                "complete": False,
                "progress": 0,
                "stage": "Error",
                "duration_ms": 0,
                "error": str(e),
                "user_data_folder": None,
            }

    def on_warmup_progress(self, callback: Callable[[int, str], None]) -> None:
        """Register a callback for warmup progress updates.

        Args:
            callback: Function to call with (progress, stage) during warmup.

        Example:
            >>> def on_progress(progress, stage):
            ...     print(f"Warmup: {progress}% - {stage}")
            >>> app.on_warmup_progress(on_progress)
        """
        self._navigation_callbacks["warmup_progress"].append(callback)

    # =========================================================================
    # Loading State API (New AuroraView Features)
    # =========================================================================

    @property
    def is_loading(self) -> bool:
        """Check if the WebView is currently loading a page.

        Returns:
            True if loading, False otherwise.

        Example:
            >>> if app.is_loading:
            ...     print("Still loading...")
        """
        if self._webview is None:
            return self._is_loading
        # Try to get from webview if available
        if hasattr(self._webview, "is_loading"):
            return self._webview.is_loading
        return self._is_loading

    @property
    def load_progress(self) -> int:
        """Get the current page load progress (0-100).

        Returns:
            Progress percentage (0-100).

        Example:
            >>> progress = app.load_progress
            >>> print(f"Loading: {progress}%")
        """
        if self._webview is None:
            return self._load_progress
        # Try to get from webview signals if available
        if hasattr(self._webview, "_signals") and hasattr(self._webview._signals, "load_progress_value"):
            return self._webview._signals.load_progress_value
        return self._load_progress

    @property
    def current_url(self) -> str:
        """Get the current URL.

        Returns:
            Current URL string.
        """
        if self._webview is None:
            return self._current_url
        if hasattr(self._webview, "_signals") and hasattr(self._webview._signals, "current_url"):
            return self._webview._signals.current_url
        return self._current_url

    def stop(self) -> None:
        """Stop the current page loading.

        Example:
            >>> if app.is_loading:
            ...     app.stop()
            ...     print("Loading cancelled")
        """
        if self._webview is None:
            logger.warning("Cannot stop: WebView not initialized")
            return
        if hasattr(self._webview, "stop"):
            self._webview.stop()
            logger.info("Page loading stopped")
        else:
            logger.debug("WebView does not support stop()")

    def on_navigation_started(self, callback: Callable[[str], None]) -> None:
        """Register a callback for navigation start events.

        Args:
            callback: Function to call with the URL when navigation starts.

        Example:
            >>> def on_start(url):
            ...     print(f"Started loading: {url}")
            >>> app.on_navigation_started(on_start)
        """
        self._navigation_callbacks["navigation_started"].append(callback)

    def on_navigation_completed(self, callback: Callable[[str, bool], None]) -> None:
        """Register a callback for navigation completion events.

        Args:
            callback: Function to call with (url, success) when navigation completes.

        Example:
            >>> def on_complete(url, success):
            ...     print(f"Loaded: {url}, success={success}")
            >>> app.on_navigation_completed(on_complete)
        """
        self._navigation_callbacks["navigation_completed"].append(callback)

    def on_navigation_failed(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for navigation failure events.

        Args:
            callback: Function to call with (url, error) when navigation fails.

        Example:
            >>> def on_fail(url, error):
            ...     print(f"Failed to load {url}: {error}")
            >>> app.on_navigation_failed(on_fail)
        """
        self._navigation_callbacks["navigation_failed"].append(callback)

    def on_load_progress(self, callback: Callable[[int], None]) -> None:
        """Register a callback for load progress events.

        Args:
            callback: Function to call with progress (0-100) during loading.

        Example:
            >>> def on_progress(progress):
            ...     print(f"Loading: {progress}%")
            >>> app.on_load_progress(on_progress)
        """
        self._navigation_callbacks["load_progress"].append(callback)

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
        callback: Optional[Callable[[Optional[str], Optional[Exception]], None]] = None,
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
    # Zoom API - Smart Display Adaptation
    # =========================================================================
    # These APIs allow controlling zoom level for different screen resolutions
    # (4K, 2K, laptop screens) and user preferences.

    def set_zoom(self, scale_factor: float) -> bool:
        """Set the zoom level of the WebView content.

        Args:
            scale_factor: Zoom scale factor (1.0 = 100%, 1.5 = 150%, 0.8 = 80%).
                         Valid range is typically 0.25 to 5.0.

        Returns:
            True if zoom was set successfully, False otherwise.

        Example:
            >>> app.set_zoom(1.25)  # 125% zoom for 4K displays
            >>> app.set_zoom(0.9)   # 90% zoom for small screens
        """
        if self._webview is None:
            logger.warning("Cannot set zoom: WebView not initialized")
            return False

        try:
            if hasattr(self._webview, "set_zoom"):
                self._webview.set_zoom(scale_factor)
                self._current_zoom = scale_factor
                logger.info(f"Zoom set to {scale_factor * 100:.0f}%")
                return True
            else:
                # Fallback: use CSS zoom via JavaScript
                js = f"document.body.style.zoom = '{scale_factor}';"
                if hasattr(self._webview, "eval_js"):
                    self._webview.eval_js(js)
                    self._current_zoom = scale_factor
                    logger.info(f"Zoom set to {scale_factor * 100:.0f}% (CSS fallback)")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to set zoom: {e}")
            return False

    def get_zoom(self) -> float:
        """Get the current zoom level.

        Returns:
            Current zoom scale factor (1.0 = 100%).
        """
        return getattr(self, "_current_zoom", 1.0)

    def zoom_in(self, step: float = 0.1) -> bool:
        """Increase zoom level by step.

        Args:
            step: Amount to increase zoom (default: 0.1 = 10%).

        Returns:
            True if zoom was changed successfully.
        """
        new_zoom = min(self.get_zoom() + step, 3.0)  # Max 300%
        return self.set_zoom(new_zoom)

    def zoom_out(self, step: float = 0.1) -> bool:
        """Decrease zoom level by step.

        Args:
            step: Amount to decrease zoom (default: 0.1 = 10%).

        Returns:
            True if zoom was changed successfully.
        """
        new_zoom = max(self.get_zoom() - step, 0.5)  # Min 50%
        return self.set_zoom(new_zoom)

    def reset_zoom(self) -> bool:
        """Reset zoom to 100%.

        Returns:
            True if zoom was reset successfully.
        """
        return self.set_zoom(1.0)

    def auto_zoom(self) -> float:
        """Automatically detect and set optimal zoom based on screen DPI/resolution.

        This analyzes the current display and sets an appropriate zoom level:
        - 4K displays (3840x2160+): 125-150%
        - 2K/QHD displays (2560x1440): 110-125%
        - Full HD (1920x1080): 100%
        - Laptop/smaller screens: 90-100%

        Returns:
            The zoom level that was applied.
        """
        try:
            # Try to get screen info via Qt
            from qtpy.QtGui import QScreen
            from qtpy.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                screen: QScreen = app.primaryScreen()
                dpi = screen.logicalDotsPerInch()
                geometry = screen.geometry()
                width = geometry.width()
                height = geometry.height()
                device_pixel_ratio = screen.devicePixelRatio()

                logger.info(f"Screen info: {width}x{height}, DPI={dpi}, devicePixelRatio={device_pixel_ratio}")

                # Calculate optimal zoom based on screen characteristics
                zoom = self._calculate_optimal_zoom(width, height, dpi, device_pixel_ratio)
                self.set_zoom(zoom)
                return zoom

        except ImportError:
            logger.debug("Qt not available for screen detection")
        except Exception as e:
            logger.warning(f"Auto zoom detection failed: {e}")

        # Default to 100% if detection fails
        return 1.0

    def _calculate_optimal_zoom(
        self,
        width: int,
        height: int,
        dpi: float,
        device_pixel_ratio: float,
    ) -> float:
        """Calculate optimal zoom level based on screen characteristics.

        Args:
            width: Screen width in pixels.
            height: Screen height in pixels.
            dpi: Logical DPI of the screen.
            device_pixel_ratio: Device pixel ratio (for HiDPI displays).

        Returns:
            Recommended zoom level.
        """
        # Base zoom on device pixel ratio (HiDPI awareness)
        if device_pixel_ratio >= 2.0:
            # Retina/HiDPI - scale down slightly as OS already scales
            base_zoom = 1.0
        elif device_pixel_ratio >= 1.5:
            base_zoom = 1.1
        else:
            base_zoom = 1.0

        # Adjust based on resolution
        if width >= 3840:  # 4K or higher
            resolution_factor = 1.25
        elif width >= 2560:  # 2K/QHD
            resolution_factor = 1.1
        elif width >= 1920:  # Full HD
            resolution_factor = 1.0
        elif width >= 1366:  # Common laptop
            resolution_factor = 0.95
        else:  # Smaller screens
            resolution_factor = 0.9

        # Adjust based on DPI (Windows scaling)
        if dpi > 120:  # 125% or higher Windows scaling
            dpi_factor = 0.9  # Compensate for OS scaling
        elif dpi > 96:  # Some scaling
            dpi_factor = 0.95
        else:
            dpi_factor = 1.0

        # Calculate final zoom
        zoom = base_zoom * resolution_factor * dpi_factor

        # Clamp to reasonable range
        zoom = max(0.75, min(zoom, 1.5))

        logger.info(f"Auto zoom calculated: {zoom:.2f} (base={base_zoom}, res={resolution_factor}, dpi={dpi_factor})")
        return round(zoom, 2)

    def _emit_navigation_event(self, event: str, *args: Any) -> None:
        """Emit a navigation event to all registered callbacks."""
        for callback in self._navigation_callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Navigation callback error ({event}): {e}")

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
            raise RuntimeError(f"Could not get {app} main window. Please ensure {app} UI is fully loaded.")
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
                webview.emit(
                    "launch_result", {"success": True, "message": f"Tool launched: {button_id}", "buttonId": button_id}
                )
            except LaunchError as e:
                logger.error(f"Failed to launch tool {button_id}: {e}")
                webview.emit("launch_result", {"success": False, "message": str(e), "buttonId": button_id})

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
            style_sheet=LOADING_STYLE_QSS,
        )
        self._layout = self._window_manager.layout

        self._window_manager.show_dialog()
        logger.info("Qt mode - Dialog shown, deferring WebView initialization...")

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
        """Called when QtWebView is ready in dockable mode.

        Uses WebViewManager for WebView setup and configuration.
        """
        logger.info("Dockable mode - WebView ready, completing initialization...")

        # Use WebViewManager to setup WebView
        self._webview_manager.setup_webview(
            webview=webview,
            min_width=MAIN_WINDOW_CONFIG["min_width"],
            min_height=MAIN_WINDOW_CONFIG["min_height"],
        )
        self._webview = self._webview_manager.webview

        # Replace placeholder with WebView
        self._window_manager.remove_widget_from_layout(self._placeholder)
        self._webview_manager.cleanup_placeholder()
        self._placeholder = None
        self._window_manager.add_widget_to_layout(self._webview)

        # Create API and AuroraView wrapper
        self._api = ShelfAPI(self)
        self._auroraview = self._webview_manager.create_auroraview_wrapper(
            parent=self._dockable_container,
            api=self._api,
            keep_alive_root=self._dockable_container,
        )

        # Bind API to WebView
        self._webview_manager.bind_api(self._api)

        # Connect Qt signals for navigation events
        self._connect_qt_signals()

        self._load_content()
        self._register_window_events()
        self._setup_shared_state()
        self._register_commands()
        self._webview_manager.show()

        # Schedule API re-registration after page load
        self._schedule_api_registration()

        # Call adapter's on_show hook
        if self._adapter:
            self._adapter.on_show(self)

        logger.info("Dockable mode - WebView initialization complete!")

    def _init_webview_deferred_qt(self) -> None:
        """Initialize WebView in Qt mode (deferred).

        Uses WindowManager for dialog adjustments and WebViewManager for WebView creation.
        """
        debug = self._init_params["debug"]

        # Update dialog style
        self._window_manager.set_dialog_style(FLAT_STYLE_QSS)

        # Adjust dialog size to ensure content area matches requested size
        self._window_manager.adjust_dialog_for_content(self._width, self._height)

        # Get content rect for WebView sizing
        content_width, content_height = self._window_manager.get_content_rect()
        webview_width = content_width if content_width > 0 else self._width
        webview_height = content_height if content_height > 0 else self._height
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
            logger.info("Qt mode - Placeholder added to layout")
        except Exception as e:
            logger.error(f"Failed to create QtWebView: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _on_webview_ready_qt(self, webview: Any) -> None:
        """Called when QtWebView is ready.

        Uses WebViewManager for WebView setup and configuration.
        """
        from qtpy.QtWidgets import QApplication

        logger.info("Qt mode - WebView ready, completing initialization...")

        # Use WebViewManager to setup WebView
        self._webview_manager.setup_webview(
            webview=webview,
            min_width=MAIN_WINDOW_CONFIG["min_width"],
            min_height=MAIN_WINDOW_CONFIG["min_height"],
        )
        self._webview = self._webview_manager.webview

        # Replace placeholder with WebView
        self._window_manager.remove_widget_from_layout(self._placeholder)
        self._webview_manager.cleanup_placeholder()
        self._placeholder = None
        # Add WebView with stretch factor to fill available space
        if self._layout:
            self._layout.addWidget(self._webview, 1)

        # Force layout update immediately after adding WebView
        # This is critical for Qt6/PySide6 where layout updates may be delayed
        if self._layout:
            self._layout.activate()
            self._layout.update()
        self._dialog.updateGeometry()
        self._webview.updateGeometry()

        # Force WebView's internal container to fill
        if hasattr(self._webview, "_force_container_geometry"):
            self._webview._force_container_geometry()

        QApplication.processEvents()

        # Create API and AuroraView wrapper
        self._api = ShelfAPI(self)
        self._auroraview = self._webview_manager.create_auroraview_wrapper(
            parent=self._dialog,
            api=self._api,
            keep_alive_root=self._dialog,
        )

        # Bind API to WebView
        self._webview_manager.bind_api(self._api)

        # Connect Qt signals for navigation events (new API)
        self._connect_qt_signals()

        self._load_content()
        self._register_window_events()
        self._setup_shared_state()
        self._register_commands()
        self._webview_manager.show()
        self._schedule_geometry_fixes()

        # Schedule API re-registration after page load
        # This is needed because QtWebView uses JS fallback for API registration,
        # which requires the page to be loaded first
        self._schedule_api_registration()

        # Call adapter's on_show hook
        if self._adapter:
            self._adapter.on_show(self)

        logger.info("Qt mode - WebView initialization complete!")

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
            # Re-register API methods after page load for JS fallback to work
            self._register_api_after_load()
        else:
            self._emit_navigation_event("navigation_failed", self._current_url, "Load failed")
        # Notify frontend about loading state
        self._notify_frontend_loading_state(False, 100 if success else 0)

    def _register_api_after_load(self) -> None:
        """Re-register API methods after page load (async version).

        This uses QTimer to schedule API registration in non-blocking steps,
        preventing UI freezes during IPC initialization.
        """
        # Guard: Prevent multiple registrations
        if self._api_registered:
            logger.debug("[_register_api_after_load] API already registered, skipping")
            return

        if self._api is None:
            return

        from qtpy.QtCore import QTimer

        # Mark as registered immediately to prevent concurrent calls
        self._api_registered = True
        logger.info("[_register_api_after_load] Starting API registration (first time)")

        # Step 1: Bind API (scheduled with 0ms delay to yield to event loop)
        def step1_bind_api() -> None:
            try:
                webview = self._get_auroraview_or_webview()
                if webview and hasattr(webview, "bind_api"):
                    logger.info("[Async] Step 1: Re-registering ShelfAPI...")
                    webview.bind_api(self._api)
                    logger.info("[Async] Step 1: bind_api completed")
                # Schedule step 2
                QTimer.singleShot(0, step2_inject_js)
            except Exception as e:
                logger.warning(f"[Async] Step 1 failed: {e}")
                QTimer.singleShot(0, step2_inject_js)  # Continue anyway

        # Step 2: Inject API methods JS
        def step2_inject_js() -> None:
            try:
                logger.info("[Async] Step 2: Injecting API methods JS...")
                self._inject_api_methods_js()
                logger.info("[Async] Step 2: API methods injected")
                # Schedule step 3
                QTimer.singleShot(0, step3_notify_ready)
            except Exception as e:
                logger.warning(f"[Async] Step 2 failed: {e}")
                QTimer.singleShot(0, step3_notify_ready)  # Continue anyway

        # Step 3: Notify API ready
        def step3_notify_ready() -> None:
            try:
                logger.info("[Async] Step 3: Notifying API ready...")
                self._notify_api_ready()
                logger.info("[Async] Step 3: API registration complete")
            except Exception as e:
                logger.warning(f"[Async] Step 3 failed: {e}")

        # Start the async chain
        QTimer.singleShot(10, step1_bind_api)  # Small delay to let page settle

    def _get_auroraview_or_webview(self) -> Any:
        """Get AuroraView or WebView instance for API operations."""
        if hasattr(self, "_auroraview") and self._auroraview:
            return self._auroraview
        return self._webview

    def _get_view_for_eval(self) -> Any:
        """Get the view instance that supports eval_js for JS execution.

        AuroraView wraps the actual WebView, so we need to get the underlying
        view that has the eval_js method.
        """
        if hasattr(self, "_auroraview") and self._auroraview:
            # AuroraView has a .view property that returns the underlying QtWebView
            if hasattr(self._auroraview, "view"):
                return self._auroraview.view
            return self._auroraview
        return self._webview

    def _inject_api_methods_js(self) -> None:
        """Inject JavaScript to register API methods manually.

        When register_api_methods is not available in core, we need to
        manually create the API method wrappers in JavaScript.
        """
        if self._api is None:
            return

        webview = self._get_view_for_eval()
        if webview is None:
            return

        # Get all public methods from ShelfAPI
        method_names = [
            name for name in dir(self._api) if not name.startswith("_") and callable(getattr(self._api, name))
        ]

        logger.info(f"[_inject_api_methods_js] Found {len(method_names)} API methods")

        if not method_names:
            logger.warning("[_inject_api_methods_js] No methods found to inject!")
            return

        # Build JavaScript code to register methods
        # Note: Rust core's register_api_methods may have already injected the API,
        # but in some environments (especially DCC apps) we need to manually inject
        # because the timing may be off or register_api_methods is not supported.
        methods_js = ", ".join(f"'{m}'" for m in method_names)
        js_code = f"""
(function() {{
    console.log('[ShelfAPI] Checking auroraview availability...');
    console.log('[ShelfAPI] window.auroraview:', typeof window.auroraview);

    if (!window.auroraview) {{
        console.error('[ShelfAPI] window.auroraview not available');
        return;
    }}

    console.log('[ShelfAPI] window.auroraview.call:', typeof window.auroraview.call);
    console.log('[ShelfAPI] window.auroraview.api:', window.auroraview.api);

    // Create api namespace if it doesn't exist
    if (!window.auroraview.api) {{
        console.log('[ShelfAPI] Creating api namespace...');
        window.auroraview.api = {{}};
    }}

    // Check if API methods are already registered by Rust core
    var methods = [{methods_js}];
    var existingMethods = Object.keys(window.auroraview.api);
    console.log('[ShelfAPI] Existing methods:', existingMethods);
    console.log('[ShelfAPI] Methods to register:', methods);

    // Register each API method
    var registeredCount = 0;
    methods.forEach(function(methodName) {{
        if (window.auroraview.api[methodName]) {{
            console.log('[ShelfAPI] Method already exists:', methodName);
            return; // Already registered
        }}

        // Create wrapper function that calls Python handler
        window.auroraview.api[methodName] = function(params) {{
            console.log('[ShelfAPI] Calling api.' + methodName, params);
            return new Promise(function(resolve, reject) {{
                try {{
                    // Use auroraview.call to invoke the Python handler
                    var result = window.auroraview.call('api.' + methodName, params || {{}});
                    console.log('[ShelfAPI] Result from api.' + methodName + ':', result, 'type:', typeof result);
                    if (result && typeof result.then === 'function') {{
                        result.then(function(data) {{
                            console.log('[ShelfAPI] Resolved api.' + methodName + ':', data);
                            resolve(data);
                        }}).catch(function(err) {{
                            console.error('[ShelfAPI] Rejected api.' + methodName + ':', err);
                            reject(err);
                        }});
                    }} else {{
                        resolve(result);
                    }}
                }} catch (e) {{
                    console.error('[ShelfAPI] Error calling api.' + methodName + ':', e);
                    reject(e);
                }}
            }});
        }};
        registeredCount++;
    }});

    console.log('[ShelfAPI] Registered ' + registeredCount + ' new API methods');
    console.log('[ShelfAPI] Final api methods:', Object.keys(window.auroraview.api));
}})();
"""

        try:
            # Try different methods to execute JS
            if hasattr(webview, "eval_js"):
                webview.eval_js(js_code)
                logger.info(f"Injected JS for {len(method_names)} API methods via eval_js")
            elif hasattr(webview, "evaluate"):
                webview.evaluate(js_code)
                logger.info(f"Injected JS for {len(method_names)} API methods via evaluate")
            elif hasattr(webview, "page") and hasattr(webview.page(), "runJavaScript"):
                webview.page().runJavaScript(js_code)
                logger.info(f"Injected JS for {len(method_names)} API methods via runJavaScript")
            else:
                logger.warning("No JS execution method available on webview")
        except Exception as e:
            logger.warning(f"Failed to inject API methods JS: {e}")
            import traceback

            logger.warning(traceback.format_exc())

    def _notify_api_ready(self) -> None:
        """Notify frontend that API is ready and trigger config reload.

        This dispatches a custom event that the frontend can listen to
        and use to reload the configuration after API registration.
        """
        webview = self._get_view_for_eval()
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
            # Debug: check webview type and methods
            logger.info(f"webview type: {type(webview).__name__}")
            public_methods = [m for m in dir(webview) if not m.startswith("_") and callable(getattr(webview, m, None))]
            logger.info(f"webview methods: {public_methods[:20]}")  # First 20 methods

            # Try different methods to execute JS
            if hasattr(webview, "eval_js"):
                logger.info("Using eval_js method...")
                webview.eval_js(js_code)
                logger.info("Notified frontend that API is ready")
            elif hasattr(webview, "evaluate"):
                logger.info("Using evaluate method...")
                webview.evaluate(js_code)
                logger.info("Notified frontend that API is ready (via evaluate)")
            elif hasattr(webview, "page") and hasattr(webview.page(), "runJavaScript"):
                logger.info("Using page().runJavaScript method...")
                webview.page().runJavaScript(js_code)
                logger.info("Notified frontend that API is ready (via runJavaScript)")
            else:
                logger.warning("webview does not have eval_js/evaluate/runJavaScript method")
        except Exception as e:
            logger.warning(f"Failed to notify API ready: {e}")
            import traceback

            logger.warning(traceback.format_exc())

    def _schedule_api_registration(self) -> None:
        """Schedule API registration after page load using QTimer.

        FIXED: Only schedule once instead of multiple times to prevent:
        - Redundant API re-registration
        - Frontend receiving multiple "API ready" events
        - Excessive IPC message queue buildup
        - UI freezing due to message processing overhead
        """
        from qtpy.QtCore import QTimer

        # Single delayed registration after page has time to load
        # 500ms is sufficient for most cases, and _api_registered flag
        # prevents duplicate registrations if called multiple times
        delay = 500
        QTimer.singleShot(delay, self._register_api_after_load)

        logger.debug(f"Scheduled single API registration at {delay}ms")

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
        if self._dialog and hasattr(self._dialog, "setWindowTitle"):
            # Only update if title is meaningful
            if title and title not in ("", "about:blank"):
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

    def _show_hwnd_mode(self, debug: bool, app: str) -> None:
        """Show using AuroraView with HWND integration (non-blocking).

        This mode creates a standalone WebView window in a background thread,
        freeing the DCC main thread for other operations.

        Architecture:
            Main Thread (DCC)    Background Thread (WebView)
            ----------------     ---------------------------
            |  app.show()   | -> |  WebView creation       |
            |  (returns)    |    |  API binding            |
            |               |    |  Event loop (blocking)  |
            |  DCC ops...   |    |  IPC handling           |
            ----------------     ---------------------------

        Best for: Unreal Engine, non-Qt applications, or when Qt mode
        causes issues with the DCC main thread.

        Args:
            debug: Enable DevTools for debugging.
            app: DCC application name (e.g., "maya", "unreal").
        """
        import threading

        logger.info("HWND mode - Starting WebView in background thread...")

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        # Initialize synchronization primitives for thread coordination
        self._hwnd_ready_event = threading.Event()

        # Create API (will be bound in background thread)
        self._api = ShelfAPI(self)

        def _create_webview_thread() -> None:
            """Create WebView in background thread (STA-compatible).

            This function runs entirely in the background thread:
            1. Creates WebView instance
            2. Binds API for IPC
            3. Loads content
            4. Runs event loop (blocking until window closes)
            """
            try:
                from auroraview import WebView

                logger.info("HWND thread - Creating WebView...")

                # Create WebView directly (not AuroraView wrapper)
                # The WebView manages its own event loop in this thread
                webview = WebView(
                    title=self._title,
                    width=self._width,
                    height=self._height,
                    debug=debug,
                    context_menu=debug,  # Enable context menu in debug mode
                    asset_root=dist_dir,
                )

                # Store WebView reference (for same-thread access only!)
                # WARNING: Do NOT call webview.eval_js() from main thread!
                self._webview = webview

                # Get thread-safe proxy for cross-thread JavaScript execution
                # Use self._webview_proxy.eval_js() from main DCC thread or other threads
                try:
                    self._webview_proxy = webview.get_proxy()
                    logger.info("HWND thread - WebViewProxy obtained for cross-thread access")
                except AttributeError:
                    # Fallback for older versions without get_proxy()
                    logger.warning("HWND thread - get_proxy() not available, " "cross-thread eval_js will not work!")
                    self._webview_proxy = None

                # Bind API - handlers will execute in this background thread
                logger.info("HWND thread - Binding API...")
                webview.bind_api(self._api)
                logger.info("HWND thread - API bound successfully")

                # Load content before showing
                if self._is_dev_mode():
                    dev_url = "http://localhost:5173"
                    logger.info(f"HWND thread - Loading dev URL: {dev_url}")
                    webview.load_url(dev_url)
                else:
                    index_path = DIST_DIR / "index.html"
                    if index_path.exists():
                        # Use auroraview:// custom protocol (asset_root was set above)
                        # Windows uses https://auroraview.localhost/ format
                        import sys

                        if sys.platform == "win32":
                            auroraview_url = "https://auroraview.localhost/index.html"
                        else:
                            auroraview_url = "auroraview://index.html"
                        logger.info(f"HWND thread - Loading via custom protocol: {auroraview_url}")
                        webview.load_url(auroraview_url)
                    else:
                        logger.error(f"HWND thread - index.html not found: {index_path}")

                # Setup shared state
                logger.info("HWND thread - Setting up shared state...")
                state = webview.state
                with state.batch_update() as batch:
                    batch["app_name"] = self._title
                    # Keep state key name for compatibility, but use the new
                    # internal flag to represent whether we are running in a
                    # DCC environment.
                    batch["dcc_mode"] = self._is_dcc_environment
                    batch["current_host"] = self._current_host
                    batch["theme"] = "dark"
                    batch["integration_mode"] = self._integration_mode

                # Use a flag to track if WebView is still running
                webview_running = threading.Event()
                webview_running.set()

                # Inject API methods after a short delay to ensure page is loaded
                # This is necessary because bind_api() is called before load_url(),
                # so the init script doesn't include API methods. We need to inject
                # them after the page loads and the event bridge is ready.
                def _delayed_api_injection() -> None:
                    """Inject API methods after page loads."""
                    import time

                    # Wait for page to load and event bridge to initialize
                    time.sleep(0.5)

                    # Check if WebView is still running before injecting
                    if not webview_running.is_set():
                        logger.info("HWND thread - WebView closed, skipping API injection")
                        return

                    logger.info("HWND thread - Injecting API methods...")
                    try:
                        self._inject_api_methods_js(webview)
                        logger.info("HWND thread - API methods injected successfully")
                    except Exception as e:
                        # Only log error if WebView is still supposed to be running
                        if webview_running.is_set():
                            logger.error(f"HWND thread - Failed to inject API methods: {e}")
                        else:
                            logger.debug(f"HWND thread - WebView closed during API injection: {e}")

                # Start injection in a separate thread to not block event loop
                injection_thread = threading.Thread(
                    target=_delayed_api_injection,
                    name="API-Injection",
                    daemon=True,
                )
                injection_thread.start()

                # Signal that WebView is ready
                self._hwnd_ready_event.set()
                logger.info("HWND thread - WebView ready, signaled main thread")

                logger.info("HWND thread - Starting WebView event loop (blocking this thread)...")

                # This blocks until the window is closed
                # The Rust event loop handles window messages and IPC
                webview.show_blocking()

                # Mark WebView as closed to stop any pending operations
                webview_running.clear()
                logger.info("HWND thread - WebView event loop exited, window closed")

            except Exception as e:
                logger.error(f"HWND thread - Error: {e}", exc_info=True)
                # Signal ready even on error to prevent main thread from waiting forever
                self._hwnd_ready_event.set()
            finally:
                # Ensure webview_running is cleared on any exit
                if "webview_running" in dir():
                    webview_running.clear()

        # Start WebView in background thread (daemon so it doesn't block app exit)
        self._webview_thread = threading.Thread(
            target=_create_webview_thread,
            name="AuroraView-HWND",
            daemon=True,
        )
        self._webview_thread.start()

        # Wait briefly for WebView to initialize (improves reliability)
        # This ensures the WebView is ready before returning to caller
        if self._hwnd_ready_event.wait(timeout=10.0):
            logger.info("HWND mode - WebView initialized successfully!")
        else:
            logger.warning("HWND mode - WebView initialization timeout, proceeding anyway...")

        logger.info("HWND mode - Background thread started, main thread free!")

    def _inject_api_methods_js(self, webview: Any) -> None:
        """Inject API method wrappers into JavaScript.

        This is called after page load to ensure the event bridge is ready.
        It creates window.auroraview.api.* methods that call Python handlers.

        Note: This method may be called from a different thread than the WebView
        was created on. It uses WebViewProxy for thread-safe JS execution.
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
            logger.warning("No API methods found to inject")
            return

        # Build JavaScript to register API methods
        methods_js = ", ".join(f"'{m}'" for m in api_methods)
        js_code = f"""
        (function() {{
            console.log('[AuroraView] Injecting API methods...');

            // Wait for event bridge to be ready
            function tryRegister() {{
                if (window.auroraview && window.auroraview._registerApiMethods) {{
                    window.auroraview._registerApiMethods('api', [{methods_js}]);
                    console.log('[AuroraView] API methods registered: {len(api_methods)} methods');
                    return true;
                }}
                return false;
            }}

            // Try immediately
            if (!tryRegister()) {{
                // Retry with polling
                var attempts = 0;
                var interval = setInterval(function() {{
                    attempts++;
                    if (tryRegister() || attempts > 50) {{
                        clearInterval(interval);
                        if (attempts > 50) {{
                            console.error('[AuroraView] Failed to register API methods after 50 attempts');
                        }}
                    }}
                }}, 100);
            }}
        }})();
        """

        try:
            # Use WebViewProxy for thread-safe cross-thread JS execution
            # This is crucial for HWND mode where this method is called from
            # the API-Injection thread, not the WebView thread
            if hasattr(self, "_webview_proxy") and self._webview_proxy is not None:
                self._webview_proxy.eval_js(js_code)
                logger.info(f"Injected {len(api_methods)} API methods via proxy: {api_methods}")
            else:
                # Fallback: try direct call (only safe if same thread)
                webview.eval_js(js_code)
                logger.info(f"Injected {len(api_methods)} API methods directly: {api_methods}")
        except Exception as e:
            logger.error(f"Failed to inject API methods: {e}")

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

    def _schedule_geometry_fixes(self) -> None:
        """Schedule geometry fixes for DCC apps (especially Nuke).

        Uses adapter's get_geometry_fix_delays() hook to get DCC-specific
        delay timings. Different DCCs may need different timing:
        - Maya: Standard delays work well
        - Nuke: Extended delays for custom window management
        - Houdini: Extended delays for Qt6 initialization
        """
        from qtpy.QtCore import QTimer
        from qtpy.QtWidgets import QApplication

        def force_geometry():
            if not self._dialog or not self._webview:
                return
            # Set dialog minimum size from config, not from current width/height
            # This prevents content clipping when Qt window decorations are present
            self._dialog.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])
            self._dialog.resize(self._width, self._height)
            # WebView should use config min size, not full window size
            self._webview.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])
            self._dialog.updateGeometry()
            self._webview.updateGeometry()

            # Force layout to recalculate (important for Qt6/PySide6)
            if self._layout:
                self._layout.activate()
                self._layout.update()

            # Force WebView container geometry if available
            if hasattr(self._webview, "_force_container_geometry"):
                self._webview._force_container_geometry()

            QApplication.processEvents()
            logger.debug(f"Forced geometry {self._width}x{self._height}")

        # Get DCC-specific geometry fix delays via hook
        delays = [100, 500, 1000, 2000]  # Default delays
        if self._adapter:
            delays = self._adapter.get_geometry_fix_delays()
            logger.debug(f"{self._adapter.name}: geometry_fix_delays={delays}")

        for delay in delays:
            QTimer.singleShot(delay, force_geometry)

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

        # Detect whether we are running inside a DCC host. This is true whenever
        # an `app` name is provided, regardless of whether Qt integration is
        # available. HWND mode does not require Qt at all, so gating this flag
        # on QT_AVAILABLE would incorrectly force DCC apps without Qt extras
        # (or with missing qtpy) into the standalone, blocking code path.
        is_dcc_host = bool(app)

        # Internal flag: whether we are running inside a DCC host. The exposed
        # state key remains "dcc_mode" for backward compatibility.
        self._is_dcc_environment = is_dcc_host
        logger.info(f"show() [8] Creating launcher, dcc_mode={self._is_dcc_environment}")
        self._launcher = ToolLauncher(self._config, dcc_mode=self._is_dcc_environment)
        logger.info("show() [9] Launcher created")

        # Use adapter's recommended mode if mode is default "qt"
        effective_mode = mode
        if mode == "qt" and self._adapter.recommended_mode != "qt":
            effective_mode = self._adapter.recommended_mode
        logger.info(f"show() [10] effective_mode={effective_mode}, " f"dcc_mode={self._is_dcc_environment}")

        # Branch by integration mode and environment. HWND mode is always safe
        # for DCC hosts (it does not depend on Qt), so we route to
        # _show_hwnd_mode whenever an app is provided and the effective mode is
        # "hwnd" – even if QT_AVAILABLE is False. This avoids falling back to
        # the standalone, blocking WebView.show() path in DCC environments.
        if is_dcc_host and effective_mode == "hwnd":
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
