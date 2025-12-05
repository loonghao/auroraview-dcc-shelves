"""UI module for DCC Shelves.

This package contains the UI components for the DCC Shelves application:
- api: ShelfAPI class for JavaScript-Python communication
- modes: Integration mode implementations (Qt, dockable, HWND, standalone)

For backwards compatibility, ShelfApp is re-exported from the app module.
"""

from auroraview_dcc_shelves.app import ShelfApp
from auroraview_dcc_shelves.ui.api import ShelfAPI

__all__ = [
    "ShelfAPI",
    "ShelfApp",
]
