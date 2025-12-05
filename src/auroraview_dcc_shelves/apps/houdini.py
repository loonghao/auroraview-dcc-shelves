"""Houdini DCC Adapter.

Handles Houdini-specific integration including:
- Main window detection via hou.qt module
- Longer timer intervals for heavy cooking/VEX operations
- Special handling for Houdini's threaded architecture
- PySide6 (Qt6) specific optimizations
- Dockable panel support via hou.pypanel

Qt Version Notes:
    Houdini uses PySide6 (Qt6). Qt version is detected dynamically
    using qtpy's API for consistency with other adapters.

Qt6 Performance Considerations:
    - Higher initialization overhead
    - Semi-transparent windows are significantly slower
    - createWindowContainer has stricter handling
    - Event system was rewritten

    This adapter applies Qt6-specific optimizations via the hook system.

Dockable Support:
    Houdini supports dockable panels via Python Panel interfaces.
    Panels can be registered and shown in Houdini's pane system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, QtConfig, _detect_qt6, register_adapter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QDialog, QWidget

logger = logging.getLogger(__name__)

# Global registry for panel widgets
_PANEL_WIDGETS: dict[str, QWidget] = {}


@register_adapter
class HoudiniAdapter(DCCAdapter):
    """Adapter for SideFX Houdini.

    Houdini-specific optimizations:
    - Longer timer interval (50ms) for heavy cooking operations
    - Extended init delay (100ms) for Qt6 initialization
    - Force opaque window to avoid Qt6 transparency performance issues
    - Disable translucent background for faster rendering
    """

    name = "Houdini"
    aliases = ["houdini", "hip"]
    timer_interval_ms = 50  # 20 FPS - Houdini's main thread is heavily loaded
    recommended_mode = "qt"

    def __init__(self) -> None:
        """Initialize the Houdini adapter."""
        super().__init__()

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Houdini.

        Houdini uses Qt6 (PySide6), but we detect dynamically
        for consistency with other adapters.

        Returns:
            QtConfig with Houdini-specific settings.
        """
        is_qt6 = _detect_qt6()

        # Houdini always needs longer delays due to heavy main thread
        # Qt6 optimizations are applied when detected
        logger.info(f"Houdini: {'Qt6' if is_qt6 else 'Qt5'} detected")
        return QtConfig(
            # Longer delay for Houdini's heavy main thread
            init_delay_ms=100,
            # Slower timer for heavy cooking operations
            timer_interval_ms=50,
            # Extended geometry fix delays
            geometry_fix_delays=[100, 300, 600, 1000, 2000],
            # Qt6 performance optimizations (applied when Qt6 detected)
            force_opaque_window=is_qt6,
            disable_translucent=is_qt6,
            is_qt6=is_qt6,
        )

    def get_main_window(self) -> Any | None:
        """Get Houdini main window as QWidget.

        Tries multiple methods:
        1. hou.qt.mainWindow() (preferred)
        2. Fallback to searching QApplication top-level widgets
        """
        try:
            from qtpy.QtWidgets import QApplication
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Method 1: hou.qt.mainWindow()
        try:
            import hou

            return hou.qt.mainWindow()
        except Exception as e:
            logger.debug(f"hou.qt.mainWindow() failed: {e}")

        # Method 2: Search by window title
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if "Houdini" in widget.windowTitle():
                    return widget

        logger.warning("Could not find Houdini main window")
        return None

    def configure_dialog(self, dialog: QDialog, use_native_window: bool | None = None) -> None:
        """Apply Qt6-specific dialog optimizations for Houdini.

        Houdini uses PySide6 (Qt6) and requires special window handling.
        By default, uses Qt.Tool flag to keep window attached to parent.

        Args:
            dialog: The QDialog to configure.
            use_native_window: If True, use Qt.Window instead of Qt.Tool for
                native window appearance. If None, uses the value from QtConfig.
                Default is None (uses QtConfig.use_native_window).

        Note:
            Qt.Tool windows:
            - Have smaller title bars (tool window style)
            - Stay on top of parent window
            - Don't appear in taskbar
            - Follow parent's minimize/restore

            Qt.Window windows:
            - Have standard title bars (native appearance)
            - Can be moved independently of parent
            - Appear in taskbar
            - Standard window behavior

        To enable native window appearance, set use_native_window=True in QtConfig:
            adapter.qt_config.use_native_window = True
        """
        # Call base implementation first
        super().configure_dialog(dialog)

        # Determine whether to use native window appearance
        # Priority: explicit parameter > QtConfig setting > default (False)
        if use_native_window is None:
            use_native_window = self.qt_config.use_native_window

        # Additional Houdini-specific dialog settings
        try:
            from qtpy.QtCore import Qt
            from auroraview.integration.qt._compat import apply_qt6_dialog_optimizations

            if use_native_window:
                # Use Qt.Window for native window appearance
                # This gives standard title bar and taskbar presence
                dialog.setWindowFlags(
                    Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
                )
                logger.debug("Houdini: Using Qt.Window for native appearance")
            else:
                # CRITICAL: Use Qt.Tool instead of Qt.Window for Houdini
                # Qt.Tool ensures the window stays on top of its parent window
                # This fixes the issue where the shelf window can be moved independently
                # and doesn't follow the Houdini main window
                #
                # From Qt documentation:
                # "If there is a parent, the tool window will always be kept on top of it."
                dialog.setWindowFlags(
                    Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
                )
                logger.debug("Houdini: Using Qt.Tool for attached window behavior")

            # Apply Qt6 optimizations using unified function
            # This ensures all Qt6-specific attributes are set correctly
            apply_qt6_dialog_optimizations(dialog)

            logger.debug("Houdini: Applied Qt6 dialog optimizations")
        except Exception as e:
            logger.debug(f"Houdini: Failed to apply dialog config: {e}")

    # NOTE: configure_webview removed - WA_OpaquePaintEvent on WebView
    # caused black screen issues in Houdini. The dialog-level optimizations
    # in configure_dialog are sufficient for Qt6 performance.

    def apply_qt_optimizations(self) -> None:
        """Apply Qt6-specific performance optimizations for Houdini."""
        try:
            from qtpy.QtCore import QCoreApplication

            app = QCoreApplication.instance()
            if not app:
                return

            logger.info("Houdini: Applying Qt6 performance optimizations")

            # Note: Some Qt6 attributes must be set before QApplication creation
            # These are applied as best-effort for already-running applications

        except Exception as e:
            logger.debug(f"Houdini: Qt6 optimization not applied: {e}")

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Houdini-specific API methods."""
        return {
            "execute_hscript": self._execute_hscript,
            "execute_python": self._execute_python,
            "get_hip_name": self._get_hip_name,
        }

    def _execute_hscript(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute HScript command in Houdini.

        Args:
            params: Dict with "command" key containing HScript code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "command" not in params:
            return {"success": False, "error": "No command provided"}

        try:
            import hou

            result = hou.hscript(params["command"])
            return {"success": True, "result": result[0], "errors": result[1]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_python(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Python code in Houdini's context.

        Args:
            params: Dict with "code" key containing Python code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "code" not in params:
            return {"success": False, "error": "No code provided"}

        try:
            # Execute in Houdini's global namespace
            exec_globals = {"hou": __import__("hou")}
            exec(params["code"], exec_globals)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_hip_name(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current Houdini scene (.hip) name.

        Returns:
            Dict with scene name or error.
        """
        try:
            import hou

            hip_name = hou.hipFile.name()
            return {"success": True, "hip_name": hip_name or "untitled.hip"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def on_init(self, shelf_app: Any) -> None:
        """Houdini-specific initialization."""
        logger.info("Houdini adapter initialized")
        logger.info(
            f"  Qt config: init_delay={self.qt_config.init_delay_ms}ms, timer={self.qt_config.timer_interval_ms}ms"
        )
        logger.info(f"  Qt6 mode: opaque_window={self.qt_config.force_opaque_window}")

        # Apply Qt6 optimizations
        self.apply_qt_optimizations()

        # Store reference to shelf_app for deferred initialization
        self._shelf_app = shelf_app

    def schedule_deferred_callback(self, callback: callable, delay_ms: int = 0) -> bool:
        """Schedule a callback using Houdini's event system.

        IMPORTANT: Houdini's Python Shell runs in a separate thread, so
        QTimer.singleShot callbacks may not execute properly. This method
        uses hou.ui.postEventCallback() to ensure the callback runs in
        Houdini's main UI thread.

        Args:
            callback: The function to call.
            delay_ms: Delay in milliseconds (used with QTimer fallback).

        Returns:
            True if scheduled successfully, False otherwise.
        """
        try:
            import hou

            # Use Houdini's postEventCallback for main thread execution
            # This is the recommended way to run Qt code from Python Shell
            if hasattr(hou.ui, "postEventCallback"):
                logger.debug(f"Houdini: Using postEventCallback for deferred execution")
                hou.ui.postEventCallback(callback)
                return True
            else:
                # Fallback to QTimer for older Houdini versions
                logger.debug(f"Houdini: postEventCallback not available, using QTimer")
                from qtpy.QtCore import QTimer

                QTimer.singleShot(delay_ms, callback)
                return True
        except Exception as e:
            logger.warning(f"Houdini: Failed to schedule callback: {e}")
            # Last resort: try QTimer directly
            try:
                from qtpy.QtCore import QTimer

                QTimer.singleShot(delay_ms, callback)
                return True
            except Exception as e2:
                logger.error(f"Houdini: All scheduling methods failed: {e2}")
                return False

    def on_show(self, shelf_app: Any) -> None:
        """Called after dialog is shown.

        For Houdini, we need to ensure WebView initialization happens
        in the main UI thread using postEventCallback.
        """
        logger.info("Houdini: on_show called, ensuring main thread execution")

    # ========================================
    # Dockable Support
    # ========================================

    def supports_dockable(self) -> bool:
        """Houdini supports dockable panels via Python Panel interfaces."""
        return True

    def create_dockable_widget(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a Houdini Python Panel containing the widget.

        Houdini's Python Panel system requires:
        1. A Python Panel interface definition (XML)
        2. A Python module that creates the widget

        For runtime panels, we use hou.pypanel.installFile() or
        create a floating panel window.

        Args:
            widget: The QWidget to embed.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.

        Returns:
            The panel interface, or None if failed.
        """
        try:
            # Store widget in global registry
            _PANEL_WIDGETS[object_name] = widget

            # Try to create a floating panel first (simpler approach)
            # Houdini's full Python Panel system requires XML interface files
            return self._create_floating_panel(widget, title, object_name)

        except Exception as e:
            logger.error(f"Houdini: Failed to create dockable panel: {e}")
            return None

    def _create_floating_panel(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a floating panel window in Houdini.

        This creates a Qt.Tool window that stays on top of Houdini.
        For full docking support, use Python Panel interfaces.

        Args:
            widget: The QWidget to embed.
            title: The title for the panel.
            object_name: Unique object name for the panel.

        Returns:
            The panel window, or None if failed.
        """
        try:
            import hou
            from qtpy.QtCore import Qt
            from qtpy.QtWidgets import QDialog, QVBoxLayout

            # Get Houdini main window as parent
            parent = hou.qt.mainWindow()

            # Create a tool window (stays on top of parent)
            dialog = QDialog(parent)
            dialog.setWindowTitle(title)
            dialog.setObjectName(object_name)
            dialog.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)

            # Apply Qt6 optimizations
            # NOTE: Do NOT set WA_OpaquePaintEvent! It causes black screen.
            dialog.setAttribute(Qt.WA_TranslucentBackground, False)

            # Add widget to dialog
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(widget)

            # Size from widget or defaults
            width = widget.width() if widget.width() > 0 else 400
            height = widget.height() if widget.height() > 0 else 600
            dialog.resize(width, height)
            dialog.setMinimumSize(300, 200)

            dialog.show()

            logger.info(f"Houdini: Created floating panel '{object_name}'")
            return dialog

        except Exception as e:
            logger.error(f"Houdini: Failed to create floating panel: {e}")
            return None

    def _create_python_panel_interface(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a full Python Panel interface for Houdini.

        This method creates a proper Python Panel that can be docked
        in Houdini's pane system. Requires more setup but provides
        full docking capabilities.

        Note: This is a more complex approach that requires:
        1. Creating a Python Panel interface XML file
        2. Installing the interface with hou.pypanel.installFile()
        3. Creating a pane tab with the interface

        Args:
            widget: The QWidget to embed.
            title: The title for the panel.
            object_name: Unique object name for the panel.

        Returns:
            The panel interface, or None if failed.
        """
        try:
            import os
            import tempfile

            import hou

            # Create a temporary Python Panel interface XML
            interface_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
    <interface name="{object_name}" label="{title}" icon="MISC_python">
        <script><![CDATA[
def createInterface():
    from auroraview_dcc_shelves.apps.houdini import _PANEL_WIDGETS
    widget = _PANEL_WIDGETS.get("{object_name}")
    if widget:
        return widget
    return None
]]></script>
    </interface>
</pythonPanelDocument>"""

            # Write to temp file
            temp_dir = tempfile.gettempdir()
            interface_file = os.path.join(temp_dir, f"{object_name}_panel.pypanel")

            with open(interface_file, "w") as f:
                f.write(interface_xml)

            # Install the interface
            hou.pypanel.installFile(interface_file)

            # Find a pane and add the panel
            desktop = hou.ui.curDesktop()
            if desktop:
                # Try to find an existing pane or create in floating window
                pane_tab = desktop.createFloatingPaneTab(
                    hou.paneTabType.PythonPanel,
                    position=(),
                    size=(400, 600),
                )
                if pane_tab:
                    pane_tab.setActiveInterface(hou.pypanel.interfaceByName(object_name))
                    logger.info(f"Houdini: Created Python Panel '{object_name}'")
                    return pane_tab

            return None

        except Exception as e:
            logger.error(f"Houdini: Failed to create Python Panel interface: {e}")
            return None

    def show_dockable(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
        **kwargs: Any,
    ) -> bool:
        """Show a widget as a dockable panel in Houdini.

        Args:
            widget: The QWidget to show as dockable.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.
            **kwargs: Additional options:
                - use_python_panel: Use full Python Panel (default: False)
                - pane: Pane name to dock to

        Returns:
            True if the dockable panel was created successfully.
        """
        use_python_panel = kwargs.get("use_python_panel", False)

        if use_python_panel:
            panel = self._create_python_panel_interface(widget, title, object_name)
        else:
            panel = self.create_dockable_widget(widget, title, object_name)

        return panel is not None

    def restore_dockable(self, object_name: str) -> bool:
        """Restore a Houdini dockable panel.

        Args:
            object_name: The unique object name of the panel.

        Returns:
            True if the panel was restored successfully.
        """
        if object_name in _PANEL_WIDGETS:
            widget = _PANEL_WIDGETS[object_name]
            if widget:
                widget.show()
                # Also show parent dialog if it exists
                parent = widget.parent()
                if parent:
                    parent.show()
                logger.info(f"Houdini: Restored dockable panel '{object_name}'")
                return True
        return False

    def close_dockable(self, object_name: str) -> bool:
        """Close a Houdini dockable panel.

        Args:
            object_name: The unique object name of the panel.

        Returns:
            True if the panel was closed successfully.
        """
        try:
            if object_name in _PANEL_WIDGETS:
                widget = _PANEL_WIDGETS[object_name]
                if widget:
                    # Close parent dialog if it exists
                    parent = widget.parent()
                    if parent and hasattr(parent, "close"):
                        parent.close()
                    widget.close()
                    widget.deleteLater()
                del _PANEL_WIDGETS[object_name]

            logger.info(f"Houdini: Closed dockable panel '{object_name}'")
            return True
        except Exception as e:
            logger.error(f"Houdini: Failed to close dockable panel: {e}")
            return False
