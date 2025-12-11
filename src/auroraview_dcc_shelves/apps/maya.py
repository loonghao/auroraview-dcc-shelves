"""Maya DCC Adapter.

Handles Maya-specific integration including:
- Main window detection using OpenMayaUI
- Shiboken/shiboken6 wrapper for Qt pointer conversion
- Optimized timer settings for Maya's event loop
- Dockable panel support via workspaceControl

Qt Version Notes:
    - Maya 2022-2025: PySide2 (Qt5)
    - Maya 2026+: PySide6 (Qt6)

    Qt version is detected dynamically using qtpy's API.
    Qt6 optimizations (opaque window, etc.) are applied automatically
    when running in Maya 2026+.

Dockable Support:
    Maya supports dockable panels via workspaceControl command.
    This provides native Maya docking with state persistence.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, QtConfig, _detect_qt6, register_adapter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# Global registry for dockable widgets (needed for Maya's callback system)
_DOCKABLE_WIDGETS: dict[str, QWidget] = {}


@register_adapter
class MayaAdapter(DCCAdapter):
    """Adapter for Autodesk Maya.

    Maya-specific optimizations:
    - Fast timer interval (16ms/60FPS) - Maya handles this well
    - Qt version detected dynamically (Qt5 for Maya 2022-2025, Qt6 for 2026+)
    - Qt6 optimizations applied automatically when needed
    """

    name = "Maya"
    aliases = []
    timer_interval_ms = 16  # 60 FPS - Maya handles fast timers well
    recommended_mode = "qt"

    def __init__(self) -> None:
        """Initialize the Maya adapter."""
        super().__init__()

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Maya.

        Detects Qt version dynamically to support both:
        - Maya 2022-2025 (PySide2/Qt5)
        - Maya 2026+ (PySide6/Qt6)

        Returns:
            QtConfig with appropriate settings.
        """
        is_qt6 = _detect_qt6()

        if is_qt6:
            # Maya 2026+ with Qt6 - apply Qt6 optimizations
            logger.info("Maya: Qt6 detected (Maya 2026+)")
            return QtConfig(
                # Slightly longer delay for Qt6 initialization
                init_delay_ms=50,
                timer_interval_ms=16,
                geometry_fix_delays=[100, 300, 500, 1000, 2000],
                # Qt6 performance optimizations
                force_opaque_window=True,
                disable_translucent=True,
                is_qt6=True,
            )
        else:
            # Maya 2022-2025 with Qt5 - standard settings
            logger.info("Maya: Qt5 detected (Maya 2022-2025)")
            return QtConfig(
                init_delay_ms=10,
                timer_interval_ms=16,
                geometry_fix_delays=[100, 500, 1000, 2000],
                force_opaque_window=False,
                disable_translucent=False,
                is_qt6=False,
            )

    def get_main_window(self) -> Any | None:
        """Get Maya main window as QWidget.

        Tries multiple methods:
        1. OpenMayaUI.MQtUtil.mainWindow() with shiboken/shiboken6
        2. Fallback to searching QApplication top-level widgets
        """
        try:
            from qtpy.QtWidgets import QApplication, QWidget
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Method 1: OpenMayaUI with shiboken
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

                # Try shiboken2 (Maya 2022-2023)
                try:
                    from shiboken2 import wrapInstance

                    return wrapInstance(int(main_window_ptr), QWidget)
                except ImportError:
                    pass
        except Exception as e:
            logger.debug(f"OpenMayaUI method failed: {e}")

        # Method 2: Search for MayaWindow
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.objectName() == "MayaWindow":
                    return widget

        logger.warning("Could not find Maya main window")
        return None

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Maya-specific API methods."""
        return {
            "execute_mel": self._execute_mel,
            "get_scene_name": self._get_scene_name,
        }

    def _execute_mel(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute MEL command in Maya.

        Args:
            params: Dict with "command" key containing MEL code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "command" not in params:
            return {"success": False, "error": "No command provided"}

        try:
            import maya.mel as mel

            result = mel.eval(params["command"])
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_scene_name(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current Maya scene name.

        Returns:
            Dict with scene name or error.
        """
        try:
            import maya.cmds as cmds

            scene_name = cmds.file(q=True, sceneName=True)
            return {"success": True, "scene_name": scene_name or "untitled"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================
    # Dockable Support
    # ========================================

    def supports_dockable(self) -> bool:
        """Maya supports dockable panels via workspaceControl."""
        return True

    def create_dockable_widget(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a Maya workspaceControl containing the widget.

        Uses Maya's workspaceControl command for native docking support.
        The widget is stored in a global registry for Maya's callback system.

        Args:
            widget: The QWidget to embed.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.

        Returns:
            The workspaceControl name, or None if failed.
        """
        try:
            import maya.cmds as cmds

            # Store widget in global registry for restore callback
            _DOCKABLE_WIDGETS[object_name] = widget

            # Delete existing workspace control if it exists
            if cmds.workspaceControl(object_name, exists=True):
                cmds.deleteUI(object_name)

            # Create the workspace control
            # uiScript is called when Maya needs to restore the panel
            workspace_control = cmds.workspaceControl(
                object_name,
                label=title,
                retain=False,  # Don't retain when closed
                floating=True,  # Start as floating window
                initialWidth=widget.width() if widget.width() > 0 else 400,
                initialHeight=widget.height() if widget.height() > 0 else 600,
                minimumWidth=300,
                minimumHeight=200,
            )

            # Get the workspace control as a Qt widget and add our widget to it
            workspace_ptr = self._get_workspace_control_ptr(workspace_control)
            if workspace_ptr:
                from qtpy.QtWidgets import QVBoxLayout
                from qtpy.QtWidgets import QWidget as QW

                # Get the workspace control widget
                workspace_widget = self._wrap_pointer(workspace_ptr, QW)
                if workspace_widget:
                    # Create layout and add our widget
                    layout = workspace_widget.layout()
                    if layout is None:
                        layout = QVBoxLayout(workspace_widget)
                        layout.setContentsMargins(0, 0, 0, 0)
                        layout.setSpacing(0)
                    layout.addWidget(widget)
                    widget.show()

                    logger.info(f"Maya: Created dockable panel '{object_name}'")
                    return workspace_control

            logger.error("Maya: Failed to get workspace control pointer")
            return None

        except Exception as e:
            logger.error(f"Maya: Failed to create dockable panel: {e}")
            return None

    def _get_workspace_control_ptr(self, workspace_control: str) -> int | None:
        """Get the Qt pointer for a workspace control.

        Args:
            workspace_control: The workspace control name.

        Returns:
            The Qt pointer as an integer, or None if failed.
        """
        try:
            import maya.OpenMayaUI as omui

            ptr = omui.MQtUtil.findControl(workspace_control)
            return int(ptr) if ptr else None
        except Exception as e:
            logger.debug(f"Maya: Failed to get workspace control pointer: {e}")
            return None

    def _wrap_pointer(self, ptr: int, base_class: type) -> Any:
        """Wrap a Qt pointer using shiboken.

        Args:
            ptr: The Qt pointer as an integer.
            base_class: The Qt class to wrap as.

        Returns:
            The wrapped Qt widget, or None if failed.
        """
        # Try shiboken6 first (Maya 2024+)
        try:
            from shiboken6 import wrapInstance

            return wrapInstance(ptr, base_class)
        except ImportError:
            pass

        # Try shiboken2 (Maya 2022-2023)
        try:
            from shiboken2 import wrapInstance

            return wrapInstance(ptr, base_class)
        except ImportError:
            pass

        return None

    def show_dockable(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
        **kwargs: Any,
    ) -> bool:
        """Show a widget as a dockable panel in Maya.

        Args:
            widget: The QWidget to show as dockable.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.
            **kwargs: Additional options:
                - floating: Start as floating window (default: True)
                - area: Dock area ("left", "right", "top", "bottom")
                - tabToControl: Tab to existing control

        Returns:
            True if the dockable panel was created successfully.
        """
        workspace_control = self.create_dockable_widget(widget, title, object_name)
        if workspace_control:
            try:
                import maya.cmds as cmds

                # Apply additional options
                floating = kwargs.get("floating", True)
                area = kwargs.get("area")
                tab_to = kwargs.get("tabToControl")

                if not floating and area:
                    cmds.workspaceControl(
                        workspace_control,
                        edit=True,
                        dockToMainWindow=(area, True),
                    )
                elif tab_to:
                    cmds.workspaceControl(
                        workspace_control,
                        edit=True,
                        tabToControl=(tab_to, -1),
                    )

                return True
            except Exception as e:
                logger.error(f"Maya: Failed to configure dockable panel: {e}")
                return False
        return False

    def restore_dockable(self, object_name: str) -> bool:
        """Restore a Maya dockable panel.

        Called by Maya when restoring workspace state.

        Args:
            object_name: The unique object name of the panel.

        Returns:
            True if the panel was restored successfully.
        """
        if object_name in _DOCKABLE_WIDGETS:
            widget = _DOCKABLE_WIDGETS[object_name]
            workspace_ptr = self._get_workspace_control_ptr(object_name)
            if workspace_ptr:
                from qtpy.QtWidgets import QVBoxLayout
                from qtpy.QtWidgets import QWidget as QW

                workspace_widget = self._wrap_pointer(workspace_ptr, QW)
                if workspace_widget:
                    layout = workspace_widget.layout()
                    if layout is None:
                        layout = QVBoxLayout(workspace_widget)
                        layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(widget)
                    widget.show()
                    logger.info(f"Maya: Restored dockable panel '{object_name}'")
                    return True
        return False

    def close_dockable(self, object_name: str) -> bool:
        """Close a Maya dockable panel.

        Args:
            object_name: The unique object name of the panel.

        Returns:
            True if the panel was closed successfully.
        """
        try:
            import maya.cmds as cmds

            if cmds.workspaceControl(object_name, exists=True):
                cmds.deleteUI(object_name)

            # Remove from registry
            if object_name in _DOCKABLE_WIDGETS:
                del _DOCKABLE_WIDGETS[object_name]

            logger.info(f"Maya: Closed dockable panel '{object_name}'")
            return True
        except Exception as e:
            logger.error(f"Maya: Failed to close dockable panel: {e}")
            return False
