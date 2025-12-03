"""Houdini DCC Adapter.

Handles Houdini-specific integration including:
- Main window detection via hou.qt module
- Longer timer intervals for heavy cooking/VEX operations
- Special handling for Houdini's threaded architecture
"""

from __future__ import annotations

import logging
from typing import Any

from .base import DCCAdapter, register_adapter

logger = logging.getLogger(__name__)


@register_adapter
class HoudiniAdapter(DCCAdapter):
    """Adapter for SideFX Houdini."""

    name = "Houdini"
    aliases = ["houdini", "hip"]
    timer_interval_ms = 50  # 20 FPS - Houdini's main thread is heavily loaded
    recommended_mode = "qt"

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
        logger.info("Houdini adapter initialized - using slower timer for cooking")

