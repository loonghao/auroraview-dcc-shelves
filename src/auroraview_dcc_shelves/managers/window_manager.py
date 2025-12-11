"""Window Manager for ShelfApp.

This module handles window creation and configuration for different modes:
- Qt mode: QWidget with QtWebView (uses QWidget instead of QDialog to avoid border issues)
- Dockable mode: DCC-specific dockable panels
- HWND mode: Standalone WebView window

The WindowManager delegates DCC-specific behavior to the adapter's hooks.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qtpy.QtWidgets import QDialog, QVBoxLayout, QWidget

    from auroraview_dcc_shelves.apps.base import DCCAdapter

logger = logging.getLogger(__name__)


class WindowManager:
    """Manages window creation and configuration for ShelfApp.

    This class encapsulates all window-related logic, delegating
    DCC-specific behavior to the adapter's hooks.

    Attributes:
        adapter: The DCC adapter for DCC-specific behavior.
        dialog: The QWidget instance (Qt mode).
        layout: The layout for the dialog.
        dockable_container: Container widget for dockable mode.
    """

    def __init__(self, adapter: DCCAdapter | None = None) -> None:
        """Initialize the WindowManager.

        Args:
            adapter: DCC adapter for DCC-specific behavior.
        """
        self._adapter = adapter
        self._dialog: QWidget | None = None
        self._layout: QVBoxLayout | None = None
        self._dockable_container: QWidget | None = None

    @property
    def dialog(self) -> QWidget | None:
        """Get the dialog instance."""
        return self._dialog

    @property
    def layout(self) -> QVBoxLayout | None:
        """Get the layout instance."""
        return self._layout

    @property
    def dockable_container(self) -> QWidget | None:
        """Get the dockable container widget."""
        return self._dockable_container

    def set_adapter(self, adapter: DCCAdapter) -> None:
        """Set the DCC adapter.

        Args:
            adapter: DCC adapter for DCC-specific behavior.
        """
        self._adapter = adapter

    def create_qt_dialog(
        self,
        parent: QWidget | None,
        title: str,
        width: int,
        height: int,
        min_width: int,
        min_height: int,
        max_width: int = 0,
        max_height: int = 0,
        frameless: bool = False,
        style_sheet: str = "",
        start_hidden: bool = True,
    ) -> QWidget:
        """Create and configure a QWidget for Qt mode.

        Uses QWidget instead of QDialog to avoid white border issues
        that can occur with QDialog in some Qt versions.

        First tries the adapter's create_dialog hook. If it returns None,
        creates a default QWidget.

        Args:
            parent: Parent widget (usually DCC main window).
            title: Window title.
            width: Initial width.
            height: Initial height.
            min_width: Minimum width.
            min_height: Minimum height.
            max_width: Maximum width (0 = no limit).
            max_height: Maximum height (0 = no limit).
            frameless: Whether to create frameless window.
            style_sheet: CSS style sheet for the dialog.
            start_hidden: If True, dialog starts hidden to prevent white flash.

        Returns:
            Configured QWidget instance.
        """
        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QWidget

        # Try adapter's create_dialog hook first
        if self._adapter:
            dialog = self._adapter.create_dialog(
                parent=parent,
                title=title,
                width=width,
                height=height,
                frameless=frameless,
            )
            if dialog is not None:
                self._dialog = dialog
                # Ensure dialog starts hidden to prevent white flash
                if start_hidden:
                    self._dialog.setVisible(False)
                self._setup_dialog_layout(dialog)
                return dialog

        # Default widget creation - use QWidget instead of QDialog
        # to avoid white border issues in some Qt versions
        self._dialog = QWidget(parent)
        self._dialog.setWindowTitle(title)

        if style_sheet:
            self._dialog.setStyleSheet(style_sheet)

        # Set window flags - QWidget needs Qt.Window to be a top-level window
        # Use standard window flags with title bar and close button
        window_flags = Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        self._dialog.setWindowFlags(window_flags)

        # CRITICAL: Ensure the window is NOT transparent
        # This prevents the "see-through to desktop" issue in Qt6/Houdini
        self._dialog.setAttribute(Qt.WA_TranslucentBackground, False)
        self._dialog.setAttribute(Qt.WA_NoSystemBackground, False)
        self._dialog.setAutoFillBackground(True)

        # CRITICAL: Set dialog to not visible before any size operations
        # This prevents Qt from auto-showing the dialog when parent is set
        if start_hidden:
            self._dialog.setVisible(False)

        # Set size
        self._dialog.resize(width, height)
        self._dialog.setMinimumSize(min_width, min_height)
        if max_width > 0:
            self._dialog.setMaximumWidth(max_width)
        if max_height > 0:
            self._dialog.setMaximumHeight(max_height)

        # Apply DCC-specific dialog configuration via hook
        if self._adapter:
            self._adapter.configure_dialog(self._dialog)
            logger.info(f"Applied {self._adapter.name} dialog configuration")

        # Setup layout
        self._setup_dialog_layout(self._dialog)

        return self._dialog

    def _get_window_flags(self, frameless: bool) -> Any:
        """Get Qt window flags for the dialog.

        Args:
            frameless: Whether to create frameless window.

        Returns:
            Qt.WindowFlags value.
        """
        from qtpy.QtCore import Qt

        # Try adapter's get_window_flags hook first
        if self._adapter:
            flags = self._adapter.get_window_flags()
            if flags is not None:
                return flags

        # Default flags
        if frameless:
            return Qt.Window | Qt.FramelessWindowHint
        return Qt.Window

    def _setup_dialog_layout(self, dialog: QDialog) -> None:
        """Setup layout for the dialog.

        Args:
            dialog: The QDialog to setup layout for.
        """
        from qtpy.QtWidgets import QVBoxLayout

        # Try adapter's setup_dialog_layout hook first
        if self._adapter:
            layout = self._adapter.setup_dialog_layout(dialog)
            if layout is not None:
                self._layout = layout
                return

        # Default layout
        self._layout = QVBoxLayout(dialog)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def create_dockable_container(
        self,
        app_name: str,
        width: int,
        height: int,
        min_width: int,
        min_height: int,
    ) -> QWidget:
        """Create a container widget for dockable mode.

        Args:
            app_name: DCC application name.
            width: Initial width.
            height: Initial height.
            min_width: Minimum width.
            min_height: Minimum height.

        Returns:
            Container QWidget for the dockable panel.
        """
        from qtpy.QtWidgets import QVBoxLayout, QWidget

        self._dockable_container = QWidget()
        self._dockable_container.setObjectName(f"auroraview_shelf_{app_name.lower()}")
        self._dockable_container.resize(width, height)
        self._dockable_container.setMinimumSize(min_width, min_height)

        self._layout = QVBoxLayout(self._dockable_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        return self._dockable_container

    def show_dialog(self) -> None:
        """Show the dialog."""
        if self._dialog:
            self._dialog.show()
            logger.info("Dialog shown")

    def show_dockable(
        self,
        title: str,
        object_name: str,
        **kwargs: Any,
    ) -> bool:
        """Show the dockable container as a dockable panel.

        Args:
            title: Panel title.
            object_name: Unique object name for the panel.
            **kwargs: Additional DCC-specific options.

        Returns:
            True if successful, False otherwise.
        """
        if not self._adapter or not self._dockable_container:
            logger.warning("Cannot show dockable: adapter or container not set")
            return False

        return self._adapter.show_dockable(
            widget=self._dockable_container,
            title=title,
            object_name=object_name,
            **kwargs,
        )

    def get_content_rect(self) -> tuple[int, int]:
        """Get the content rect size of the dialog or container.

        Returns:
            Tuple of (width, height) for the content area.
        """
        if self._dialog:
            rect = self._dialog.contentsRect()
            return rect.width(), rect.height()
        if self._dockable_container:
            rect = self._dockable_container.contentsRect()
            return rect.width(), rect.height()
        return 0, 0

    def adjust_dialog_for_content(self, target_width: int, target_height: int) -> None:
        """Adjust dialog size to ensure content area matches target size.

        Args:
            target_width: Target content width.
            target_height: Target content height.
        """
        if not self._dialog:
            return

        content_rect = self._dialog.contentsRect()
        dialog_rect = self._dialog.rect()

        if content_rect.width() < target_width or content_rect.height() < target_height:
            width_overhead = dialog_rect.width() - content_rect.width()
            height_overhead = dialog_rect.height() - content_rect.height()
            new_width = target_width + width_overhead
            new_height = target_height + height_overhead
            logger.info(
                f"Adjusting dialog size: {new_width}x{new_height} (overhead: {width_overhead}x{height_overhead})"
            )
            self._dialog.resize(new_width, new_height)

    def add_widget_to_layout(self, widget: QWidget) -> None:
        """Add a widget to the layout.

        Args:
            widget: Widget to add.
        """
        if self._layout:
            self._layout.addWidget(widget)

    def remove_widget_from_layout(self, widget: QWidget) -> None:
        """Remove a widget from the layout.

        Args:
            widget: Widget to remove.
        """
        if self._layout:
            self._layout.removeWidget(widget)

    def set_dialog_style(self, style_sheet: str) -> None:
        """Set the dialog style sheet.

        Args:
            style_sheet: CSS style sheet.
        """
        if self._dialog:
            self._dialog.setStyleSheet(style_sheet)

    def cleanup(self) -> None:
        """Cleanup window resources."""
        if self._dialog:
            self._dialog.close()
            self._dialog = None
        if self._dockable_container:
            self._dockable_container.close()
            self._dockable_container = None
        self._layout = None
