"""Base DCC Adapter interface.

This module defines the abstract base class for DCC adapters and provides
a registry system for adapter lookup.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

# Registry of DCC adapters
_ADAPTER_REGISTRY: dict[str, type[DCCAdapter]] = {}


class DCCAdapter(ABC):
    """Abstract base class for DCC application adapters.

    Each DCC application should have its own adapter that implements
    application-specific functionality like window management and
    performance settings.

    Attributes:
        name: Display name of the DCC application.
        aliases: Alternative names for this DCC (e.g., "max" for "3dsmax").
        timer_interval_ms: Recommended timer interval for UI updates.
        recommended_mode: Recommended integration mode ("qt" or "hwnd").
    """

    name: str = "Unknown"
    aliases: list[str] = []
    timer_interval_ms: int = 16  # 60 FPS default
    recommended_mode: str = "qt"

    @abstractmethod
    def get_main_window(self) -> Any | None:
        """Get the DCC main window as a QWidget.

        Returns:
            The main window QWidget, or None if not found.
        """
        pass

    def on_init(self, shelf_app: Any) -> None:
        """Called when ShelfApp initializes for this DCC.

        Override to perform DCC-specific initialization.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    def on_show(self, shelf_app: Any) -> None:
        """Called after the shelf window is shown.

        Override to perform DCC-specific post-show setup.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    def on_close(self, shelf_app: Any) -> None:
        """Called when the shelf window is closed.

        Override to perform DCC-specific cleanup.

        Args:
            shelf_app: The ShelfApp instance.
        """
        pass

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Return additional API methods to expose to JavaScript.

        Override to add DCC-specific API methods.

        Returns:
            Dictionary of method_name -> callable.
        """
        return {}


class GenericAdapter(DCCAdapter):
    """Generic adapter for unknown DCC applications."""

    name = "Generic"
    timer_interval_ms = 16

    def get_main_window(self) -> Any | None:
        """Get active window from Qt application."""
        try:
            from qtpy.QtWidgets import QApplication
            app = QApplication.instance()
            return app.activeWindow() if app else None
        except ImportError:
            return None


def register_adapter(adapter_class: type[DCCAdapter]) -> type[DCCAdapter]:
    """Register a DCC adapter class.

    This can be used as a decorator:
        @register_adapter
        class MyDCCAdapter(DCCAdapter):
            name = "MyDCC"
            ...

    Args:
        adapter_class: The adapter class to register.

    Returns:
        The same adapter class (for decorator use).
    """
    key = adapter_class.name.lower()
    _ADAPTER_REGISTRY[key] = adapter_class

    # Also register aliases
    for alias in adapter_class.aliases:
        _ADAPTER_REGISTRY[alias.lower()] = adapter_class

    logger.debug(f"Registered DCC adapter: {adapter_class.name}")
    return adapter_class


def get_adapter(app_name: str | None) -> DCCAdapter:
    """Get the appropriate adapter for a DCC application.

    Args:
        app_name: Name of the DCC application (case-insensitive).
            If None or empty, returns a generic adapter.

    Returns:
        An instance of the appropriate DCCAdapter.
    """
    if not app_name:
        return GenericAdapter()

    key = app_name.lower()
    adapter_class = _ADAPTER_REGISTRY.get(key)

    if adapter_class:
        return adapter_class()

    logger.warning(f"No adapter found for '{app_name}', using generic adapter")
    return GenericAdapter()


# Auto-import all adapters to trigger registration
def _load_adapters() -> None:
    """Load all adapter modules to register them."""
    from . import maya, houdini, nuke, max3ds, unreal  # noqa: F401


# Lazy loading - adapters are loaded on first get_adapter call
_adapters_loaded = False


def _ensure_adapters_loaded() -> None:
    """Ensure all adapters are loaded."""
    global _adapters_loaded
    if not _adapters_loaded:
        _load_adapters()
        _adapters_loaded = True


# Patch get_adapter to ensure adapters are loaded
_original_get_adapter = get_adapter


def get_adapter(app_name: str | None) -> DCCAdapter:  # noqa: F811
    """Get the appropriate adapter for a DCC application."""
    _ensure_adapters_loaded()
    return _original_get_adapter(app_name)

