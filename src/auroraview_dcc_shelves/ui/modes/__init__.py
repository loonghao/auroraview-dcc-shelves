"""UI integration modes for DCC Shelves.

This package contains different integration mode implementations:
- qt: Qt widget integration for DCC apps with Qt support (recommended)
      Uses createWindowContainer for native Qt layout integration with automatic resize.
- dockable: Dockable panel integration for DCC apps
- hwnd: Native window handle integration for non-Qt apps
- standalone: Standalone WebView mode
"""

from auroraview_dcc_shelves.ui.modes.base import ModeMixin
from auroraview_dcc_shelves.ui.modes.dockable import DockableModeMixin
from auroraview_dcc_shelves.ui.modes.hwnd import HWNDModeMixin
from auroraview_dcc_shelves.ui.modes.qt import QtModeMixin
from auroraview_dcc_shelves.ui.modes.standalone import StandaloneModeMixin

__all__ = [
    "ModeMixin",
    "QtModeMixin",
    "DockableModeMixin",
    "HWNDModeMixin",
    "StandaloneModeMixin",
]
