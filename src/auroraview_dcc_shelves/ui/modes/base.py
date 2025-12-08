"""Base mode mixin for DCC Shelves UI.

This module provides the base class for all integration mode mixins.
Each mode (Qt, dockable, HWND, standalone) inherits from this base.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from auroraview import WebView

logger = logging.getLogger(__name__)

# Path to the frontend dist directory
DIST_DIR = Path(__file__).parent.parent.parent.parent.parent / "dist"


class ModeMixin:
    """Base mixin class for integration modes.

    This class provides common functionality shared by all modes,
    including content loading, API registration, and event handling.

    Subclasses should implement the specific _show_*_mode method.
    """

    # These attributes are expected to be set by ShelfApp
    _webview: Any
    _api: Any
    _debug: bool
    _current_host: str
    _integration_mode: str
    _init_params: dict[str, Any]

    def _load_content(self) -> None:
        """Load the frontend content into the WebView."""
        if self._webview is None:
            return

        # Get dist directory
        dist_dir = DIST_DIR
        if not dist_dir.exists():
            logger.warning(f"Dist directory not found: {dist_dir}")
            return

        # Load the index.html file
        index_path = dist_dir / "index.html"
        if not index_path.exists():
            logger.error(f"Index file not found: {index_path}")
            return

        # On Windows, use auroraview.localhost protocol
        if sys.platform == "win32":
            auroraview_url = "https://auroraview.localhost/index.html"
        else:
            auroraview_url = "auroraview://index.html"

        logger.info(f"Loading URL: {auroraview_url}")
        self._webview.load_url(auroraview_url)

    def _register_api(self, webview: WebView) -> None:
        """Register the ShelfAPI with the WebView.

        Args:
            webview: The WebView instance to register API with.
        """
        if self._api is None:
            return

        if hasattr(webview, "bind_api"):
            webview.bind_api(self._api)
            logger.info("ShelfAPI bound successfully")

    def _register_api_methods_rust(self) -> None:
        """Register API methods using Rust's high-performance register_api_methods.

        This uses the Rust core's register_api_methods which generates optimized
        JavaScript code at compile time via Askama templates.
        """
        if self._webview is None or self._api is None:
            return

        # Get all public methods from ShelfAPI
        method_names = []
        for name in dir(self._api):
            if name.startswith("_"):
                continue
            attr = getattr(self._api, name)
            if callable(attr):
                method_names.append(name)

        if not method_names:
            return

        # Use Rust's register_api_methods for high-performance registration
        try:
            core = getattr(self._webview, "_core", None)
            if core is not None and hasattr(core, "register_api_methods"):
                core.register_api_methods("api", method_names)
                logger.debug(f"Registered {len(method_names)} API methods via Rust")
            else:
                logger.warning("Rust core not available, API methods not registered")
        except Exception as e:
            logger.warning(f"Failed to register API methods via Rust: {e}")
