"""Qt integration mode for DCC Shelves UI.

This module provides Qt-native widget integration for DCC applications
that support Qt (Maya, Houdini, Nuke, 3ds Max).

Anti-Flicker Strategy:
    The main challenge is that WebView2 initialization takes time (100-500ms),
    during which the dialog would show a white/empty background.

    Solution:
    1. Create dialog with dark background (LOADING_STYLE_QSS)
    2. Show dialog immediately (user sees dark background)
    3. Create WebView with deferred initialization
    4. Swap to WebView after loadFinished signal
    5. Apply final style (FLAT_STYLE_QSS)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from auroraview_dcc_shelves.constants import MAIN_WINDOW_CONFIG
from auroraview_dcc_shelves.styles import FLAT_STYLE_QSS, LOADING_STYLE_QSS
from auroraview_dcc_shelves.ui.modes.base import DIST_DIR, ModeMixin

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class QtModeMixin(ModeMixin):
    """Mixin for Qt widget integration mode.

    This mode creates a true Qt widget (QDialog) that can be managed
    by Qt's parent-child system. Best for Maya, Houdini, Nuke, 3ds Max.
    """

    # Expected attributes from ShelfApp
    _dialog: Any
    _layout: Any
    _placeholder: Any
    _auroraview: Any
    _title: str
    _width: int
    _height: int
    _default_width: int
    _default_height: int
    _adapter: Any

    def _show_qt_mode(self, debug: bool, app: str) -> None:
        """Show using QtWebView for Qt-native integration (non-blocking).

        This mode creates a true Qt widget that can be docked, embedded in
        layouts, and managed by Qt's parent-child system.

        Best for: Maya, Houdini, Nuke, 3ds Max
        """

        app_lower = app.lower()
        parent_window = self._get_dcc_parent_window(app)

        from qtpy.QtCore import Qt, QTimer
        from qtpy.QtWidgets import QApplication, QVBoxLayout, QWidget

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        self._dialog = QWidget(parent_window)
        self._dialog.setWindowTitle(self._title)
        self._dialog.setStyleSheet(LOADING_STYLE_QSS)
        # QWidget needs Qt.Window flag to be a top-level window
        self._dialog.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # Check device pixel ratio for DPI scaling
        qt_app = QApplication.instance()
        if qt_app:
            screen = qt_app.primaryScreen()
            if screen:
                device_pixel_ratio = screen.devicePixelRatio()
                logger.info(f"Device pixel ratio: {device_pixel_ratio}")

        # Set initial size
        self._dialog.resize(self._width, self._height)

        # Apply size constraints from config
        self._dialog.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])
        if MAIN_WINDOW_CONFIG["max_width"] > 0:
            self._dialog.setMaximumWidth(MAIN_WINDOW_CONFIG["max_width"])
        if MAIN_WINDOW_CONFIG["max_height"] > 0:
            self._dialog.setMaximumHeight(MAIN_WINDOW_CONFIG["max_height"])

        # Apply DCC-specific dialog configuration via hook
        if self._adapter:
            self._adapter.configure_dialog(self._dialog)
            logger.info(f"Applied {self._adapter.name} dialog configuration")

        self._layout = QVBoxLayout(self._dialog)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._dialog.show()
        logger.info("Qt mode - Dialog shown, deferring WebView initialization...")

        self._init_params = {"debug": debug, "app_lower": app_lower}

        # Use adapter-specific delay for WebView initialization
        init_delay = 10
        if self._adapter:
            init_delay = self._adapter.get_init_delay_ms()
            logger.info(f"{self._adapter.name}: init_delay={init_delay}ms")

        QTimer.singleShot(init_delay, self._init_webview_deferred_qt)

    def _init_webview_deferred_qt(self) -> None:
        """Initialize WebView in Qt mode (deferred)."""
        from auroraview import QtWebView

        debug = self._init_params["debug"]
        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        self._dialog.setStyleSheet(FLAT_STYLE_QSS)

        # Get the dialog's content rect (excludes window decorations)
        content_rect = self._dialog.contentsRect()
        dialog_rect = self._dialog.rect()
        frame_geometry = self._dialog.frameGeometry()
        geometry = self._dialog.geometry()

        logger.info("Dialog geometry debug:")
        logger.info(f"  - contentsRect: {content_rect.width()}x{content_rect.height()}")
        logger.info(f"  - rect: {dialog_rect.width()}x{dialog_rect.height()}")
        logger.info(f"  - frameGeometry: {frame_geometry.width()}x{frame_geometry.height()}")
        logger.info(f"  - geometry: {geometry.width()}x{geometry.height()}")
        logger.info(f"  - requested size: {self._width}x{self._height}")

        # Adjust for window decorations if needed
        if content_rect.width() < self._width or content_rect.height() < self._height:
            width_overhead = dialog_rect.width() - content_rect.width()
            height_overhead = dialog_rect.height() - content_rect.height()
            new_width = self._width + width_overhead
            new_height = self._height + height_overhead
            logger.info(f"  - adjusting dialog size: {new_width}x{new_height}")
            self._dialog.resize(new_width, new_height)
            content_rect = self._dialog.contentsRect()

        webview_width = content_rect.width() if content_rect.width() > 0 else self._width
        webview_height = content_rect.height() if content_rect.height() > 0 else self._height
        logger.info(f"  - final webview size: {webview_width}x{webview_height}")

        # CRITICAL: Always use "child" mode to prevent WebView from being dragged independently
        # "owner" mode allows the WebView to be moved separately from the Qt container
        embed_mode = "child"  # FORCED to "child" - do not change!
        logger.info(f"  - embed_mode: {embed_mode} (forced to child for proper embedding)")

        # Create WebView with deferred initialization
        # NOTE: The dcc_webview library handles visibility internally:
        # - Container mode creates window as invisible (with_visible=false in Rust)
        # - Anti-flicker optimizations are applied automatically
        self._placeholder = QtWebView.create_deferred(
            parent=self._dialog,
            width=webview_width,
            height=webview_height,
            dev_tools=debug,
            context_menu=debug,
            asset_root=dist_dir,
            embed_mode=embed_mode,
            on_ready=self._on_webview_ready_qt,
            on_error=self._on_webview_error,
        )
        self._layout.addWidget(self._placeholder)

    def _on_webview_ready_qt(self, webview: Any) -> None:
        """Called when QtWebView is ready.

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

        logger.info("Qt mode - WebView ready, completing initialization...")
        self._webview = webview
        self._webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._webview.setMinimumSize(MAIN_WINDOW_CONFIG["min_width"], MAIN_WINDOW_CONFIG["min_height"])

        # Ensure no borders on the WebView Qt widget itself
        self._webview.setStyleSheet("border: none; margin: 0; padding: 0;")
        self._webview.setContentsMargins(0, 0, 0, 0)

        # CRITICAL: Force WebView to be a proper child window to prevent independent dragging
        self._force_webview_child_style()

        # Also clean up Qt container's native window styles to remove any white borders
        self._force_qt_container_style()

        # Connect dialog resize event to sync WebView size
        self._connect_dialog_resize_handler()

        # Apply DCC-specific WebView configuration via hook
        if self._adapter:
            self._adapter.configure_webview(self._webview)
            logger.debug(f"Applied {self._adapter.name} WebView configuration")

        # Anti-flicker: Hide WebView initially, show after content loads
        self._webview.hide()
        self._layout.addWidget(self._webview)

        # Create API instance but defer binding to avoid blocking
        self._api = ShelfAPI(self)

        # Set _auroraview to _webview for compatibility with app.py methods
        self._auroraview = self._webview

        # Defer API binding to avoid blocking main thread
        def _deferred_bind_api() -> None:
            if hasattr(self._webview, "bind_api"):
                logger.info("Binding ShelfAPI to QtWebView (deferred)...")
                try:
                    self._webview.bind_api(self._api)
                    logger.info("ShelfAPI bound successfully")
                except Exception as e:
                    logger.warning(f"Failed to bind API: {e}")

        QTimer.singleShot(100, _deferred_bind_api)

        # Anti-flicker: Connect loadFinished to swap visibility
        self._placeholder_removed = False

        def _swap_to_webview(success: bool = True) -> None:
            """Swap from placeholder to WebView after content loads."""
            if self._placeholder_removed:
                return
            self._placeholder_removed = True

            logger.info(f"Qt mode - Content loaded (success={success}), swapping to WebView")

            # Small delay to allow first paint
            def _do_swap() -> None:
                if self._placeholder is not None:
                    self._placeholder.hide()
                    self._layout.removeWidget(self._placeholder)
                    self._placeholder.deleteLater()
                    self._placeholder = None

                self._webview.show()
                QApplication.processEvents()
                logger.info("Qt mode - Placeholder removed, WebView visible")

            QTimer.singleShot(50, _do_swap)

        # Connect loadFinished signal if available
        if hasattr(self._webview, "loadFinished"):
            self._webview.loadFinished.connect(_swap_to_webview)
        else:
            # Fallback: use timer if no loadFinished signal
            QTimer.singleShot(300, lambda: _swap_to_webview(True))

        # Load content first (this is async)
        self._load_content()

        # Defer all other initialization to avoid blocking main thread
        def _deferred_init_step1() -> None:
            """Connect Qt signals (non-blocking)."""
            try:
                self._connect_qt_signals()
                logger.debug("Step 1: Qt signals connected")
            except Exception as e:
                logger.warning(f"Step 1 failed: {e}")
            QTimer.singleShot(10, _deferred_init_step2)

        def _deferred_init_step2() -> None:
            """Register window events (non-blocking)."""
            try:
                self._register_window_events()
                logger.debug("Step 2: Window events registered")
            except Exception as e:
                logger.warning(f"Step 2 failed: {e}")
            QTimer.singleShot(10, _deferred_init_step3)

        def _deferred_init_step3() -> None:
            """Setup shared state (non-blocking)."""
            try:
                self._setup_shared_state()
                logger.debug("Step 3: Shared state setup")
            except Exception as e:
                logger.warning(f"Step 3 failed: {e}")
            QTimer.singleShot(10, _deferred_init_step4)

        def _deferred_init_step4() -> None:
            """Register commands (non-blocking)."""
            try:
                self._register_commands()
                logger.debug("Step 4: Commands registered")
            except Exception as e:
                logger.warning(f"Step 4 failed: {e}")
            QTimer.singleShot(10, _deferred_init_step5)

        def _deferred_init_step5() -> None:
            """Schedule geometry fixes and API registration (non-blocking)."""
            try:
                self._schedule_geometry_fixes()
                self._schedule_api_registration()
                logger.debug("Step 5: Geometry and API scheduled")
            except Exception as e:
                logger.warning(f"Step 5 failed: {e}")
            QTimer.singleShot(10, _deferred_init_final)

        def _deferred_init_final() -> None:
            """Call adapter's on_show hook (non-blocking)."""
            try:
                if self._adapter:
                    self._adapter.on_show(self)
                logger.info("Qt mode - WebView initialization complete!")
            except Exception as e:
                logger.warning(f"Final step failed: {e}")

        # Start deferred initialization chain
        QTimer.singleShot(50, _deferred_init_step1)

    def _force_webview_child_style(self) -> None:
        """Force WebView to be a proper child window.

        NOTE: This is now a no-op. The auroraview library handles all window
        style management in prepare_hwnd_for_container() (platforms/win.py).

        The Rust backend (native.rs) sets WS_CHILD style when embed_mode="child".
        Qt's createWindowContainer handles the parent-child relationship.
        """
        # No-op: auroraview library handles window styles
        pass

    def _force_qt_container_style(self) -> None:
        """Force Qt container widget to have no borders.

        NOTE: This is now a no-op. The auroraview library handles all window
        style management in prepare_hwnd_for_container() (platforms/win.py).
        """
        # No-op: auroraview library handles window styles
        pass

    def _connect_dialog_resize_handler(self) -> None:
        """Connect dialog resize event to sync WebView size.

        This ensures the WebView follows the main window when it's resized.
        The WebView should always fill the entire dialog content area.
        """
        if not self._dialog or not self._webview:
            return

        from qtpy.QtCore import QEvent, QObject

        class ResizeEventFilter(QObject):
            """Event filter to handle dialog resize events."""

            def __init__(self, dialog, webview, layout, parent=None):
                super().__init__(parent)
                self._dialog = dialog
                self._webview = webview
                self._layout = layout

            def eventFilter(self, watched, event):
                if watched == self._dialog and event.type() == QEvent.Resize:
                    # Sync WebView size with dialog content area
                    content_rect = self._dialog.contentsRect()
                    if content_rect.width() > 0 and content_rect.height() > 0:
                        # Force WebView to fill the content area
                        self._webview.setGeometry(content_rect)

                        # Also sync the internal container if available
                        if hasattr(self._webview, "_force_container_geometry"):
                            self._webview._force_container_geometry()

                        # Sync WebView2 controller bounds
                        if hasattr(self._webview, "_sync_webview2_controller_bounds"):
                            self._webview._sync_webview2_controller_bounds(content_rect.width(), content_rect.height())

                        logger.debug(
                            f"Dialog resized: WebView synced to {content_rect.width()}x{content_rect.height()}"
                        )

                return super().eventFilter(watched, event)

        # Create and install the event filter
        self._resize_event_filter = ResizeEventFilter(self._dialog, self._webview, self._layout, self._dialog)
        self._dialog.installEventFilter(self._resize_event_filter)
        logger.debug("Dialog resize event filter installed")
