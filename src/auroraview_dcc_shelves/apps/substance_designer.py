"""Substance 3D Designer DCC Adapter.

Handles Substance 3D Designer-specific integration including:
- Main window detection via sd module
- PySide6/Qt6 optimizations for Designer
- Graph and package management APIs
- Balanced timer settings for node-based workflows

Qt Version Notes:
    Substance 3D Designer uses PySide6 (Qt6).
    Qt version is detected dynamically using qtpy's API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, QtConfig, _detect_qt6, register_adapter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QDialog, QWidget

logger = logging.getLogger(__name__)


@register_adapter
class SubstanceDesignerAdapter(DCCAdapter):
    """Adapter for Adobe Substance 3D Designer.

    Substance Designer-specific optimizations:
    - Balanced timer interval (40ms/25FPS) for node graph workflows
    - Qt6 optimizations applied when detected
    - Graph and package context awareness
    """

    name = "SubstanceDesigner"
    aliases = ["substancedesigner", "designer", "sd", "substance_designer", "substance3ddesigner"]
    timer_interval_ms = 40  # 25 FPS - node graphs can be heavy
    recommended_mode = "qt"

    def __init__(self) -> None:
        """Initialize the Substance Designer adapter."""
        super().__init__()

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Substance Designer.

        Substance Designer uses Qt6 (PySide6).

        Returns:
            QtConfig with appropriate settings.
        """
        is_qt6 = _detect_qt6()
        logger.info(f"Substance Designer: {'Qt6' if is_qt6 else 'Qt5'} detected")

        return QtConfig(
            init_delay_ms=50,
            timer_interval_ms=40,
            geometry_fix_delays=[50, 150, 300],
            force_opaque_window=is_qt6,
            disable_translucent=is_qt6,
            is_qt6=is_qt6,
        )

    def get_main_window(self) -> Any | None:
        """Get Substance Designer main window as QWidget.

        Tries multiple methods:
        1. sd.getContext().getMainWindow() (preferred)
        2. Fallback to searching QApplication top-level widgets
        """
        try:
            from qtpy.QtWidgets import QApplication
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Method 1: sd module
        try:
            import sd

            ctx = sd.getContext()
            app = ctx.getSDApplication()
            ui_mgr = app.getQtForPythonUIMgr()
            return ui_mgr.getMainWindow()
        except Exception as e:
            logger.debug(f"sd.getContext() method failed: {e}")

        # Method 2: Search by window title
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                title = widget.windowTitle()
                if "Substance" in title and "Designer" in title:
                    return widget

        logger.warning("Could not find Substance Designer main window")
        return None

    def configure_dialog(self, dialog: "QDialog") -> None:
        """Apply Qt6-specific dialog optimizations for Substance Designer.

        Args:
            dialog: The QDialog to configure.
        """
        super().configure_dialog(dialog)

        try:
            from qtpy.QtCore import Qt

            dialog.setWindowFlags(Qt.Tool | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
            dialog.setAttribute(Qt.WA_OpaquePaintEvent, True)
            dialog.setAttribute(Qt.WA_TranslucentBackground, False)

            logger.debug("Substance Designer: Applied Qt6 dialog optimizations")
        except Exception as e:
            logger.debug(f"Substance Designer: Failed to apply dialog config: {e}")

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Substance Designer-specific API methods."""
        return {
            "get_current_graph": self._get_current_graph,
            "get_package_info": self._get_package_info,
            "get_selected_nodes": self._get_selected_nodes,
            "execute_node": self._execute_node,
        }

    def _get_current_graph(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current active graph information.

        Returns:
            Dict with graph name and type.
        """
        try:
            import sd

            ctx = sd.getContext()
            app = ctx.getSDApplication()
            ui_mgr = app.getQtForPythonUIMgr()
            current_graph = ui_mgr.getCurrentGraph()

            if current_graph:
                return {
                    "success": True,
                    "identifier": current_graph.getIdentifier(),
                    "type": str(current_graph.getType()),
                }
            return {"success": True, "graph": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_package_info(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current package information.

        Returns:
            Dict with package file path.
        """
        try:
            import sd

            ctx = sd.getContext()
            app = ctx.getSDApplication()
            pkg_mgr = app.getPackageMgr()
            packages = pkg_mgr.getUserPackages()

            pkg_list = []
            for pkg in packages:
                pkg_list.append(
                    {
                        "file_path": pkg.getFilePath(),
                    }
                )
            return {"success": True, "packages": pkg_list}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_selected_nodes(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get currently selected nodes in the graph.

        Returns:
            Dict with list of selected node identifiers.
        """
        try:
            import sd

            ctx = sd.getContext()
            app = ctx.getSDApplication()
            ui_mgr = app.getQtForPythonUIMgr()
            selection = ui_mgr.getCurrentGraphSelection()

            if selection:
                nodes = []
                for node in selection:
                    nodes.append(
                        {
                            "identifier": node.getIdentifier(),
                            "definition": node.getDefinition().getLabel() if node.getDefinition() else None,
                        }
                    )
                return {"success": True, "nodes": nodes, "count": len(nodes)}
            return {"success": True, "nodes": [], "count": 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_node(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute/compute a specific node.

        Args:
            params: Dict with "node_id" key for node identifier.

        Returns:
            Dict with execution status.
        """
        if not params or "node_id" not in params:
            return {"success": False, "error": "No node_id provided"}

        try:
            import sd

            ctx = sd.getContext()
            app = ctx.getSDApplication()
            ui_mgr = app.getQtForPythonUIMgr()
            graph = ui_mgr.getCurrentGraph()

            if graph:
                node = graph.getNodeFromId(params["node_id"])
                if node:
                    node.compute()
                    return {"success": True, "node_id": params["node_id"]}
                return {"success": False, "error": "Node not found"}
            return {"success": False, "error": "No graph open"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def on_init(self, shelf_app: Any) -> None:
        """Substance Designer-specific initialization."""
        logger.info("Substance Designer adapter initialized")
        logger.info(
            f"  Qt config: init_delay={self.qt_config.init_delay_ms}ms, timer={self.qt_config.timer_interval_ms}ms"
        )

    def supports_dockable(self) -> bool:
        """Substance Designer supports dockable panels."""
        return True
