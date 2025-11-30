"""Window settings persistence for DCC Shelves.

This module provides functionality to save and restore window settings
(position, size) across application sessions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default settings directory
def _get_settings_dir() -> Path:
    """Get the settings directory based on the platform."""
    import sys
    if sys.platform == "win32":
        # Windows: use APPDATA
        import os
        app_data = os.environ.get("APPDATA", "")
        if app_data:
            return Path(app_data) / "auroraview-dcc-shelves"
        return Path.home() / ".auroraview-dcc-shelves"
    elif sys.platform == "darwin":
        # macOS: use ~/Library/Application Support
        return Path.home() / "Library" / "Application Support" / "auroraview-dcc-shelves"
    else:
        # Linux/Unix: use ~/.config
        return Path.home() / ".config" / "auroraview-dcc-shelves"


@dataclass
class WindowSettings:
    """Window settings data class.
    
    Attributes:
        width: Window width in pixels.
        height: Window height in pixels.
        x: Window X position (optional, -1 means center).
        y: Window Y position (optional, -1 means center).
    """
    width: int = 800
    height: int = 600
    x: int = -1  # -1 means use default/center position
    y: int = -1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WindowSettings":
        """Create from dictionary."""
        return cls(
            width=data.get("width", 800),
            height=data.get("height", 600),
            x=data.get("x", -1),
            y=data.get("y", -1),
        )


class WindowSettingsManager:
    """Manager for window settings persistence.
    
    Saves and loads window settings to/from a JSON file.
    Settings are stored per-application (e.g., maya, nuke, standalone).
    """

    def __init__(self, app_name: str = "standalone"):
        """Initialize the settings manager.
        
        Args:
            app_name: Application identifier (maya, nuke, houdini, standalone).
        """
        self._app_name = app_name.lower() if app_name else "standalone"
        self._settings_dir = _get_settings_dir()
        self._settings_file = self._settings_dir / f"window_{self._app_name}.json"
        self._settings: WindowSettings | None = None

    def _ensure_settings_dir(self) -> None:
        """Ensure the settings directory exists."""
        self._settings_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> WindowSettings:
        """Load window settings from file.
        
        Returns:
            WindowSettings object with saved or default values.
        """
        if self._settings is not None:
            return self._settings

        try:
            if self._settings_file.exists():
                with open(self._settings_file, encoding="utf-8") as f:
                    data = json.load(f)
                self._settings = WindowSettings.from_dict(data)
                logger.debug(f"Loaded window settings from {self._settings_file}")
            else:
                self._settings = WindowSettings()
                logger.debug("Using default window settings")
        except Exception as e:
            logger.warning(f"Failed to load window settings: {e}")
            self._settings = WindowSettings()

        return self._settings

    def save(self, settings: WindowSettings) -> None:
        """Save window settings to file.
        
        Args:
            settings: WindowSettings to save.
        """
        try:
            self._ensure_settings_dir()
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(settings.to_dict(), f, indent=2)
            self._settings = settings
            logger.debug(f"Saved window settings to {self._settings_file}")
        except Exception as e:
            logger.warning(f"Failed to save window settings: {e}")

    def save_from_dialog(self, dialog: Any) -> None:
        """Save window settings from a QDialog.
        
        Args:
            dialog: QDialog instance to extract geometry from.
        """
        try:
            geometry = dialog.geometry()
            settings = WindowSettings(
                width=geometry.width(),
                height=geometry.height(),
                x=geometry.x(),
                y=geometry.y(),
            )
            self.save(settings)
        except Exception as e:
            logger.warning(f"Failed to save dialog geometry: {e}")

    def apply_to_dialog(self, dialog: Any, default_width: int = 800, 
                        default_height: int = 600) -> None:
        """Apply saved settings to a QDialog.
        
        Args:
            dialog: QDialog to apply settings to.
            default_width: Default width if no settings saved.
            default_height: Default height if no settings saved.
        """
        settings = self.load()
        
        # Use saved size or defaults
        width = settings.width if settings.width > 0 else default_width
        height = settings.height if settings.height > 0 else default_height
        
        dialog.resize(width, height)
        
        # Apply position if saved (not -1)
        if settings.x >= 0 and settings.y >= 0:
            dialog.move(settings.x, settings.y)

