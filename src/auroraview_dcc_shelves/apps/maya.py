"""Maya DCC Adapter.

Handles Maya-specific integration including:
- Main window detection using OpenMayaUI
- Shiboken/shiboken6 wrapper for Qt pointer conversion
- Optimized timer settings for Maya's event loop
"""

from __future__ import annotations

import logging
from typing import Any

from .base import DCCAdapter, register_adapter

logger = logging.getLogger(__name__)


@register_adapter
class MayaAdapter(DCCAdapter):
    """Adapter for Autodesk Maya."""

    name = "Maya"
    aliases = []
    timer_interval_ms = 16  # 60 FPS - Maya handles fast timers well
    recommended_mode = "qt"

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

