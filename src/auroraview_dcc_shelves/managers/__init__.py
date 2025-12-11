"""Managers for ShelfApp components.

This module provides manager classes that handle specific responsibilities:
- WindowManager: Window creation and configuration
- WebViewManager: WebView initialization and event handling
"""

from auroraview_dcc_shelves.managers.webview_manager import WebViewManager
from auroraview_dcc_shelves.managers.window_manager import WindowManager

__all__ = ["WindowManager", "WebViewManager"]
