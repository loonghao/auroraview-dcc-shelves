"""AuroraView DCC Shelves - A dynamic tool shelf system for DCC software.

This package provides a configurable tool shelf system powered by AuroraView,
allowing you to organize and launch Python scripts and executables from a
modern web-based UI.

Example (Standalone):
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show()

Example (Desktop mode):
    >>> # Via command line
    >>> # python -m auroraview_dcc_shelves -c shelf_config.yaml
    >>> # auroraview-shelves -c shelf_config.yaml

    >>> # Via Python
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show(app="desktop", mode="qt")

Example (Maya with Qt mode - recommended):
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show(app="maya", mode="qt")

Example (Maya with dockable panel):
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show(app="maya", mode="qt", dockable=True)

Example (Houdini integration):
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show(app="houdini", mode="qt")
"""

from auroraview_dcc_shelves.config import (
    BannerConfig,
    ButtonConfig,
    CircularReferenceError,
    ConfigError,
    ShelfConfig,
    ShelvesConfig,
    ToolType,
    load_config,
    validate_config,
)
from auroraview_dcc_shelves.launcher import ToolLauncher
from auroraview_dcc_shelves.settings import WindowSettings, WindowSettingsManager
from auroraview_dcc_shelves.ui import ShelfApp

__version__ = "0.3.0"
__author__ = "Hal Long"
__email__ = "hal.long@outlook.com"

__all__ = [
    # Config
    "BannerConfig",
    "ButtonConfig",
    "CircularReferenceError",
    "ConfigError",
    "ShelfConfig",
    "ShelvesConfig",
    "ToolType",
    "load_config",
    "validate_config",
    # Launcher
    "ToolLauncher",
    # Settings
    "WindowSettings",
    "WindowSettingsManager",
    # UI
    "ShelfApp",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]
