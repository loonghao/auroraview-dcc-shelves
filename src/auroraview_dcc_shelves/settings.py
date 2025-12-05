"""DCC state persistence for DCC Shelves.

This module provides functionality to save and restore DCC-specific state
(UI preferences, panel states) across application sessions.

Each DCC application has its own isolated state file to prevent
cross-contamination between different applications.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
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
class DCCState:
    """DCC-specific state data class.

    Stores UI state and preferences for a specific DCC application.
    Does NOT store window size (size is fixed by design).

    Attributes:
        collapsed_shelves: List of shelf IDs that are collapsed.
        last_active_shelf: ID of the last active shelf.
        bottom_panel_tab: Currently selected bottom panel tab.
        bottom_panel_expanded: Whether the bottom panel is expanded.
        custom_data: Additional DCC-specific data.
    """

    collapsed_shelves: list[str] = field(default_factory=list)
    last_active_shelf: str = ""
    bottom_panel_tab: str = "info"
    bottom_panel_expanded: bool = True
    custom_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DCCState:
        """Create from dictionary."""
        return cls(
            collapsed_shelves=data.get("collapsed_shelves", []),
            last_active_shelf=data.get("last_active_shelf", ""),
            bottom_panel_tab=data.get("bottom_panel_tab", "info"),
            bottom_panel_expanded=data.get("bottom_panel_expanded", True),
            custom_data=data.get("custom_data", {}),
        )


class DCCStateManager:
    """Manager for DCC-specific state persistence.

    Each DCC application has its own state file to prevent
    cross-contamination between different applications.

    State files are stored as: state_{dcc_name}.json
    """

    def __init__(self, dcc_name: str = "standalone"):
        """Initialize the state manager.

        Args:
            dcc_name: DCC identifier (maya, nuke, houdini, blender, etc.).
        """
        self._dcc_name = dcc_name.lower() if dcc_name else "standalone"
        self._settings_dir = _get_settings_dir()
        self._state_file = self._settings_dir / f"state_{self._dcc_name}.json"
        self._state: DCCState | None = None

    @property
    def dcc_name(self) -> str:
        """Get the DCC name."""
        return self._dcc_name

    def _ensure_settings_dir(self) -> None:
        """Ensure the settings directory exists."""
        self._settings_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> DCCState:
        """Load DCC state from file.

        Returns:
            DCCState object with saved or default values.
        """
        if self._state is not None:
            return self._state

        try:
            if self._state_file.exists():
                with open(self._state_file, encoding="utf-8") as f:
                    data = json.load(f)
                self._state = DCCState.from_dict(data)
                logger.debug(f"Loaded DCC state from {self._state_file}")
            else:
                self._state = DCCState()
                logger.debug(f"Using default DCC state for {self._dcc_name}")
        except Exception as e:
            logger.warning(f"Failed to load DCC state: {e}")
            self._state = DCCState()

        return self._state

    def save(self, state: DCCState | None = None) -> None:
        """Save DCC state to file.

        Args:
            state: DCCState to save. If None, saves current state.
        """
        if state is not None:
            self._state = state

        if self._state is None:
            return

        try:
            self._ensure_settings_dir()
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(self._state.to_dict(), f, indent=2)
            logger.debug(f"Saved DCC state to {self._state_file}")
        except Exception as e:
            logger.warning(f"Failed to save DCC state: {e}")

    def update(self, **kwargs: Any) -> None:
        """Update specific state fields and save.

        Args:
            **kwargs: State fields to update.
        """
        state = self.load()

        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                # Store in custom_data
                state.custom_data[key] = value

        self.save(state)

    def get_custom(self, key: str, default: Any = None) -> Any:
        """Get a custom data value.

        Args:
            key: Custom data key.
            default: Default value if key not found.

        Returns:
            The stored value or default.
        """
        state = self.load()
        return state.custom_data.get(key, default)

    def set_custom(self, key: str, value: Any) -> None:
        """Set a custom data value and save.

        Args:
            key: Custom data key.
            value: Value to store.
        """
        state = self.load()
        state.custom_data[key] = value
        self.save(state)


# Legacy alias for backward compatibility
# TODO: Remove after migrating all usages
class WindowSettingsManager:
    """Legacy manager - no longer saves window size.

    This class is kept for backward compatibility but now uses DCCStateManager
    internally. Window size is no longer persisted as it's fixed by design.
    """

    def __init__(self, app_name: str = "standalone"):
        """Initialize the settings manager.

        Args:
            app_name: Application identifier (maya, nuke, houdini, standalone).
        """
        self._dcc_state = DCCStateManager(app_name)
        logger.debug(f"WindowSettingsManager initialized for {app_name} (size persistence disabled)")

    def load(self) -> WindowSettings:
        """Load window settings (returns defaults only).

        Window size is now fixed, so this returns default values.
        """
        return WindowSettings()

    def save(self, width: int, height: int) -> None:
        """Save window settings (no-op, size is fixed)."""
        # Size is no longer saved - window size is fixed by design
        pass

    def save_from_dialog(self, dialog: Any) -> None:
        """Save window settings from a QDialog (no-op)."""
        # Size is no longer saved - window size is fixed by design
        pass


@dataclass
class WindowSettings:
    """Legacy window settings data class.

    Kept for backward compatibility. Returns default values only.
    """

    width: int = 0  # 0 means use default
    height: int = 0  # 0 means use default
    x: int = -1
    y: int = -1
