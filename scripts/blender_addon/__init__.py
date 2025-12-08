"""AuroraView DCC Shelves Addon for Blender.

This addon adds menu items and operators for the DCC Shelves tool.

Installation:
1. Copy the 'blender_addon' folder to:
   - Windows: %APPDATA%/Blender/<version>/scripts/addons/
   - macOS: ~/Library/Application Support/Blender/<version>/scripts/addons/
   - Linux: ~/.config/blender/<version>/scripts/addons/

2. Rename the folder to 'auroraview_dcc_shelves' (recommended)

3. In Blender: Edit > Preferences > Add-ons > Search "AuroraView" > Enable

The addon will add:
- Menu: Window > DCC Shelves
- Operator: wm.auroraview_dcc_shelves_open
"""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path

import bpy

# Blender addon metadata (required)
bl_info = {
    "name": "AuroraView DCC Shelves",
    "author": "AuroraView Team",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "Window > DCC Shelves",
    "description": "Dynamic YAML-configurable tool shelf system",
    "warning": "",
    "doc_url": "https://github.com/loonghao/auroraview-dcc-shelves",
    "tracker_url": "https://github.com/loonghao/auroraview-dcc-shelves/issues",
    "category": "Interface",
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auroraview_dcc_shelves_addon")

# Development source path - update this for your environment
DEV_SOURCE_PATH = Path(r"C:\github\auroraview-dcc-shelves\src")
AURORAVIEW_PYTHON_PATH = Path(r"C:\Users\hallo\Documents\augment-projects\dcc_webview\python")

# Global state
_shelf_app = None


def _ensure_path():
    """Ensure the development source paths are in sys.path."""
    paths_to_add = [DEV_SOURCE_PATH, AURORAVIEW_PYTHON_PATH]
    for path in paths_to_add:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
            logger.info(f"Added path: {path}")


def _reload_modules():
    """Force reload of auroraview and auroraview_dcc_shelves modules for development."""
    modules_to_reload = [
        m for m in sys.modules if m.startswith("auroraview_dcc_shelves") or m.startswith("auroraview")
    ]
    for mod_name in sorted(modules_to_reload, reverse=True):
        del sys.modules[mod_name]
        logger.debug(f"Unloaded: {mod_name}")
    logger.info(f"Unloaded {len(modules_to_reload)} modules for hot reload")


def _load_shelf_config():
    """Load shelf configuration from YAML file."""
    from auroraview_dcc_shelves.config import load_config

    config_path = DEV_SOURCE_PATH.parent / "examples" / "shelf_config_modular.yaml"
    if not config_path.exists():
        config_path = DEV_SOURCE_PATH.parent / "examples" / "shelf_config.yaml"
    return load_config(config_path)


# ============================================================
# Operators
# ============================================================


class AURORAVIEW_OT_open_shelf(bpy.types.Operator):
    """Open the DCC Shelves window"""

    bl_idname = "wm.auroraview_dcc_shelves_open"
    bl_label = "Open DCC Shelves"
    bl_description = "Open the AuroraView DCC Shelves tool window"
    bl_options = {"REGISTER"}

    debug: bpy.props.BoolProperty(
        name="Debug Mode",
        description="Enable DevTools for debugging",
        default=False,
    )

    def execute(self, context):
        global _shelf_app

        try:
            logger.info("[Addon] Opening DCC Shelves...")
            _ensure_path()
            _reload_modules()

            from auroraview_dcc_shelves import ShelfApp

            # Close existing instance
            if _shelf_app is not None:
                with contextlib.suppress(Exception):
                    _shelf_app.close()
                _shelf_app = None

            config = _load_shelf_config()
            _shelf_app = ShelfApp(config)
            _shelf_app.show(debug=self.debug, app="blender")

            self.report({"INFO"}, "DCC Shelves opened")
            logger.info("[Addon] DCC Shelves opened successfully")

        except Exception as e:
            logger.error(f"Failed to open shelf: {e}")
            import traceback

            traceback.print_exc()
            self.report({"ERROR"}, f"Failed to open: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


class AURORAVIEW_OT_open_shelf_debug(bpy.types.Operator):
    """Open the DCC Shelves window with DevTools"""

    bl_idname = "wm.auroraview_dcc_shelves_open_debug"
    bl_label = "Open DCC Shelves (Debug)"
    bl_description = "Open DCC Shelves with DevTools enabled"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.auroraview_dcc_shelves_open(debug=True)
        return {"FINISHED"}


class AURORAVIEW_OT_close_shelf(bpy.types.Operator):
    """Close the DCC Shelves window"""

    bl_idname = "wm.auroraview_dcc_shelves_close"
    bl_label = "Close DCC Shelves"
    bl_description = "Close the AuroraView DCC Shelves window"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global _shelf_app

        if _shelf_app is not None:
            try:
                _shelf_app.close()
                self.report({"INFO"}, "DCC Shelves closed")
                logger.info("[Addon] DCC Shelves closed")
            except Exception as e:
                logger.warning(f"Error closing shelf: {e}")
                self.report({"WARNING"}, f"Error closing: {e}")
            finally:
                _shelf_app = None
        else:
            self.report({"INFO"}, "DCC Shelves not open")

        return {"FINISHED"}


class AURORAVIEW_OT_reload_shelf(bpy.types.Operator):
    """Reload the DCC Shelves (hot reload for development)"""

    bl_idname = "wm.auroraview_dcc_shelves_reload"
    bl_label = "Reload DCC Shelves"
    bl_description = "Close and reopen DCC Shelves with fresh modules"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.auroraview_dcc_shelves_close()
        bpy.ops.wm.auroraview_dcc_shelves_open()
        self.report({"INFO"}, "DCC Shelves reloaded")
        return {"FINISHED"}


# ============================================================
# Menu
# ============================================================


class AURORAVIEW_MT_shelf_menu(bpy.types.Menu):
    """DCC Shelves submenu"""

    bl_idname = "AURORAVIEW_MT_shelf_menu"
    bl_label = "DCC Shelves"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.auroraview_dcc_shelves_open", icon="WINDOW")
        layout.operator("wm.auroraview_dcc_shelves_open_debug", icon="CONSOLE")
        layout.separator()
        layout.operator("wm.auroraview_dcc_shelves_close", icon="PANEL_CLOSE")
        layout.operator("wm.auroraview_dcc_shelves_reload", icon="FILE_REFRESH")


def menu_func(self, context):
    """Add DCC Shelves submenu to Window menu."""
    self.layout.menu(AURORAVIEW_MT_shelf_menu.bl_idname, icon="TOOL_SETTINGS")


# ============================================================
# Registration
# ============================================================

classes = (
    AURORAVIEW_OT_open_shelf,
    AURORAVIEW_OT_open_shelf_debug,
    AURORAVIEW_OT_close_shelf,
    AURORAVIEW_OT_reload_shelf,
    AURORAVIEW_MT_shelf_menu,
)


def register():
    """Register the addon."""
    logger.info(f"Registering AuroraView DCC Shelves addon v{'.'.join(map(str, bl_info['version']))}")

    for cls in classes:
        bpy.utils.register_class(cls)

    # Add menu to Window menu
    bpy.types.TOPBAR_MT_window.append(menu_func)

    logger.info("Addon registered successfully")


def unregister():
    """Unregister the addon."""
    global _shelf_app

    logger.info("Unregistering AuroraView DCC Shelves addon")

    # Close shelf if open
    if _shelf_app is not None:
        with contextlib.suppress(Exception):
            _shelf_app.close()
        _shelf_app = None

    # Remove menu
    bpy.types.TOPBAR_MT_window.remove(menu_func)

    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    logger.info("Addon unregistered")


# For testing in Blender's text editor
if __name__ == "__main__":
    register()
