"""Blender DCC Adapter.

Handles Blender-specific integration including:
- Main window detection via bpy module
- Qt integration through bpy.app.handlers
- Scene and object management APIs
- Balanced timer settings for 3D workflows

Note:
    Blender uses its own UI toolkit, not Qt. However, we can still
    create Qt windows that work alongside Blender. The main window
    detection returns None since Blender doesn't use Qt for its UI.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, QtConfig, _detect_qt6, register_adapter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QDialog, QWidget

logger = logging.getLogger(__name__)


@register_adapter
class BlenderAdapter(DCCAdapter):
    """Adapter for Blender.

    Blender-specific considerations:
    - Blender uses its own UI toolkit, not Qt
    - Qt windows can be created but won't be parented to Blender
    - Modal operators may be needed for proper integration
    - Timer interval balanced for 3D workflows
    """

    name = "Blender"
    aliases = ["blender", "bpy"]
    timer_interval_ms = 32  # 30 FPS - balanced for 3D work
    recommended_mode = "qt"  # Qt windows work, just not parented

    def __init__(self) -> None:
        """Initialize the Blender adapter."""
        super().__init__()

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Blender.

        Since Blender doesn't use Qt for its UI, we use
        standalone Qt window settings.

        Returns:
            QtConfig with standalone window settings.
        """
        is_qt6 = _detect_qt6()
        logger.info(f"Blender: Using {'Qt6' if is_qt6 else 'Qt5'} for standalone window")

        return QtConfig(
            init_delay_ms=50,
            timer_interval_ms=32,
            geometry_fix_delays=[50, 150, 300],
            force_opaque_window=is_qt6,
            disable_translucent=is_qt6,
            is_qt6=is_qt6,
        )

    def get_main_window(self) -> Any | None:
        """Get Blender main window.

        Note: Blender doesn't use Qt for its UI, so we can't get
        a QWidget reference to the main window. Instead, we return
        None and the dialog will be created as a standalone window.
        """
        # Try to get the window via ctypes on Windows
        try:
            import sys

            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes

                # Find Blender window by title
                user32 = ctypes.windll.user32
                hwnd = user32.FindWindowW(None, None)

                while hwnd:
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        if "Blender" in buf.value:
                            logger.info(f"Found Blender window: {buf.value}")
                            # We found it, but can't return as QWidget
                            break
                    hwnd = user32.GetWindow(hwnd, 2)  # GW_HWNDNEXT
        except Exception as e:
            logger.debug(f"Window search failed: {e}")

        logger.info("Blender: Using standalone window mode (Blender doesn't use Qt)")
        return None

    def configure_dialog(self, dialog: "QDialog", use_native_window: bool | None = None) -> None:
        """Configure dialog for Blender (standalone mode).

        Since Blender doesn't use Qt, dialogs are standalone windows.

        Args:
            dialog: The QDialog to configure.
            use_native_window: Ignored for Blender (always uses Qt.Window).
        """
        super().configure_dialog(dialog, use_native_window)

        try:
            from qtpy.QtCore import Qt

            # Use Window flag for standalone behavior
            dialog.setWindowFlags(
                Qt.Window
                | Qt.WindowTitleHint
                | Qt.WindowCloseButtonHint
                | Qt.WindowMinMaxButtonsHint
                | Qt.WindowStaysOnTopHint  # Keep on top of Blender
            )
            dialog.setAttribute(Qt.WA_OpaquePaintEvent, True)

            logger.debug("Blender: Configured standalone dialog")
        except Exception as e:
            logger.debug(f"Blender: Failed to apply dialog config: {e}")

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Blender-specific API methods."""
        return {
            "get_scene_info": self._get_scene_info,
            "get_selected_objects": self._get_selected_objects,
            "get_active_object": self._get_active_object,
            "execute_python": self._execute_python,
        }

    def _get_scene_info(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current scene information.

        Returns:
            Dict with scene name and frame info.
        """
        try:
            import bpy

            scene = bpy.context.scene
            return {
                "success": True,
                "name": scene.name,
                "frame_current": scene.frame_current,
                "frame_start": scene.frame_start,
                "frame_end": scene.frame_end,
                "object_count": len(scene.objects),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_selected_objects(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get currently selected objects.

        Returns:
            Dict with list of selected object names.
        """
        try:
            import bpy

            selected = [obj.name for obj in bpy.context.selected_objects]
            return {"success": True, "objects": selected, "count": len(selected)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_active_object(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get the active object.

        Returns:
            Dict with active object information.
        """
        try:
            import bpy

            obj = bpy.context.active_object
            if obj:
                return {
                    "success": True,
                    "name": obj.name,
                    "type": obj.type,
                    "location": list(obj.location),
                    "rotation": list(obj.rotation_euler),
                    "scale": list(obj.scale),
                }
            return {"success": True, "object": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_python(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Python code in Blender's context.

        Args:
            params: Dict with "code" key containing Python code.

        Returns:
            Dict with execution result.
        """
        if not params or "code" not in params:
            return {"success": False, "error": "No code provided"}

        try:
            import bpy

            exec_globals = {"bpy": bpy}
            exec(params["code"], exec_globals)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def on_init(self, shelf_app: Any) -> None:
        """Blender-specific initialization."""
        logger.info("Blender adapter initialized")
        logger.info("  Note: Blender uses standalone window mode (not Qt-based UI)")
        logger.info(f"  Timer interval: {self.qt_config.timer_interval_ms}ms")

    def supports_dockable(self) -> bool:
        """Blender doesn't support Qt dockable panels natively."""
        return False
