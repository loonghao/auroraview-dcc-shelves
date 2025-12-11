"""3ds Max DCC Adapter.

Handles 3ds Max-specific integration including:
- Main window detection via MaxPlus or pymxs
- Windows-specific COM considerations
- Balanced timer settings
"""

from __future__ import annotations

import logging
from typing import Any

from .base import DCCAdapter, register_adapter

logger = logging.getLogger(__name__)


@register_adapter
class Max3dsAdapter(DCCAdapter):
    """Adapter for Autodesk 3ds Max."""

    name = "3dsmax"
    aliases = ["max", "3ds", "3dsmax"]
    timer_interval_ms = 32  # 30 FPS - balanced
    recommended_mode = "qt"

    def get_main_window(self) -> Any | None:
        """Get 3ds Max main window as QWidget.

        Tries multiple methods:
        1. MaxPlus.GetQMaxMainWindow() (Max 2018+)
        2. pymxs runtime (Max 2021+)
        3. Fallback to QApplication search
        """
        try:
            from qtpy.QtWidgets import QApplication
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Method 1: MaxPlus (deprecated but still works in some versions)
        try:
            import MaxPlus
            return MaxPlus.GetQMaxMainWindow()
        except Exception as e:
            logger.debug(f"MaxPlus method failed: {e}")

        # Method 2: pymxs (3ds Max 2021+)
        try:
            from pymxs import runtime as rt
            import ctypes
            from qtpy.QtWidgets import QWidget

            hwnd = rt.windows.getMAXHWND()
            if hwnd:
                # Try to find the QWidget wrapping this HWND
                app = QApplication.instance()
                if app:
                    for widget in app.topLevelWidgets():
                        if widget.winId() == hwnd:
                            return widget
        except Exception as e:
            logger.debug(f"pymxs method failed: {e}")

        # Method 3: Search by window title
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                title = widget.windowTitle()
                if "3ds Max" in title or "Autodesk" in title:
                    return widget

        logger.warning("Could not find 3ds Max main window")
        return None

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add 3ds Max-specific API methods."""
        return {
            "execute_maxscript": self._execute_maxscript,
            "get_scene_name": self._get_scene_name,
        }

    def _execute_maxscript(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute MAXScript code in 3ds Max.

        Args:
            params: Dict with "script" key containing MAXScript code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "script" not in params:
            return {"success": False, "error": "No script provided"}

        try:
            from pymxs import runtime as rt
            result = rt.execute(params["script"])
            return {"success": True, "result": str(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_scene_name(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current 3ds Max scene name.

        Returns:
            Dict with scene name or error.
        """
        try:
            from pymxs import runtime as rt
            scene_name = rt.maxFilePath + rt.maxFileName
            return {"success": True, "scene_name": scene_name or "untitled.max"}
        except Exception as e:
            return {"success": False, "error": str(e)}

