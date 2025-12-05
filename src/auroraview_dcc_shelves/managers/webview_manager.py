"""WebView Manager for ShelfApp.

This module handles WebView initialization, configuration, and event handling
for different integration modes:
- Qt mode: QtWebView with deferred initialization
- Dockable mode: QtWebView in dockable container
- HWND mode: WebView in background thread

The WebViewManager delegates DCC-specific behavior to the adapter's hooks.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from auroraview_dcc_shelves.apps.base import DCCAdapter

logger = logging.getLogger(__name__)


class WebViewManager:
    """Manages WebView initialization and configuration for ShelfApp.

    This class encapsulates all WebView-related logic, delegating
    DCC-specific behavior to the adapter's hooks.

    Attributes:
        adapter: The DCC adapter for DCC-specific behavior.
        webview: The WebView instance.
        auroraview: The AuroraView wrapper instance.
    """

    def __init__(
        self,
        adapter: "DCCAdapter | None" = None,
        dist_dir: Path | None = None,
    ) -> None:
        """Initialize the WebViewManager.

        Args:
            adapter: DCC adapter for DCC-specific behavior.
            dist_dir: Path to the frontend dist directory.
        """
        self._adapter = adapter
        self._dist_dir = dist_dir
        self._webview: Any = None
        self._auroraview: Any = None
        self._placeholder: Any = None
        self._webview_proxy: Any = None

        # Navigation state
        self._is_loading = False
        self._load_progress = 0
        self._current_url = ""

    @property
    def webview(self) -> Any:
        """Get the WebView instance."""
        return self._webview

    @property
    def auroraview(self) -> Any:
        """Get the AuroraView wrapper instance."""
        return self._auroraview

    @property
    def webview_proxy(self) -> Any:
        """Get the WebViewProxy for cross-thread access."""
        return self._webview_proxy

    def set_adapter(self, adapter: "DCCAdapter") -> None:
        """Set the DCC adapter.

        Args:
            adapter: DCC adapter for DCC-specific behavior.
        """
        self._adapter = adapter

    def set_dist_dir(self, dist_dir: Path) -> None:
        """Set the dist directory path.

        Args:
            dist_dir: Path to the frontend dist directory.
        """
        self._dist_dir = dist_dir

    def is_dev_mode(self) -> bool:
        """Check if running in development mode.

        Returns:
            True if dev mode (no dist build), False otherwise.
        """
        if self._dist_dir is None:
            return True
        return not (self._dist_dir / "index.html").exists()

    def get_asset_root(self) -> str | None:
        """Get the asset root directory for WebView.

        Returns:
            Asset root path string, or None for dev mode.
        """
        if self.is_dev_mode():
            return None
        return str(self._dist_dir) if self._dist_dir else None

    def get_webview_params(self, debug: bool = False) -> dict[str, Any]:
        """Get WebView creation parameters.

        Args:
            debug: Whether debug mode is enabled.

        Returns:
            Dictionary of WebView creation parameters.
        """
        # Try adapter's get_webview_params hook first
        if self._adapter:
            params = self._adapter.get_webview_params(debug)
            if params:
                return params

        # Default parameters
        return {
            "dev_tools": debug,
            "context_menu": debug,
        }

    def create_qt_webview_deferred(
        self,
        parent: "QWidget",
        width: int,
        height: int,
        debug: bool = False,
        on_ready: Callable[..., None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> Any:
        """Create QtWebView with deferred initialization.

        Args:
            parent: Parent widget.
            width: WebView width.
            height: WebView height.
            debug: Whether debug mode is enabled.
            on_ready: Callback when WebView is ready.
            on_error: Callback on error.

        Returns:
            Placeholder widget for the WebView.
        """
        from auroraview import QtWebView

        asset_root = self.get_asset_root()
        params = self.get_webview_params(debug)

        logger.info(f"Creating QtWebView with create_deferred...")
        logger.info(f"  - parent: {parent}")
        logger.info(f"  - size: {width}x{height}")
        logger.info(f"  - dev_tools: {params.get('dev_tools', debug)}")
        logger.info(f"  - asset_root: {asset_root}")

        try:
            self._placeholder = QtWebView.create_deferred(
                parent=parent,
                width=width,
                height=height,
                dev_tools=params.get("dev_tools", debug),
                context_menu=params.get("context_menu", debug),
                asset_root=asset_root,
                embed_mode="owner",
                on_ready=on_ready,
                on_error=on_error or self._on_webview_error,
            )
            logger.info(f"  - placeholder created: {self._placeholder}")
            return self._placeholder
        except Exception as e:
            logger.error(f"Failed to create QtWebView: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def setup_webview(
        self,
        webview: Any,
        min_width: int,
        min_height: int,
    ) -> None:
        """Setup WebView after it's ready.

        Args:
            webview: The WebView instance.
            min_width: Minimum width.
            min_height: Minimum height.
        """
        from qtpy.QtWidgets import QSizePolicy

        self._webview = webview
        self._webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._webview.setMinimumSize(min_width, min_height)

        # Apply DCC-specific WebView configuration via hook
        if self._adapter:
            self._adapter.configure_webview(self._webview)
            logger.debug(f"Applied {self._adapter.name} WebView configuration")

    def create_auroraview_wrapper(
        self,
        parent: "QWidget",
        api: Any,
        keep_alive_root: "QWidget | None" = None,
    ) -> Any:
        """Create AuroraView wrapper for the WebView.

        Args:
            parent: Parent widget.
            api: ShelfAPI instance.
            keep_alive_root: Widget to keep alive.

        Returns:
            AuroraView wrapper instance.
        """
        from auroraview import AuroraView

        self._auroraview = AuroraView(
            parent=parent,
            api=api,
            _view=self._webview,
            _keep_alive_root=keep_alive_root or parent,
        )
        return self._auroraview

    def bind_api(self, api: Any) -> None:
        """Bind API to the WebView.

        Args:
            api: ShelfAPI instance to bind.
        """
        if self._webview and hasattr(self._webview, "bind_api"):
            logger.info("Explicitly binding ShelfAPI to QtWebView...")
            self._webview.bind_api(api)
            logger.info("ShelfAPI bound successfully")

    def load_content(self) -> None:
        """Load the frontend content into the WebView."""
        if self._webview is None:
            logger.warning("Cannot load content: WebView not initialized")
            return

        logger.info(f"Loading content, dist_dir={self._dist_dir}")

        if self.is_dev_mode():
            dev_url = "http://localhost:5173"
            logger.info(f"Loading dev URL: {dev_url}")
            self._webview.load_url(dev_url)
        else:
            index_path = self._dist_dir / "index.html"
            if index_path.exists():
                resolved_path = str(index_path.resolve())
                logger.info(f"Loading file: {resolved_path}")
                self._webview.load_file(resolved_path)
            else:
                logger.error(f"index.html not found at {index_path}")
                raise FileNotFoundError(f"index.html not found at {index_path}")

    def get_content_url(self) -> str:
        """Get the URL to load in WebView.

        Returns:
            URL string.
        """
        # Try adapter's get_content_url hook first
        if self._adapter:
            url = self._adapter.get_content_url(self.is_dev_mode())
            if url:
                return url

        # Default URL
        if self.is_dev_mode():
            return "http://localhost:5173"

        import sys
        if sys.platform == "win32":
            return "https://auroraview.localhost/index.html"
        return "auroraview://index.html"

    def connect_qt_signals(
        self,
        on_load_progress: Callable[[int], None] | None = None,
        on_url_changed: Callable[[str], None] | None = None,
        on_title_changed: Callable[[str], None] | None = None,
    ) -> None:
        """Connect Qt signals for navigation events.

        Args:
            on_load_progress: Callback for load progress.
            on_url_changed: Callback for URL changes.
            on_title_changed: Callback for title changes.
        """
        if self._webview is None:
            return

        try:
            if hasattr(self._webview, "loadProgress") and on_load_progress:
                self._webview.loadProgress.connect(on_load_progress)
            if hasattr(self._webview, "urlChanged") and on_url_changed:
                self._webview.urlChanged.connect(on_url_changed)
            if hasattr(self._webview, "titleChanged") and on_title_changed:
                self._webview.titleChanged.connect(on_title_changed)
            logger.debug("Qt signals connected")
        except Exception as e:
            logger.warning(f"Failed to connect Qt signals: {e}")

    def eval_js(self, script: str) -> bool:
        """Execute JavaScript in the WebView.

        Args:
            script: JavaScript code to execute.

        Returns:
            True if successful, False otherwise.
        """
        # Try thread-safe proxy first (for HWND mode)
        if self._webview_proxy is not None:
            try:
                self._webview_proxy.eval_js(script)
                return True
            except Exception as e:
                logger.warning(f"WebViewProxy eval_js failed: {e}")

        # Fall back to direct WebView call
        if self._webview is None:
            logger.warning("WebView not initialized")
            return False

        try:
            if hasattr(self._webview, "eval_js"):
                self._webview.eval_js(script)
                return True
        except Exception as e:
            logger.error(f"eval_js failed: {e}")
            return False

        return False

    def get_view_for_eval(self) -> Any:
        """Get the view instance that supports eval_js.

        Returns:
            View instance with eval_js method.
        """
        if self._auroraview:
            if hasattr(self._auroraview, "view"):
                return self._auroraview.view
            return self._auroraview
        return self._webview

    def cleanup_placeholder(self) -> None:
        """Cleanup the placeholder widget."""
        if self._placeholder:
            self._placeholder.deleteLater()
            self._placeholder = None

    def show(self) -> None:
        """Show the WebView."""
        if self._webview:
            self._webview.show()

    def cleanup(self) -> None:
        """Cleanup WebView resources."""
        self._webview = None
        self._auroraview = None
        self._placeholder = None
        self._webview_proxy = None

    def _on_webview_error(self, error_msg: str) -> None:
        """Handle WebView creation error.

        Args:
            error_msg: Error message.
        """
        logger.error(f"Failed to create WebView: {error_msg}")

