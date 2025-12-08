"""Blender DCC Adapter.

Handles Blender-specific integration including:
- Main window detection via bpy module and Win32 API
- Native WebView window (tao/wry) - Blender doesn't use Qt
- Scene and object management APIs
- Balanced timer settings for 3D workflows

Note:
    Blender uses its own UI toolkit (GHOST), not Qt. We use the native
    tao/wry WebView window which runs in a background thread, allowing
    Blender's main thread to remain responsive.

    The WebView window stays on top of Blender and can be positioned
    alongside Blender's UI.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, QtConfig, register_adapter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QDialog, QWidget

logger = logging.getLogger(__name__)

# Global registry for panel widgets (unused in standalone mode, kept for API compatibility)
_PANEL_WIDGETS: dict[str, QWidget] = {}


@register_adapter
class BlenderAdapter(DCCAdapter):
    """Adapter for Blender.

    Blender-specific considerations:
    - Blender uses its own UI toolkit (GHOST), not Qt
    - Uses native tao/wry WebView window (like Desktop mode)
    - WebView runs in background thread, keeping Blender responsive
    - Timer interval balanced for 3D workflows
    """

    name = "Blender"
    aliases = ["blender", "bpy"]
    timer_interval_ms = 32  # 30 FPS - balanced for 3D work
    # Use HWND mode - native tao/wry window in background thread
    # This works without Qt and keeps Blender's main thread free
    recommended_mode = "hwnd"

    def __init__(self) -> None:
        """Initialize the Blender adapter."""
        super().__init__()
        self._blender_hwnd: int | None = None

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Blender.

        Note: Blender doesn't use Qt, but we provide a config
        for API compatibility. The actual mode is "hwnd" which
        doesn't use Qt at all.

        Returns:
            QtConfig with default settings.
        """
        # Blender doesn't use Qt, but provide config for API compatibility
        return QtConfig(
            init_delay_ms=10,
            timer_interval_ms=16,
            geometry_fix_delays=[],
            force_opaque_window=False,
            disable_translucent=False,
            is_qt6=False,  # Not using Qt
        )

    def _get_blender_hwnd(self) -> int | None:
        """Get Blender main window HWND via Win32 API.

        Returns:
            The HWND as an integer, or None if not found.
        """
        if self._blender_hwnd is not None:
            return self._blender_hwnd

        try:
            import sys

            if sys.platform != "win32":
                return None

            import ctypes

            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, None)

            while hwnd:
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    if "Blender" in buf.value:
                        logger.info(f"Found Blender window HWND: 0x{hwnd:X} ({buf.value})")
                        self._blender_hwnd = hwnd
                        return hwnd
                hwnd = user32.GetWindow(hwnd, 2)  # GW_HWNDNEXT

        except Exception as e:
            logger.debug(f"Blender HWND search failed: {e}")

        return None

    def get_main_window(self) -> Any | None:
        """Get Blender main window.

        Note: Blender doesn't use Qt for its UI, so we can't get
        a QWidget reference. We return None and use HWND mode instead.
        """
        # Get and cache the HWND for reference
        hwnd = self._get_blender_hwnd()
        if hwnd:
            logger.info(f"Blender: Found main window HWND 0x{hwnd:X}")
        else:
            logger.info("Blender: Main window HWND not found")
        # Return None - we use HWND mode, not Qt mode
        return None

    def configure_dialog(self, dialog: QDialog, use_native_window: bool | None = None) -> None:
        """Configure dialog for Blender.

        Note: This method is not used in HWND mode, but provided
        for API compatibility.

        Args:
            dialog: The QDialog to configure.
            use_native_window: Ignored for Blender.
        """
        # Not used in HWND mode
        pass

    def get_webview_params(self, debug: bool = False) -> dict[str, Any]:
        """Get WebView creation parameters for Blender.

        Args:
            debug: Whether debug mode is enabled.

        Returns:
            Dictionary of WebView creation parameters.
        """
        return {
            "dev_tools": debug,
            "context_menu": debug,
        }

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
        logger.info("  Mode: HWND (native tao/wry window)")
        logger.info(f"  Timer interval: {self.timer_interval_ms}ms")
        if self._blender_hwnd:
            logger.info(f"  Blender HWND: 0x{self._blender_hwnd:X}")

    # ========================================
    # Dockable Support
    # ========================================

    def supports_dockable(self) -> bool:
        """Blender doesn't support Qt dockable panels (uses HWND mode)."""
        return False
