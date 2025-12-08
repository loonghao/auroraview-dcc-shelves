"""Dockable panel integration mode for DCC Shelves UI.

This module provides dockable panel integration for DCC applications
that support native docking (Maya workspaceControl, Nuke panels, etc.).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from auroraview_dcc_shelves.constants import MAIN_WINDOW_CONFIG
from auroraview_dcc_shelves.ui.modes.base import DIST_DIR, ModeMixin

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DockableModeMixin(ModeMixin):
    """Mixin for dockable panel integration mode.

    This mode creates a native dockable panel that can be docked into
    the DCC's panel system (Maya workspaceControl, Nuke panels, etc.).
    """

    # Expected attributes from ShelfApp
    _dockable_container: Any
    _layout: Any
    _placeholder: Any
    _auroraview: Any
    _title: str
    _width: int
    _height: int
    _default_width: int
    _default_height: int
    _adapter: Any

    def _show_dockable_mode(self, debug: bool, app: str) -> None:
        """Show as a dockable panel in the DCC application.

        This mode creates a native dockable panel that can be docked
        into the DCC's panel system (Maya workspaceControl, Nuke panels,
        Houdini Python Panels).

        Best for: Maya, Houdini, Nuke when native docking is desired.
        """
        if not self._adapter or not self._adapter.supports_dockable():
            logger.warning(f"Dockable mode not supported for {app}. Falling back to Qt mode.")
            return self._show_qt_mode(debug, app)

        app_lower = app.lower()

        from qtpy.QtCore import QTimer
        from qtpy.QtWidgets import QVBoxLayout, QWidget

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        # Create a container widget for the WebView
        self._dockable_container = QWidget()
        self._dockable_container.setObjectName(f"auroraview_shelf_{app_lower}")
        self._dockable_container.resize(self._width, self._height)
        self._dockable_container.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])

        self._layout = QVBoxLayout(self._dockable_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Store params for deferred initialization
        self._init_params = {"debug": debug, "app_lower": app_lower}

        # Use adapter's show_dockable to create the dockable panel
        object_name = f"auroraview_shelf_{app_lower}"
        success = self._adapter.show_dockable(
            widget=self._dockable_container,
            title=self._title,
            object_name=object_name,
        )

        if success:
            logger.info(f"Dockable mode - Panel created for {app}")
            init_delay = self._adapter.get_init_delay_ms()
            QTimer.singleShot(init_delay, self._init_webview_deferred_dockable)
        else:
            logger.warning(f"Failed to create dockable panel for {app}. Falling back to Qt mode.")
            self._dockable_container.deleteLater()
            self._dockable_container = None
            return self._show_qt_mode(debug, app)

    def _init_webview_deferred_dockable(self) -> None:
        """Initialize WebView in dockable mode (deferred)."""
        from auroraview import QtWebView

        debug = self._init_params["debug"]
        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        # Get container size
        container_rect = self._dockable_container.contentsRect()
        webview_width = container_rect.width() if container_rect.width() > 0 else self._width
        webview_height = container_rect.height() if container_rect.height() > 0 else self._height

        logger.info(f"Dockable mode - Creating WebView: {webview_width}x{webview_height}")

        # CRITICAL: Always use "child" mode to prevent WebView from being dragged independently
        # "owner" mode allows the WebView to be moved separately from the Qt container
        embed_mode = "child"  # FORCED to "child" - do not change!
        logger.info(f"  - embed_mode: {embed_mode} (forced to child for proper embedding)")

        # Try to create with visible=False to prevent white flash
        try:
            self._placeholder = QtWebView.create_deferred(
                parent=self._dockable_container,
                width=webview_width,
                height=webview_height,
                dev_tools=debug,
                context_menu=debug,
                asset_root=dist_dir,
                embed_mode=embed_mode,
                visible=False,  # Prevent white flash during initialization
                on_ready=self._on_webview_ready_dockable,
                on_error=self._on_webview_error,
            )
        except TypeError as e:
            # Fallback if visible parameter is not supported
            if "visible" in str(e):
                logger.warning("QtWebView.create_deferred doesn't support 'visible', retrying without it")
                self._placeholder = QtWebView.create_deferred(
                    parent=self._dockable_container,
                    width=webview_width,
                    height=webview_height,
                    dev_tools=debug,
                    context_menu=debug,
                    asset_root=dist_dir,
                    embed_mode=embed_mode,
                    on_ready=self._on_webview_ready_dockable,
                    on_error=self._on_webview_error,
                )
            else:
                raise
        self._layout.addWidget(self._placeholder)

    def _on_webview_ready_dockable(self, webview: Any) -> None:
        """Called when QtWebView is ready in dockable mode.

        Note: We use QtWebView directly without wrapping in AuroraView.
        AuroraView is designed for non-Qt applications (Unreal Engine).
        For Qt-based DCC apps, QtWebView provides all needed functionality.

        Anti-flicker strategy:
        1. Keep placeholder visible while WebView loads content
        2. Hide WebView initially
        3. Swap visibility after loadFinished + render delay
        """
        from qtpy.QtCore import QTimer
        from qtpy.QtWidgets import QApplication, QSizePolicy

        from auroraview_dcc_shelves.ui.api import ShelfAPI

        logger.info("Dockable mode - WebView ready, completing initialization...")
        self._webview = webview
        self._webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._webview.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])

        # CRITICAL: Force WebView to be a proper child window to prevent independent dragging
        self._force_webview_child_style_dockable()

        # Apply DCC-specific WebView configuration via hook
        if self._adapter:
            self._adapter.configure_webview(self._webview)
            logger.debug(f"Applied {self._adapter.name} WebView configuration")

        # Anti-flicker: Hide WebView initially, show after content loads
        self._webview.hide()
        self._layout.addWidget(self._webview)

        # Bind API directly to QtWebView
        self._api = ShelfAPI(self)
        if hasattr(self._webview, "bind_api"):
            logger.info("Binding ShelfAPI to QtWebView (dockable)...")
            self._webview.bind_api(self._api)
            logger.info("ShelfAPI bound successfully (dockable)")

        # Set _auroraview to _webview for compatibility with app.py methods
        self._auroraview = self._webview

        # Anti-flicker: Connect loadFinished to swap visibility
        self._placeholder_removed = False

        def _swap_to_webview(success: bool = True) -> None:
            """Swap from placeholder to WebView after content loads."""
            if self._placeholder_removed:
                return
            self._placeholder_removed = True

            logger.info(f"Dockable mode - Content loaded (success={success}), swapping to WebView")

            def _do_swap() -> None:
                if self._placeholder is not None:
                    self._placeholder.hide()
                    self._layout.removeWidget(self._placeholder)
                    self._placeholder.deleteLater()
                    self._placeholder = None

                self._webview.show()
                QApplication.processEvents()
                logger.info("Dockable mode - Placeholder removed, WebView visible")

            QTimer.singleShot(50, _do_swap)

        # Connect loadFinished signal if available
        if hasattr(self._webview, "loadFinished"):
            self._webview.loadFinished.connect(_swap_to_webview)
        else:
            QTimer.singleShot(300, lambda: _swap_to_webview(True))

        # Connect Qt signals for navigation events
        self._connect_qt_signals()

        self._load_content()
        self._register_window_events()
        self._setup_shared_state()
        self._register_commands()

        # Schedule API re-registration after page load
        self._schedule_api_registration()

        # Call adapter's on_show hook
        if self._adapter:
            self._adapter.on_show(self)

        logger.info("Dockable mode - WebView initialization complete!")

    def _force_webview_child_style_dockable(self) -> None:
        """Force WebView to be a proper child window.

        NOTE: This is now a no-op. The auroraview library handles all window
        style management in prepare_hwnd_for_container() (platforms/win.py).

        The Rust backend (native.rs) sets WS_CHILD style when embed_mode="child".
        Qt's createWindowContainer handles the parent-child relationship.
        """
        # No-op: auroraview library handles window styles
        pass
