"""AuroraView DCC Shelves Plugin for Substance 3D Painter.

This plugin adds a menu item to Substance Painter's Python menu
for quick access to the DCC Shelves tool.

Installation:
1. Copy the 'substance_painter_plugin' folder to:
   - Windows: %USERPROFILE%/Documents/Adobe/Adobe Substance 3D Painter/python/plugins/
   - macOS: ~/Documents/Adobe/Adobe Substance 3D Painter/python/plugins/
   - Linux: ~/.local/share/Adobe/Adobe Substance 3D Painter/python/plugins/

2. Rename the folder to 'auroraview_dcc_shelves_plugin' (optional)

3. Restart Substance Painter or reload plugins from Python menu

The plugin will add a "DCC Shelves" submenu under Python > Plugins menu.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import substance_painter.ui

# Plugin metadata
PLUGIN_NAME = "AuroraView DCC Shelves"
PLUGIN_VERSION = "0.1.0"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auroraview_dcc_shelves_plugin")

# Development source path - update this for your environment
DEV_SOURCE_PATH = Path(r"C:\github\auroraview-dcc-shelves\src")
sys.path.insert(0, r"C:\Users\hallo\Documents\augment-projects\dcc_webview\python")

# Global state
_shelf_app = None
_menu_actions = []


def _ensure_path():
    """Ensure the development source path is in sys.path."""
    if DEV_SOURCE_PATH.exists() and str(DEV_SOURCE_PATH) not in sys.path:
        sys.path.insert(0, str(DEV_SOURCE_PATH))
        logger.info(f"Added dev source path: {DEV_SOURCE_PATH}")


def _reload_modules():
    """Force reload of auroraview and auroraview_dcc_shelves modules for development."""
    # Reload both auroraview (core) and auroraview_dcc_shelves
    modules_to_reload = [
        m for m in sys.modules.keys()
        if m.startswith("auroraview_dcc_shelves") or m.startswith("auroraview")
    ]
    for mod_name in sorted(modules_to_reload, reverse=True):  # Unload children first
        del sys.modules[mod_name]
        logger.debug(f"Unloaded: {mod_name}")
    logger.info(f"Unloaded {len(modules_to_reload)} modules for hot reload")


def _load_shelf_config():
    """Load shelf configuration from YAML file."""
    from auroraview_dcc_shelves.config import load_config
    config_path = DEV_SOURCE_PATH.parent / "examples" / "shelf_config_modular.yaml"
    return load_config(config_path)


def show_shelf():
    """Show the DCC Shelves window."""
    global _shelf_app

    try:
        logger.info("[Plugin] show_shelf() called")
        _ensure_path()
        logger.info("[Plugin] Path ensured")
        _reload_modules()
        logger.info("[Plugin] Modules reloaded")

        from auroraview_dcc_shelves import ShelfApp
        logger.info("[Plugin] ShelfApp imported")

        # Close existing
        if _shelf_app is not None:
            try:
                _shelf_app.close()
            except Exception:
                pass

        logger.info("[Plugin] Loading config...")
        config = _load_shelf_config()
        logger.info("[Plugin] Config loaded")

        logger.info("[Plugin] Creating ShelfApp...")
        _shelf_app = ShelfApp(config)
        logger.info("[Plugin] ShelfApp created, calling show()...")

        _shelf_app.show(debug=False, app="substancepainter")
        logger.info("[Plugin] show() returned! Shelf opened successfully")

    except Exception as e:
        logger.error(f"Failed to show shelf: {e}")
        import traceback
        traceback.print_exc()


def show_shelf_debug():
    """Show the DCC Shelves window with DevTools enabled."""
    global _shelf_app

    try:
        _ensure_path()
        _reload_modules()

        from auroraview_dcc_shelves import ShelfApp

        if _shelf_app is not None:
            try:
                _shelf_app.close()
            except Exception:
                pass

        config = _load_shelf_config()
        _shelf_app = ShelfApp(config)
        _shelf_app.show(debug=True, app="substancepainter")
        logger.info("Shelf opened in debug mode")

    except Exception as e:
        logger.error(f"Failed to show shelf: {e}")
        import traceback
        traceback.print_exc()


def close_shelf():
    """Close the DCC Shelves window."""
    global _shelf_app

    if _shelf_app is not None:
        try:
            _shelf_app.close()
            logger.info("Shelf closed")
        except Exception as e:
            logger.warning(f"Error closing shelf: {e}")
        finally:
            _shelf_app = None


def reload_shelf():
    """Reload the shelf (hot reload for development)."""
    close_shelf()
    show_shelf()


def start_plugin():
    """Called when the plugin is loaded by Substance Painter."""
    global _menu_actions

    logger.info(f"Starting {PLUGIN_NAME} v{PLUGIN_VERSION}")

    try:
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QApplication

        # Get main window as parent for actions
        main_window = substance_painter.ui.get_main_window()

        menu = substance_painter.ui.ApplicationMenu.Window

        # Create QAction objects
        action_open = QAction("DCC Shelves - Open", main_window)
        action_open.triggered.connect(show_shelf)
        substance_painter.ui.add_action(menu, action_open)
        _menu_actions.append(action_open)

        action_debug = QAction("DCC Shelves - Debug", main_window)
        action_debug.triggered.connect(show_shelf_debug)
        substance_painter.ui.add_action(menu, action_debug)
        _menu_actions.append(action_debug)

        action_close = QAction("DCC Shelves - Close", main_window)
        action_close.triggered.connect(close_shelf)
        substance_painter.ui.add_action(menu, action_close)
        _menu_actions.append(action_close)

        action_reload = QAction("DCC Shelves - Reload", main_window)
        action_reload.triggered.connect(reload_shelf)
        substance_painter.ui.add_action(menu, action_reload)
        _menu_actions.append(action_reload)

        logger.info("Plugin menu items added to Window menu")
    except Exception as e:
        logger.error(f"Failed to add menu items: {e}")
        import traceback
        traceback.print_exc()


def close_plugin():
    """Called when the plugin is unloaded."""
    global _menu_actions

    close_shelf()

    # Remove menu items
    for action in _menu_actions:
        substance_painter.ui.delete_ui_element(action)
    _menu_actions.clear()

    logger.info("Plugin unloaded")


# Plugin entry point
if __name__ == "__main__":
    start_plugin()

