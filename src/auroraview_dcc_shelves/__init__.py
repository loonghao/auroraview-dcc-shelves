"""AuroraView DCC Shelves - A dynamic tool shelf system for DCC software.

This package provides a configurable tool shelf system powered by AuroraView,
allowing you to organize and launch Python scripts and executables from a
modern web-based UI.

Example (Standalone):
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show()

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

Example (WebView2 Warmup for faster startup):
    >>> # In DCC startup script (e.g., userSetup.py)
    >>> from auroraview_dcc_shelves import start_warmup
    >>> start_warmup()  # Non-blocking background initialization
    >>>
    >>> # Later, when showing UI
    >>> from auroraview_dcc_shelves import ShelfApp, load_config
    >>> config = load_config("shelf_config.yaml")
    >>> app = ShelfApp(config)
    >>> app.show(app="maya")  # Much faster since WebView2 is already warmed up
"""

from auroraview_dcc_shelves.config import (
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

__version__ = "0.2.0"
__author__ = "Hal Long"
__email__ = "hal.long@outlook.com"


# =============================================================================
# Warmup API (convenience wrappers)
# =============================================================================
# These functions wrap ShelfApp static methods for easy access
def start_warmup() -> bool:
    """Start WebView2 warmup in background (non-blocking).

    Call this early in DCC startup to pre-initialize WebView2 environment.

    Returns:
        True if warmup started successfully, False if not available.

    Example:
        >>> from auroraview_dcc_shelves import start_warmup
        >>> start_warmup()  # Call in DCC userSetup.py
    """
    return ShelfApp.start_warmup()


def warmup_sync(timeout_ms: int = 30000) -> bool:
    """Synchronously wait for WebView2 warmup to complete (blocking).

    Args:
        timeout_ms: Maximum time to wait in milliseconds.

    Returns:
        True if warmup completed successfully, False otherwise.
    """
    return ShelfApp.warmup_sync(timeout_ms)


def is_warmup_complete() -> bool:
    """Check if WebView2 warmup has completed.

    Returns:
        True if warmup is complete and WebView2 is ready.
    """
    return ShelfApp.is_warmup_complete()


def get_warmup_progress() -> int:
    """Get the current warmup progress (0-100).

    Returns:
        Progress percentage (0-100).
    """
    return ShelfApp.get_warmup_progress()


def get_warmup_stage() -> str:
    """Get the current warmup stage description.

    Returns:
        Human-readable stage description.
    """
    return ShelfApp.get_warmup_stage()


def get_warmup_status() -> dict:
    """Get complete warmup status information.

    Returns:
        Dictionary with warmup status including progress, stage, duration, etc.
    """
    return ShelfApp.get_warmup_status()


__all__ = [
    # Config
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
    # Warmup API
    "start_warmup",
    "warmup_sync",
    "is_warmup_complete",
    "get_warmup_progress",
    "get_warmup_stage",
    "get_warmup_status",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]
