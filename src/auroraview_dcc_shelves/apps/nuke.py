"""Nuke DCC Adapter.

Handles Nuke-specific integration including:
- Main window detection via nukescripts or QApplication
- Geometry fixes for Nuke's custom window management
- Balanced timer settings for compositing workflows
- Dockable panel support via nukescripts.panels

Qt Version Notes:
    Nuke currently uses PySide2 (Qt5). Future versions may use Qt6.
    Qt version is detected dynamically using qtpy's API.

Dockable Support:
    Nuke supports dockable panels via nukescripts.panels.registerWidgetAsPanel().
    This provides native Nuke panel docking with tab support.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import DCCAdapter, QtConfig, _detect_qt6, register_adapter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# Global registry for panel widget factories
_PANEL_FACTORIES: dict[str, type] = {}
_PANEL_INSTANCES: dict[str, QWidget] = {}


@register_adapter
class NukeAdapter(DCCAdapter):
    """Adapter for Foundry Nuke.

    Nuke-specific optimizations:
    - Balanced timer interval (32ms/30FPS) for compositing
    - Extended geometry fix delays for Nuke's window management
    - Qt version detected dynamically
    """

    name = "Nuke"
    aliases = ["nuke", "nukex", "nukestudio"]
    timer_interval_ms = 32  # 30 FPS - balanced for compositing
    recommended_mode = "qt"

    def __init__(self) -> None:
        """Initialize the Nuke adapter."""
        super().__init__()

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Nuke.

        Detects Qt version dynamically. Nuke requires extended
        geometry fixes due to its custom window management system.

        Returns:
            QtConfig with appropriate settings.
        """
        is_qt6 = _detect_qt6()

        if is_qt6:
            # Future Nuke with Qt6
            logger.info("Nuke: Qt6 detected")
            return QtConfig(
                init_delay_ms=50,
                timer_interval_ms=32,
                geometry_fix_delays=[100, 300, 500, 1000, 2000],
                force_opaque_window=True,
                disable_translucent=True,
                is_qt6=True,
            )
        else:
            # Current Nuke with Qt5
            logger.info("Nuke: Qt5 detected")
            return QtConfig(
                init_delay_ms=10,
                timer_interval_ms=32,
                geometry_fix_delays=[100, 300, 500, 1000, 2000],
                force_opaque_window=False,
                disable_translucent=False,
                is_qt6=False,
            )

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

    # ========================================
    # Dockable Support
    # ========================================

    def supports_dockable(self) -> bool:
        """Nuke supports dockable panels via nukescripts.panels."""
        return True

    def create_dockable_widget(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a Nuke panel containing the widget.

        Uses nukescripts.panels.registerWidgetAsPanel() for native docking.
        The widget is wrapped in a panel class that Nuke can manage.

        Args:
            widget: The QWidget to embed.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.

        Returns:
            The panel ID, or None if failed.
        """
        try:
            import nukescripts

            # Store the widget instance
            _PANEL_INSTANCES[object_name] = widget

            # Create a panel class that returns our widget
            # Nuke requires a class with a specific interface
            panel_id = f"com.auroraview.{object_name}"

            # Create a factory function that returns the widget
            def create_widget_factory(stored_widget: QWidget):
                """Create a factory class for the widget."""

                class PanelWidget:
                    """Wrapper class for Nuke panel."""

                    def __init__(self):
                        self.widget = stored_widget

                    def makeUI(self):
                        """Return the widget for Nuke to display."""
                        return self.widget

                return PanelWidget

            # Create and store the factory
            factory_class = create_widget_factory(widget)
            _PANEL_FACTORIES[object_name] = factory_class

            # Register the panel with Nuke
            # nukescripts.panels.registerWidgetAsPanel expects:
            # - widget class path (string)
            # - panel label
            # - panel ID
            # - create (bool) - whether to create immediately

            # Since we can't use a string path for our dynamic class,
            # we use a different approach: create a custom panel directly
            nukescripts.panels.registerWidgetAsPanel(
                f"auroraview_dcc_shelves.apps.nuke._get_panel_widget_{object_name}",
                title,
                panel_id,
                create=True,
            )

            logger.info(f"Nuke: Created dockable panel '{object_name}'")
            return panel_id

        except Exception as e:
            logger.error(f"Nuke: Failed to create dockable panel: {e}")
            # Fallback: try alternative approach using PythonPanel
            return self._create_python_panel(widget, title, object_name)

    def _create_python_panel(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a Nuke panel using nukescripts.PythonPanel.

        This is a fallback approach that creates a floating panel.

        Args:
            widget: The QWidget to embed.
            title: The title for the panel.
            object_name: Unique object name for the panel.

        Returns:
            The panel instance, or None if failed.
        """
        try:
            import nukescripts

            # Create a PythonPanel subclass
            class ShelfPanel(nukescripts.PythonPanel):
                """Custom panel for shelf widget."""

                def __init__(self, widget_to_embed: QWidget, panel_title: str):
                    nukescripts.PythonPanel.__init__(self, panel_title)
                    self._widget = widget_to_embed

                def makeUI(self):
                    """Return the widget for Nuke to display."""
                    return self._widget

            # Create and show the panel
            panel = ShelfPanel(widget, title)
            panel.setMinimumSize(300, 200)

            # Store reference
            _PANEL_INSTANCES[object_name] = widget

            # Show as modal or add to pane
            # For docking, we need to add to a pane
            panel.addToPane()

            logger.info(f"Nuke: Created Python panel '{object_name}'")
            return panel

        except Exception as e:
            logger.error(f"Nuke: Failed to create Python panel: {e}")
            return None

    def show_dockable(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
        **kwargs: Any,
    ) -> bool:
        """Show a widget as a dockable panel in Nuke.

        Args:
            widget: The QWidget to show as dockable.
            title: The title for the dockable panel.
            object_name: Unique object name for the panel.
            **kwargs: Additional options:
                - pane: Pane name to dock to

        Returns:
            True if the dockable panel was created successfully.
        """
        panel = self.create_dockable_widget(widget, title, object_name)
        if panel:
            try:
                pane = kwargs.get("pane")
                if pane:
                    # Try to dock to specific pane
                    import nuke

                    nuke.executeInMainThread(lambda: self._dock_to_pane(panel, pane))
                return True
            except Exception as e:
                logger.error(f"Nuke: Failed to configure dockable panel: {e}")
                return False
        return False

    def _dock_to_pane(self, panel: Any, pane_name: str) -> None:
        """Dock a panel to a specific pane.

        Args:
            panel: The panel to dock.
            pane_name: The name of the pane to dock to.
        """
        try:
            # Nuke's pane system is complex; this is a simplified approach
            logger.debug(f"Nuke: Attempting to dock to pane '{pane_name}'")
        except Exception as e:
            logger.debug(f"Nuke: Failed to dock to pane: {e}")

    def restore_dockable(self, object_name: str) -> bool:
        """Restore a Nuke dockable panel.

        Args:
            object_name: The unique object name of the panel.

        Returns:
            True if the panel was restored successfully.
        """
        if object_name in _PANEL_INSTANCES:
            widget = _PANEL_INSTANCES[object_name]
            if widget:
                widget.show()
                logger.info(f"Nuke: Restored dockable panel '{object_name}'")
                return True
        return False

    def close_dockable(self, object_name: str) -> bool:
        """Close a Nuke dockable panel.

        Args:
            object_name: The unique object name of the panel.

        Returns:
            True if the panel was closed successfully.
        """
        try:
            # Remove from registries
            if object_name in _PANEL_INSTANCES:
                widget = _PANEL_INSTANCES[object_name]
                if widget:
                    widget.close()
                    widget.deleteLater()
                del _PANEL_INSTANCES[object_name]

            if object_name in _PANEL_FACTORIES:
                del _PANEL_FACTORIES[object_name]

            logger.info(f"Nuke: Closed dockable panel '{object_name}'")
            return True
        except Exception as e:
            logger.error(f"Nuke: Failed to close dockable panel: {e}")
            return False
