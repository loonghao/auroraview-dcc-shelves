"""Base DCC Adapter interface.

This module defines the abstract base class for DCC adapters and provides
a registry system for adapter lookup.

Hook System Architecture:
    DCCAdapter provides a set of hooks that can be overridden by each DCC
    to customize behavior at various lifecycle stages:

    Lifecycle Hooks:
        - on_init: Called when ShelfApp initializes
        - on_show: Called after window is shown
        - on_close: Called when window is closed

    Window Creation Hooks:
        - create_dialog: Create and configure QDialog for the shelf
        - setup_dialog_layout: Setup layout for the dialog
        - get_window_flags: Return Qt window flags for the dialog

    WebView Hooks:
        - create_webview: Create WebView instance with DCC-specific settings
        - configure_webview: Customize WebView after creation
        - get_webview_params: Return WebView creation parameters
        - on_webview_ready: Called when WebView is ready

    Qt Dialog Hooks:
        - configure_dialog: Customize QDialog properties before show
        - get_init_delay_ms: Return initialization delay for deferred loading

    Performance Hooks:
        - apply_qt_optimizations: Apply Qt version-specific optimizations
        - get_geometry_fix_delays: Return delays for geometry fix timers

    Content Loading Hooks:
        - get_content_url: Return URL to load in WebView
        - on_content_loaded: Called when content is loaded

    This allows each DCC to handle its specific requirements:
        - Maya/Nuke (PySide2/Qt5): Faster initialization, standard settings
        - Houdini (PySide6/Qt6): Longer delays, opaque window optimizations
        - Unreal (HWND mode): No Qt hooks needed
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qtpy.QtWidgets import QDialog, QWidget

logger = logging.getLogger(__name__)

# Registry of DCC adapters
_ADAPTER_REGISTRY: dict[str, type[DCCAdapter]] = {}


@dataclass
class QtConfig:
    """Qt-specific configuration for a DCC adapter.

    This dataclass holds all Qt-related settings that can differ
    between DCCs, especially between PySide2 (Qt5) and PySide6 (Qt6).
    """

    # Initialization delay before WebView creation (ms)
    init_delay_ms: int = 10

    # Timer interval for UI updates (ms)
    timer_interval_ms: int = 16  # 60 FPS default

    # Geometry fix delays (ms) - applied after dialog.show()
    geometry_fix_delays: list[int] = field(default_factory=lambda: [])  # Disabled for testing

    # Whether to force opaque window (helps Qt6 performance)
    force_opaque_window: bool = False

    # Whether to disable translucent background
    disable_translucent: bool = False

    # Whether this DCC uses Qt6 (PySide6)
    is_qt6: bool = False

    # Whether to use native window appearance (Qt.Window) instead of tool window (Qt.Tool)
    # Qt.Tool: Smaller title bar, stays on top of parent, no taskbar icon
    # Qt.Window: Standard title bar, can be moved independently, has taskbar icon
    use_native_window: bool = False


def _detect_qt6() -> bool:
    """Detect if the current Qt binding is Qt6.

    Uses qtpy's API to detect Qt version:
    - QT_VERSION: e.g., "5.15.2" or "6.5.0"
    - API_NAME: e.g., "PySide2", "PySide6", "PyQt5", "PyQt6"

    Returns:
        True if Qt6 (PySide6 or PyQt6), False otherwise.
    """
    try:
        from qtpy import API_NAME, QT_VERSION

        # Check API_NAME first (more reliable)
        if API_NAME in ("PySide6", "PyQt6"):
            return True

        # Fallback to version string check
        if QT_VERSION and QT_VERSION.startswith("6"):
            return True

        return False
    except Exception:
        return False


class DCCAdapter(ABC):
    """Abstract base class for DCC application adapters.

    Each DCC application should have its own adapter that implements
    application-specific functionality like window management and
    performance settings.

    Attributes:
        name: Display name of the DCC application.
        aliases: Alternative names for this DCC (e.g., "max" for "3dsmax").
        timer_interval_ms: Recommended timer interval for UI updates.
        recommended_mode: Recommended integration mode ("qt" or "hwnd").
    """

    name: str = "Unknown"
    aliases: list[str] = []
    timer_interval_ms: int = 16  # 60 FPS default
    recommended_mode: str = "qt"

    def __init__(self) -> None:
        """Initialize the adapter with Qt configuration."""
        self._qt_config: QtConfig | None = None

    @property
    def qt_config(self) -> QtConfig:
        """Get Qt configuration, initializing if needed.

        This is lazily initialized to allow detection of Qt version
        at runtime.
        """
        if self._qt_config is None:
            self._qt_config = self._create_qt_config()
        return self._qt_config

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for this DCC.

        Override this method to provide DCC-specific Qt settings.
        The base implementation detects Qt version and applies defaults.

        Returns:
            QtConfig with appropriate settings for this DCC.
        """
        is_qt6 = _detect_qt6()

        return QtConfig(
            init_delay_ms=10,
            timer_interval_ms=self.timer_interval_ms,
            is_qt6=is_qt6,
        )

    @abstractmethod
    def get_main_window(self) -> Any | None:
        """Get the DCC main window as a QWidget.

        Returns:
            The main window QWidget, or None if not found.
        """
        pass

    # ========================================
    # Lifecycle Hooks
    # ========================================

    def on_init(self, shelf_app: Any) -> None:
        """Called when ShelfApp initializes for this DCC.

        Override to perform DCC-specific initialization.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    def on_show(self, shelf_app: Any) -> None:
        """Called after the shelf window is shown.

        Override to perform DCC-specific post-show setup.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    def on_close(self, shelf_app: Any) -> None:
        """Called when the shelf window is closed.

        Override to perform DCC-specific cleanup.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    # ========================================
    # Qt Dialog Hooks
    # ========================================

    def configure_dialog(self, dialog: QDialog, use_native_window: bool | None = None) -> None:
        """Configure QDialog before it is shown.

        This hook is called after the dialog is created but before show().
        Use it to apply DCC-specific window attributes or styles.

        Args:
            dialog: The QDialog instance to configure.
            use_native_window: If True, use Qt.Window instead of Qt.Tool for
                native window appearance. If None, uses the value from QtConfig.
                Default is None (uses QtConfig.use_native_window).
        """
        config = self.qt_config

        if not config.is_qt6:
            return

        # Apply Qt6-specific optimizations
        try:
            from qtpy.QtCore import Qt

            logger.debug(f"{self.name}: Applying Qt6 dialog optimizations")

            if config.force_opaque_window:
                # Disable auto fill background for opaque rendering
                dialog.setAutoFillBackground(False)
                # NOTE: Do NOT set WA_OpaquePaintEvent on dialogs containing WebView!
                # This causes black screen because Qt assumes the widget paints its
                # entire background, but WebView container needs transparency.
                dialog.setAttribute(Qt.WA_NoSystemBackground, False)

            if config.disable_translucent:
                dialog.setAttribute(Qt.WA_TranslucentBackground, False)
                dialog.repaint()  # Force repaint after transparency change

        except Exception as e:
            logger.debug(f"{self.name}: Failed to apply dialog config: {e}")

    def configure_webview(self, webview: QWidget) -> None:
        """Configure WebView widget after creation.

        This hook is called after the WebView is created and added
        to the layout. Use it to apply DCC-specific WebView settings.

        Args:
            webview: The WebView widget (QtWebView wrapper).
        """
        pass

    def set_transparency(self, widget: QWidget, enabled: bool) -> None:
        """Set UI transparency on a widget.

        Dynamically toggle transparency on/off for a Qt widget.
        Useful for switching between opaque and transparent modes at runtime.

        Args:
            widget: The Qt widget to configure.
            enabled: True to enable transparency, False for opaque.
        """
        try:
            from qtpy.QtCore import Qt

            if enabled:
                widget.setAutoFillBackground(False)
            else:
                widget.setAttribute(Qt.WA_NoSystemBackground, False)

            widget.setAttribute(Qt.WA_TranslucentBackground, enabled)
            widget.repaint()

            logger.debug(f"{self.name}: Set transparency={enabled} on {widget.__class__.__name__}")
        except Exception as e:
            logger.debug(f"{self.name}: Failed to set transparency: {e}")

    def get_init_delay_ms(self) -> int:
        """Get initialization delay for deferred WebView creation.

        Returns:
            Delay in milliseconds before WebView initialization.
        """
        return self.qt_config.init_delay_ms

    def get_geometry_fix_delays(self) -> list[int]:
        """Get delays for geometry fix timers.

        Some DCCs (especially Nuke) need delayed geometry fixes
        to ensure proper window sizing.

        Returns:
            List of delays in milliseconds.
        """
        return self.qt_config.geometry_fix_delays

    # ========================================
    # Performance Hooks
    # ========================================

    def apply_qt_optimizations(self) -> None:
        """Apply Qt-specific performance optimizations.

        Called during initialization to apply DCC-specific
        Qt optimizations (e.g., disabling animations in Qt6).
        """
        pass

    # ========================================
    # Window Creation Hooks
    # ========================================

    def get_window_flags(self) -> Any:
        """Get Qt window flags for the dialog.

        Override to customize window flags for specific DCC requirements.
        For example, Houdini uses Qt.Tool to keep window attached to parent.

        Returns:
            Qt.WindowFlags or None to use default.
        """
        return None

    def create_dialog(
        self,
        parent: QWidget | None,
        title: str,
        width: int,
        height: int,
        frameless: bool = False,
    ) -> QDialog | None:
        """Create and configure QDialog for the shelf.

        Override to create DCC-specific dialog with custom settings.
        Return None to use default dialog creation.

        Args:
            parent: Parent widget (usually DCC main window).
            title: Window title.
            width: Initial width.
            height: Initial height.
            frameless: Whether to create frameless window.

        Returns:
            Configured QDialog, or None to use default.
        """
        return None

    def setup_dialog_layout(self, dialog: QDialog) -> Any:
        """Setup layout for the dialog.

        Override to create DCC-specific layout configuration.
        Return None to use default layout.

        Args:
            dialog: The QDialog to setup layout for.

        Returns:
            QLayout instance, or None to use default.
        """
        return None

    # ========================================
    # WebView Hooks
    # ========================================

    def get_webview_params(self, debug: bool = False) -> dict[str, Any]:
        """Get WebView creation parameters.

        Override to customize WebView creation for specific DCC.

        Args:
            debug: Whether debug mode is enabled.

        Returns:
            Dictionary of WebView creation parameters.
        """
        return {
            "dev_tools": debug,
            "context_menu": debug,
        }

    def create_webview(
        self,
        parent: QWidget,
        debug: bool = False,
        asset_root: str | None = None,
    ) -> QWidget | None:
        """Create WebView instance with DCC-specific settings.

        Override to create custom WebView configuration.
        Return None to use default WebView creation.

        Args:
            parent: Parent widget for the WebView.
            debug: Whether debug mode is enabled.
            asset_root: Root directory for assets.

        Returns:
            WebView widget, or None to use default.
        """
        return None

    def on_webview_ready(self, shelf_app: Any, webview: QWidget) -> None:
        """Called when WebView is ready and content is loaded.

        Override to perform DCC-specific setup after WebView is ready.

        Args:
            shelf_app: The ShelfApp instance.
            webview: The WebView widget.
        """
        pass

    # ========================================
    # Content Loading Hooks
    # ========================================

    def get_content_url(self, is_dev_mode: bool) -> str | None:
        """Get URL to load in WebView.

        Override to customize content URL for specific DCC.
        Return None to use default URL.

        Args:
            is_dev_mode: Whether running in development mode.

        Returns:
            URL string, or None to use default.
        """
        return None

    def on_content_loaded(self, shelf_app: Any) -> None:
        """Called when content is loaded in WebView.

        Override to perform DCC-specific setup after content loads.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    # ========================================
    # Dockable Hooks
    # ========================================

    def supports_dockable(self) -> bool:
        """Check if this DCC supports dockable panels.

        Override to return True if the DCC has native docking support.
        When True, show_dockable() will be called instead of creating
        a standalone QDialog.

        Returns:
            True if dockable panels are supported, False otherwise.
        """
        return False

    def create_dockable_widget(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a dockable panel containing the given widget.

        This method is called when dockable=True is passed to show().
        Override to implement DCC-specific docking behavior.

        Args:
            widget: The QWidget to embed in the dockable panel.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel (used for state persistence).

        Returns:
            The dockable container (DCC-specific type), or None if failed.

        Example implementations:
            - Maya: Use MayaQWidgetDockableMixin or workspaceControl
            - Nuke: Use nukescripts.panels.registerWidgetAsPanel()
            - Houdini: Use hou.PythonPanel interface
        """
        logger.warning(
            f"{self.name}: Dockable panels not implemented. Override create_dockable_widget() to add support."
        )
        return None

    def show_dockable(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
        **kwargs: Any,
    ) -> bool:
        """Show a widget as a dockable panel in the DCC.

        This is the main entry point for dockable panel creation.
        Override to implement DCC-specific show behavior.

        Args:
            widget: The QWidget to show as dockable.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.
            **kwargs: Additional DCC-specific options.

        Returns:
            True if the dockable panel was created successfully.
        """
        dockable = self.create_dockable_widget(widget, title, object_name)
        return dockable is not None

    def restore_dockable(self, object_name: str) -> bool:
        """Restore a previously created dockable panel.

        Some DCCs (like Maya) require special handling to restore
        dockable panels after scene reload or restart.

        Args:
            object_name: The unique object name of the panel to restore.

        Returns:
            True if the panel was restored successfully.
        """
        return False

    def close_dockable(self, object_name: str) -> bool:
        """Close and cleanup a dockable panel.

        Args:
            object_name: The unique object name of the panel to close.

        Returns:
            True if the panel was closed successfully.
        """
        return False

    # ========================================
    # API Hooks
    # ========================================

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Return additional API methods to expose to JavaScript.

        Override to add DCC-specific API methods.

        Returns:
            Dictionary of method_name -> callable.
        """
        return {}


class GenericAdapter(DCCAdapter):
    """Generic adapter for unknown DCC applications."""

    name = "Generic"
    timer_interval_ms = 16

    def __init__(self) -> None:
        """Initialize the generic adapter."""
        super().__init__()

    def get_main_window(self) -> Any | None:
        """Get active window from Qt application."""
        try:
            from qtpy.QtWidgets import QApplication

            app = QApplication.instance()
            return app.activeWindow() if app else None
        except ImportError:
            return None


def register_adapter(adapter_class: type[DCCAdapter]) -> type[DCCAdapter]:
    """Register a DCC adapter class.

    This can be used as a decorator:
        @register_adapter
        class MyDCCAdapter(DCCAdapter):
            name = "MyDCC"
            ...

    Args:
        adapter_class: The adapter class to register.

    Returns:
        The same adapter class (for decorator use).
    """
    key = adapter_class.name.lower()
    _ADAPTER_REGISTRY[key] = adapter_class

    # Also register aliases
    for alias in adapter_class.aliases:
        _ADAPTER_REGISTRY[alias.lower()] = adapter_class

    logger.debug(f"Registered DCC adapter: {adapter_class.name}")
    return adapter_class


def get_adapter(app_name: str | None) -> DCCAdapter:
    """Get the appropriate adapter for a DCC application.

    Args:
        app_name: Name of the DCC application (case-insensitive).
            If None or empty, returns a generic adapter.

    Returns:
        An instance of the appropriate DCCAdapter.
    """
    if not app_name:
        return GenericAdapter()

    key = app_name.lower()
    adapter_class = _ADAPTER_REGISTRY.get(key)

    if adapter_class:
        return adapter_class()

    logger.warning(f"No adapter found for '{app_name}', using generic adapter")
    return GenericAdapter()


# Auto-import all adapters to trigger registration
def _load_adapters() -> None:
    """Load all adapter modules to register them."""
    from . import (  # noqa: F401  # noqa: F401
        blender,
        desktop,
        houdini,
        max3ds,
        maya,
        nuke,
        substance_designer,
        substance_painter,
        unreal,
    )


# Lazy loading - adapters are loaded on first get_adapter call
_adapters_loaded = False


def _ensure_adapters_loaded() -> None:
    """Ensure all adapters are loaded."""
    global _adapters_loaded
    if not _adapters_loaded:
        _load_adapters()
        _adapters_loaded = True


# Patch get_adapter to ensure adapters are loaded
_original_get_adapter = get_adapter


def get_adapter(app_name: str | None) -> DCCAdapter:  # noqa: F811
    """Get the appropriate adapter for a DCC application."""
    _ensure_adapters_loaded()
    return _original_get_adapter(app_name)
