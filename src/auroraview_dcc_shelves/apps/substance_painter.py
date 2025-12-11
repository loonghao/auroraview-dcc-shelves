"""Substance 3D Painter DCC Adapter.

Handles Substance 3D Painter-specific integration including:
- Main window detection via substance_painter module
- PySide6/Qt6 optimizations for Painter 2021+
- Project and layer management APIs
- Balanced timer settings for texture painting workflows

Qt Version Notes:
    Substance 3D Painter 2021+ uses PySide6 (Qt6).
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
class SubstancePainterAdapter(DCCAdapter):
    """Adapter for Adobe Substance 3D Painter.

    Substance Painter-specific optimizations:
    - Balanced timer interval (32ms/30FPS) for painting workflows
    - Qt6 optimizations applied when detected
    - Project context awareness
    """

    name = "SubstancePainter"
    aliases = ["substancepainter", "painter", "sp", "substance_painter", "substance3dpainter"]
    timer_interval_ms = 32  # 30 FPS - balanced for texture painting
    recommended_mode = "qt"  # Qt mode with PySide6

    def __init__(self) -> None:
        """Initialize the Substance Painter adapter."""
        super().__init__()

    def _create_qt_config(self) -> QtConfig:
        """Create Qt configuration for Substance Painter.

        Substance Painter 2021+ uses Qt6 (PySide6).

        Returns:
            QtConfig with appropriate settings.
        """
        is_qt6 = _detect_qt6()
        logger.info(f"Substance Painter: {'Qt6' if is_qt6 else 'Qt5'} detected")

        return QtConfig(
            init_delay_ms=50,
            timer_interval_ms=32,
            # Extended delays for Qt6/PySide6 layout updates
            geometry_fix_delays=[50, 150, 300, 500, 1000],
            force_opaque_window=is_qt6,
            disable_translucent=is_qt6,
            is_qt6=is_qt6,
        )

    def get_main_window(self) -> Any | None:
        """Get Substance Painter main window as QWidget.

        Tries multiple methods:
        1. substance_painter.ui.get_main_window() (preferred)
        2. Fallback to searching QApplication top-level widgets
        """
        try:
            from qtpy.QtWidgets import QApplication
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Method 1: substance_painter.ui.get_main_window()
        try:
            import substance_painter.ui

            return substance_painter.ui.get_main_window()
        except Exception as e:
            logger.debug(f"substance_painter.ui.get_main_window() failed: {e}")

        # Method 2: Search by window title
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                title = widget.windowTitle()
                if "Substance" in title and "Painter" in title:
                    return widget

        logger.warning("Could not find Substance Painter main window")
        return None

    def configure_dialog(self, dialog: "QDialog") -> None:
        """Apply Qt6-specific dialog optimizations for Substance Painter.

        Args:
            dialog: The QDialog to configure.
        """
        super().configure_dialog(dialog)

        try:
            from qtpy.QtCore import Qt
            from auroraview.integration.qt._compat import apply_qt6_dialog_optimizations

            # Use frameless window - HTML content provides its own title bar
            # Qt.Tool keeps it as a tool window (stays on top of parent)
            dialog.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)

            # Apply Qt6 optimizations using unified function
            apply_qt6_dialog_optimizations(dialog)

            logger.debug("Substance Painter: Applied Qt6 frameless dialog optimizations")
        except Exception as e:
            logger.debug(f"Substance Painter: Failed to apply dialog config: {e}")

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Substance Painter-specific API methods."""
        return {
            "get_project_info": self._get_project_info,
            "get_current_layer": self._get_current_layer,
            "export_textures": self._export_textures,
            "execute_js": self._execute_js,
        }

    def _get_project_info(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current project information.

        Returns:
            Dict with project name and state.
        """
        try:
            import substance_painter.project

            if substance_painter.project.is_open():
                return {
                    "success": True,
                    "is_open": True,
                    "name": substance_painter.project.name(),
                    "file_path": substance_painter.project.file_path(),
                }
            return {"success": True, "is_open": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_current_layer(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current selected layer.

        Returns:
            Dict with layer information.
        """
        try:
            import substance_painter.layerstack
            import substance_painter.textureset

            texture_set = substance_painter.textureset.get_active_stack()
            if texture_set:
                layers = substance_painter.layerstack.get_selected_layers(texture_set)
                if layers:
                    layer = layers[0]
                    return {
                        "success": True,
                        "name": layer.name(),
                        "type": str(type(layer).__name__),
                    }
            return {"success": True, "layer": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _export_textures(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Export textures using current export settings.

        Args:
            params: Dict with optional "preset" key for export preset name.

        Returns:
            Dict with export status.
        """
        try:
            import substance_painter.export
            import substance_painter.project

            if not substance_painter.project.is_open():
                return {"success": False, "error": "No project open"}

            # Use default export or specified preset
            preset_name = params.get("preset") if params else None
            if preset_name:
                # Export with specified preset
                presets = substance_painter.export.list_project_export_presets()
                preset = next((p for p in presets if p.name() == preset_name), None)
                if preset:
                    substance_painter.export.export_project_textures(preset)
                    return {"success": True, "preset": preset_name}
                return {"success": False, "error": f"Preset not found: {preset_name}"}

            return {"success": True, "message": "Use specific preset name to export"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_js(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute JavaScript in Substance Painter.

        Args:
            params: Dict with "code" key containing JS code.

        Returns:
            Dict with execution result.
        """
        if not params or "code" not in params:
            return {"success": False, "error": "No code provided"}

        try:
            import substance_painter.js

            result = substance_painter.js.evaluate(params["code"])
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def on_init(self, shelf_app: Any) -> None:
        """Substance Painter-specific initialization."""
        logger.info("Substance Painter adapter initialized")
        logger.info(
            f"  Qt config: init_delay={self.qt_config.init_delay_ms}ms, timer={self.qt_config.timer_interval_ms}ms"
        )

    def supports_dockable(self) -> bool:
        """Substance Painter supports dockable panels."""
        return True
