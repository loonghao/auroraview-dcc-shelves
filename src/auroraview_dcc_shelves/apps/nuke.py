"""Nuke DCC Adapter.

Handles Nuke-specific integration including:
- Main window detection via nukescripts or QApplication
- Geometry fixes for Nuke's custom window management
- Balanced timer settings for compositing workflows
"""

from __future__ import annotations

import logging
from typing import Any

from .base import DCCAdapter, register_adapter

logger = logging.getLogger(__name__)


@register_adapter
class NukeAdapter(DCCAdapter):
    """Adapter for Foundry Nuke."""

    name = "Nuke"
    aliases = ["nuke", "nukex", "nukestudio"]
    timer_interval_ms = 32  # 30 FPS - balanced for compositing
    recommended_mode = "qt"

    def get_main_window(self) -> Any | None:
        """Get Nuke main window as QWidget.

        Tries multiple methods:
        1. nukescripts.panels.getMainWindow() (if available)
        2. Search for NukeMainWindow in QApplication
        3. Fallback to searching by window title
        """
        try:
            from qtpy.QtWidgets import QApplication
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Method 1: nukescripts.panels
        try:
            from nukescripts import panels
            if hasattr(panels, "getMainWindow"):
                return panels.getMainWindow()
        except Exception as e:
            logger.debug(f"nukescripts.panels failed: {e}")

        # Method 2: Search for NukeMainWindow
        app = QApplication.instance()
        if app:
            for obj in app.topLevelWidgets():
                if obj.objectName() == "NukeMainWindow":
                    return obj

        # Method 3: Search by class name
        if app:
            for widget in app.topLevelWidgets():
                class_name = widget.metaObject().className()
                if "MainWindow" in class_name or "Nuke" in widget.windowTitle():
                    return widget

        logger.warning("Could not find Nuke main window")
        return None

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Nuke-specific API methods."""
        return {
            "execute_tcl": self._execute_tcl,
            "execute_python": self._execute_python,
            "get_script_name": self._get_script_name,
            "create_node": self._create_node,
        }

    def _execute_tcl(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute TCL command in Nuke.

        Args:
            params: Dict with "command" key containing TCL code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "command" not in params:
            return {"success": False, "error": "No command provided"}

        try:
            import nuke
            result = nuke.tcl(params["command"])
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_python(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Python code in Nuke's context.

        Args:
            params: Dict with "code" key containing Python code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "code" not in params:
            return {"success": False, "error": "No code provided"}

        try:
            exec_globals = {"nuke": __import__("nuke")}
            exec(params["code"], exec_globals)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_script_name(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current Nuke script name.

        Returns:
            Dict with script name or error.
        """
        try:
            import nuke
            script_name = nuke.root().name()
            return {"success": True, "script_name": script_name or "untitled.nk"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_node(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a node in Nuke.

        Args:
            params: Dict with "node_type" and optional "name" keys.

        Returns:
            Dict with success status and node name.
        """
        if not params or "node_type" not in params:
            return {"success": False, "error": "No node_type provided"}

        try:
            import nuke
            node = nuke.createNode(params["node_type"])
            if "name" in params:
                node.setName(params["name"])
            return {"success": True, "node_name": node.name()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def on_show(self, shelf_app: Any) -> None:
        """Nuke-specific post-show setup.

        Nuke requires additional geometry fixes due to its
        custom window management.
        """
        logger.debug("Nuke adapter: scheduling geometry fixes")

