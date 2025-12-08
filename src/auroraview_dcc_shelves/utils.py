"""Utility functions for DCC Shelves UI.

This module contains helper functions for icon path resolution,
configuration conversion, and other utilities used by ShelfApp.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from auroraview.utils import path_to_auroraview_url

from auroraview_dcc_shelves.constants import ICON_EXTENSIONS

if TYPE_CHECKING:
    from auroraview_dcc_shelves.config import ButtonConfig


def is_local_icon_path(icon: str) -> bool:
    """Check if an icon string is a local file path (not a Lucide icon name).

    Args:
        icon: The icon string to check.

    Returns:
        True if it's a local file path, False if it's an icon name.
    """
    if not icon:
        return False
    # Check for file extensions commonly used for icons
    if any(icon.lower().endswith(ext) for ext in ICON_EXTENSIONS):
        return True
    # Check for relative path indicators
    if icon.startswith("./") or icon.startswith("../") or icon.startswith("icons/"):
        return True
    # Check if it contains path separators
    return "/" in icon or "\\" in icon


def resolve_icon_path(icon: str, base_path: Path | None) -> str:
    """Resolve icon path to AuroraView protocol URL if it is a local file.

    Args:
        icon: The icon string (could be Lucide name or local path).
        base_path: Base path of the config file for resolving relative paths.

    Returns:
        AuroraView protocol URL for local icons, or original icon name.

    Examples:
        >>> resolve_icon_path("C:/icons/maya.svg", None)
        'https://auroraview.localhost/file/C:/icons/maya.svg'
        >>> resolve_icon_path("icons/tool.png", Path("/config"))
        'https://auroraview.localhost/file/config/icons/tool.png'
        >>> resolve_icon_path("Box", None)  # Lucide icon name
        'Box'
    """
    if not is_local_icon_path(icon) or not base_path:
        # If no base_path but it's still a local icon with absolute path
        if is_local_icon_path(icon) and Path(icon).is_absolute():
            return path_to_auroraview_url(icon)
        return icon

    # Resolve relative path against config base path
    icon_path = Path(icon)
    if not icon_path.is_absolute():
        icon_path = (base_path / icon).resolve()

    # Convert to AuroraView protocol URL
    return path_to_auroraview_url(icon_path)


def button_to_dict(button: ButtonConfig, base_path: Path | None = None) -> dict[str, Any]:
    """Convert a ButtonConfig to a dictionary for JSON serialization.

    Args:
        button: The button configuration.
        base_path: Base path for resolving relative icon paths.

    Returns:
        Dictionary representation of the button.
    """
    # Resolve icon path if it's a local file
    resolved_icon = resolve_icon_path(button.icon, base_path)

    return {
        "id": button.id,
        "label": button.label,
        "label_zh": button.label_zh,
        "icon": resolved_icon,
        "tooltip": button.tooltip,
        "tooltip_zh": button.tooltip_zh,
        "command": button.command,
        "hosts": button.hosts,
        "color": button.color,
        "category": button.category,
        "enabled": button.enabled,
        "tags": button.tags,
        "author": button.author,
        "version": button.version,
        "source_file": button.source_file,
        "help_url": button.help_url,
    }


def shelf_to_dict(
    shelf_name: str,
    buttons: list[ButtonConfig],
    base_path: Path | None = None,
) -> dict[str, Any]:
    """Convert a shelf (name + buttons) to a dictionary.

    Args:
        shelf_name: Name of the shelf.
        buttons: List of button configurations for this shelf.
        base_path: Base path for resolving relative icon paths.

    Returns:
        Dictionary representation of the shelf.
    """
    return {
        "name": shelf_name,
        "buttons": [button_to_dict(b, base_path) for b in buttons],
    }
