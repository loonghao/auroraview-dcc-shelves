"""Standalone mode for DCC Shelves UI.

This module provides standalone WebView mode for running outside
of DCC applications (testing, development, standalone usage).
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from auroraview_dcc_shelves.ui.modes.base import DIST_DIR, ModeMixin

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StandaloneModeMixin(ModeMixin):
    """Mixin for standalone WebView mode.

    This mode creates a regular WebView window for standalone usage
    outside of DCC applications. Useful for testing and development.
    """

    # Expected attributes from ShelfApp
    _title: str
    _width: int
    _height: int
    _default_width: int
    _default_height: int
    _adapter: Any

    def _show_standalone_mode(self, debug: bool) -> None:
        """Show using regular WebView for standalone mode (blocking)."""
        from auroraview import WebView

        from auroraview_dcc_shelves.ui.api import ShelfAPI

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        create_params: dict[str, Any] = {
            "title": self._title,
            "width": self._width,
            "height": self._height,
            "debug": debug,
        }

        if self._is_dev_mode():
            dev_url = "http://localhost:5173"
            logger.info(f"Standalone mode - Loading dev URL: {dev_url}")
            create_params["url"] = dev_url
            self._webview = WebView.create(**create_params)
        else:
            logger.info("Standalone mode - Loading production build")
            create_params["asset_root"] = str(DIST_DIR)
            self._webview = WebView.create(**create_params)

            if sys.platform == "win32":
                auroraview_url = "https://auroraview.localhost/index.html"
            else:
                auroraview_url = "auroraview://index.html"

            logger.info(f"Loading URL: {auroraview_url}")
            self._webview.load_url(auroraview_url)

        self._api = ShelfAPI(self)
        self._register_api(self._webview)
        self._setup_shared_state()
        self._register_commands()
        self._webview.show()

        # Call adapter's on_show hook
        if self._adapter:
            self._adapter.on_show(self)
