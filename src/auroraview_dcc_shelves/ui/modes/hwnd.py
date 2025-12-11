"""HWND integration mode for DCC Shelves UI.

This module provides HWND-based window integration for applications
that don't support Qt well (Unreal Engine, non-Qt applications).

Architecture:
    HWND mode runs WebView in a background thread to avoid blocking
    the DCC main thread. Key considerations:

    1. WebView event loop runs in background thread
    2. Python API callbacks execute in the background thread
    3. For DCC operations that require main thread, use deferred execution
    4. Use show() with auto_show=True for non-blocking operation

Threading Model:
    Main Thread (DCC)    Background Thread (WebView)
    ----------------     ---------------------------
    |  app.show()   | -> |  WebView creation       |
    |  (returns)    |    |  API binding            |
    |               |    |  Event loop (blocking)  |
    |  DCC ops...   |    |  IPC handling           |
    ----------------     ---------------------------

Cross-Thread Safety:
    WebView is marked as 'unsendable' in PyO3, meaning it cannot be
    accessed from a different thread than it was created on. To safely
    call eval_js() or emit() from the main DCC thread, use WebViewProxy:

    >>> # In background thread
    >>> webview = WebView(...)
    >>> proxy = webview.get_proxy()  # Thread-safe proxy
    >>>
    >>> # From main thread - safe!
    >>> proxy.eval_js("console.log('Hello!')")

Notes:
    - DCC-specific API methods should use executeDeferred if needed
    - Qt mode is preferred for DCC apps with Qt support
    - HWND mode is best for Unreal Engine or non-Qt environments
    - Use self._webview_proxy for cross-thread JS execution
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import TYPE_CHECKING, Any, Callable

from auroraview_dcc_shelves.ui.modes.base import DIST_DIR, ModeMixin

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HWNDModeMixin(ModeMixin):
    """Mixin for HWND window integration mode.

    This mode creates a standalone WebView window that can be embedded
    using HWND APIs. The window follows the parent but is not a true
    Qt child widget.

    Best for: Unreal Engine, non-Qt applications, or when Qt mode
    causes issues with the DCC main thread.

    Thread Safety:
        - WebView runs in a daemon background thread
        - API callbacks execute in the background thread
        - For DCC operations, use self._run_on_main_thread()
        - For cross-thread JS execution, use self._webview_proxy

    Attributes:
        _webview_proxy: Thread-safe proxy for cross-thread WebView operations.
            Use this instead of self._webview for eval_js/emit from main thread.
    """

    # Expected attributes from ShelfApp
    _title: str
    _width: int
    _height: int
    _default_width: int
    _default_height: int
    # Whether we are running inside a DCC (Qt-based) host. The corresponding
    # state key exposed to the frontend is still named "dcc_mode" for
    # backward compatibility.
    _is_dcc_environment: bool
    _current_host: str
    _webview_thread: threading.Thread
    _main_thread_queue: queue.Queue[tuple[Callable[..., Any], tuple, dict]]
    _hwnd_ready_event: threading.Event
    _webview_proxy: Any  # WebViewProxy - thread-safe proxy for cross-thread access

    def _show_hwnd_mode(self, debug: bool, app: str) -> None:
        """Show using AuroraView with HWND integration (non-blocking).

        This mode creates a standalone WebView window that can be embedded
        using HWND APIs. The window follows the parent but is not a true
        Qt child widget.

        The WebView runs in a background thread, freeing the main thread
        for DCC operations. API callbacks execute in the background thread.

        Best for: Unreal Engine, non-Qt applications, or when Qt mode
        causes issues with the DCC main thread.

        Args:
            debug: Enable DevTools for debugging.
            app: DCC application name (e.g., "maya", "unreal").
        """
        from auroraview_dcc_shelves.ui.api import ShelfAPI

        # Window size is fixed - use default values
        self._width = self._default_width
        self._height = self._default_height

        dist_dir = str(DIST_DIR) if not self._is_dev_mode() else None

        logger.info("HWND mode - Starting WebView in background thread...")

        # Initialize synchronization primitives
        self._main_thread_queue = queue.Queue()
        self._hwnd_ready_event = threading.Event()

        # Create API (will be bound in background thread)
        self._api = ShelfAPI(self)

        def _create_webview_thread() -> None:
            """Create WebView in background thread (STA-compatible).

            This function runs entirely in the background thread:
            1. Creates WebView instance
            2. Gets thread-safe proxy for cross-thread access
            3. Binds API for IPC
            4. Loads content
            5. Runs event loop (blocking until window closes)
            """
            try:
                from auroraview import WebView

                logger.info("HWND thread - Creating WebView...")

                # Create WebView directly (not AuroraView wrapper)
                # The WebView manages its own event loop in this thread
                webview = WebView(
                    title=self._title,
                    width=self._width,
                    height=self._height,
                    debug=debug,
                    context_menu=debug,  # Enable context menu in debug mode
                    asset_root=dist_dir,
                )

                # Store WebView reference (for same-thread access only!)
                # WARNING: Do NOT call webview.eval_js() from main thread!
                self._webview = webview

                # Get thread-safe proxy for cross-thread JavaScript execution
                # Use self._webview_proxy.eval_js() from main DCC thread
                try:
                    self._webview_proxy = webview.get_proxy()
                    logger.info("HWND thread - WebViewProxy obtained for cross-thread access")
                except AttributeError:
                    # Fallback for older versions without get_proxy()
                    logger.warning("HWND thread - get_proxy() not available, cross-thread eval_js will not work!")
                    self._webview_proxy = None

                # Bind API - handlers will execute in this background thread
                logger.info("HWND thread - Binding API...")
                webview.bind_api(self._api)
                logger.info("HWND thread - API bound successfully")

                # Load content before showing
                if self._is_dev_mode():
                    dev_url = "http://localhost:5173"
                    logger.info(f"HWND thread - Loading dev URL: {dev_url}")
                    webview.load_url(dev_url)
                else:
                    index_path = DIST_DIR / "index.html"
                    if index_path.exists():
                        file_url = f"file:///{index_path.resolve().as_posix()}"
                        logger.info(f"HWND thread - Loading file: {file_url}")
                        webview.load_file(str(index_path.resolve()))
                    else:
                        logger.error(f"HWND thread - index.html not found: {index_path}")

                # Setup shared state
                logger.info("HWND thread - Setting up shared state...")
                state = webview.state
                with state.batch_update() as batch:
                    batch["app_name"] = self._title
                    # Keep the state key name "dcc_mode" stable while using
                    # the clearer internal flag _is_dcc_environment on the
                    # Python side.
                    batch["dcc_mode"] = self._is_dcc_environment
                    batch["current_host"] = self._current_host
                    batch["theme"] = "dark"
                    batch["integration_mode"] = self._integration_mode

                # Signal that WebView is ready
                self._hwnd_ready_event.set()
                logger.info("HWND thread - WebView ready, signaled main thread")

                logger.info("HWND thread - Starting WebView event loop (blocking this thread)...")

                # This blocks until the window is closed
                # The Rust event loop handles window messages and IPC
                webview.show_blocking()

                logger.info("HWND thread - WebView event loop exited, window closed")

            except Exception as e:
                logger.error(f"HWND thread - Error: {e}", exc_info=True)
                # Signal ready even on error to prevent main thread from waiting forever
                self._hwnd_ready_event.set()

        # Start WebView in background thread (daemon so it doesn't block app exit)
        self._webview_thread = threading.Thread(
            target=_create_webview_thread,
            name="AuroraView-HWND",
            daemon=True,
        )
        self._webview_thread.start()

        # Wait briefly for WebView to initialize (optional, improves reliability)
        # This ensures the WebView is ready before returning to caller
        if self._hwnd_ready_event.wait(timeout=10.0):
            logger.info("HWND mode - WebView initialized, main thread free!")
        else:
            logger.warning("HWND mode - WebView initialization timeout, proceeding anyway...")

        logger.info("HWND mode - Background thread started, returning control to main thread")

    def _run_on_main_thread(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Queue a function to run on the main thread.

        Use this for DCC operations that must run on the main thread
        (e.g., Maya commands, Houdini node operations).

        Args:
            func: Function to execute on main thread.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Note:
            The caller is responsible for processing the queue.
            In DCC apps, use an idle callback or timer to process.
        """
        if hasattr(self, "_main_thread_queue"):
            self._main_thread_queue.put((func, args, kwargs))
        else:
            logger.warning("Main thread queue not initialized, executing directly")
            func(*args, **kwargs)

    def _process_main_thread_queue(self) -> int:
        """Process pending main thread callbacks.

        Returns:
            Number of callbacks processed.

        Note:
            Call this from the main thread (e.g., via idle callback).
        """
        if not hasattr(self, "_main_thread_queue"):
            return 0

        processed = 0
        while True:
            try:
                func, args, kwargs = self._main_thread_queue.get_nowait()
                try:
                    func(*args, **kwargs)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error in main thread callback: {e}")
            except queue.Empty:
                break

        return processed

    def eval_js_safe(self, script: str) -> bool:
        """Execute JavaScript safely from any thread.

        This method uses WebViewProxy to safely execute JavaScript
        even when called from the main DCC thread (different from
        the WebView's background thread).

        Args:
            script: JavaScript code to execute.

        Returns:
            True if the script was queued successfully, False otherwise.

        Example:
            >>> # From main DCC thread - safe!
            >>> app.eval_js_safe("console.log('Hello from DCC!')")
            >>> app.eval_js_safe("document.title = 'Updated'")

        Note:
            The script is queued and executed asynchronously by the
            WebView's event loop. There's no return value - use
            events for two-way communication.
        """
        if not hasattr(self, "_webview_proxy") or self._webview_proxy is None:
            logger.warning("WebViewProxy not available, cannot execute JavaScript safely")
            return False

        try:
            self._webview_proxy.eval_js(script)
            return True
        except Exception as e:
            logger.error(f"Failed to queue JavaScript for execution: {e}")
            return False

    def emit_safe(self, event_name: str, data: dict[str, Any] | None = None) -> bool:
        """Emit an event safely from any thread.

        This method uses WebViewProxy to safely emit events
        even when called from the main DCC thread.

        Args:
            event_name: Name of the event to emit.
            data: Optional data to include with the event.

        Returns:
            True if the event was queued successfully, False otherwise.

        Example:
            >>> # From main DCC thread - safe!
            >>> app.emit_safe("update_status", {"message": "Processing..."})
        """
        if not hasattr(self, "_webview_proxy") or self._webview_proxy is None:
            logger.warning("WebViewProxy not available, cannot emit event safely")
            return False

        try:
            self._webview_proxy.emit(event_name, data or {})
            return True
        except Exception as e:
            logger.error(f"Failed to queue event for emission: {e}")
            return False
