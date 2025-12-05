"""DCC Application Adapters.

This package contains adapters for different DCC (Digital Content Creation)
applications. Each adapter handles application-specific logic like:
- Getting the main window for Qt parent integration
- Timer settings for optimal performance
- Special initialization/cleanup routines
- Application-specific API extensions

Supported DCCs:
- Maya
- Houdini
- Nuke
- 3ds Max
- Unreal Engine
- Substance 3D Painter
- Substance 3D Designer
- Blender

Example:
    from auroraview_dcc_shelves.apps import get_adapter

    adapter = get_adapter("maya")
    parent_window = adapter.get_main_window()
    timer_interval = adapter.timer_interval_ms
"""

from .base import DCCAdapter, get_adapter, register_adapter

__all__ = [
    "DCCAdapter",
    "get_adapter",
    "register_adapter",
]
