"""YAML configuration parser for DCC tool shelves.

This module provides functions and classes for loading and validating
shelf configuration from YAML files.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """Type of tool to execute."""

    PYTHON = "python"
    EXECUTABLE = "executable"


class ConfigError(Exception):
    """Exception raised for configuration errors."""


@dataclass
class ButtonConfig:
    """Configuration for a single shelf button."""

    name: str
    tool_type: ToolType
    tool_path: str
    icon: str = ""
    args: list[str] = field(default_factory=list)
    description: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            # Generate a simple ID from the name
            self.id = self.name.lower().replace(" ", "_").replace("-", "_")
        # Ensure tool_type is enum
        if isinstance(self.tool_type, str):
            self.tool_type = ToolType(self.tool_type.lower())


@dataclass
class ShelfConfig:
    """Configuration for a tool shelf (group of buttons)."""

    name: str
    buttons: list[ButtonConfig] = field(default_factory=list)
    id: str = ""

    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            self.id = self.name.lower().replace(" ", "_").replace("-", "_")


@dataclass
class ShelvesConfig:
    """Root configuration containing all shelves."""

    shelves: list[ShelfConfig] = field(default_factory=list)
    base_path: Path | None = None

    def get_all_buttons(self) -> list[ButtonConfig]:
        """Get all buttons from all shelves."""
        buttons = []
        for shelf in self.shelves:
            buttons.extend(shelf.buttons)
        return buttons


def _parse_button(data: dict[str, Any]) -> ButtonConfig:
    """Parse a button configuration from dictionary."""
    required_fields = ["name", "tool_type", "tool_path"]
    for field_name in required_fields:
        if field_name not in data:
            raise ConfigError(f"Button missing required field: {field_name}")

    # Validate tool_type
    tool_type_str = data["tool_type"].lower()
    try:
        tool_type = ToolType(tool_type_str)
    except ValueError as e:
        valid_types = ", ".join(t.value for t in ToolType)
        raise ConfigError(f"Invalid tool_type '{data['tool_type']}'. Valid types: {valid_types}") from e

    return ButtonConfig(
        name=data["name"],
        tool_type=tool_type,
        tool_path=data["tool_path"],
        icon=data.get("icon", ""),
        args=data.get("args", []),
        description=data.get("description", ""),
        id=data.get("id", ""),
    )


def _parse_shelf(data: dict[str, Any]) -> ShelfConfig:
    """Parse a shelf configuration from dictionary."""
    if "name" not in data:
        raise ConfigError("Shelf missing required field: name")

    buttons = []
    for button_data in data.get("buttons", []):
        try:
            buttons.append(_parse_button(button_data))
        except ConfigError as e:
            logger.warning(f"Skipping invalid button in shelf '{data['name']}': {e}")

    return ShelfConfig(
        name=data["name"],
        buttons=buttons,
        id=data.get("id", ""),
    )


def load_config(config_path: str | Path) -> ShelvesConfig:
    """Load shelf configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        ShelvesConfig object containing all parsed configuration.

    Raises:
        ConfigError: If the configuration file is invalid or cannot be read.
        FileNotFoundError: If the configuration file does not exist.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration file: {e}") from e

    if data is None:
        raise ConfigError("Configuration file is empty")

    if "shelves" not in data:
        raise ConfigError("Configuration must contain 'shelves' key")

    shelves = []
    for shelf_data in data["shelves"]:
        try:
            shelves.append(_parse_shelf(shelf_data))
        except ConfigError as e:
            logger.warning(f"Skipping invalid shelf: {e}")

    config = ShelvesConfig(shelves=shelves, base_path=config_path.parent)
    return config


def validate_config(config: ShelvesConfig) -> list[str]:
    """Validate a configuration and return list of warnings.

    Args:
        config: The configuration to validate.

    Returns:
        List of warning messages for non-critical issues.
    """
    warnings = []

    if not config.shelves:
        warnings.append("Configuration contains no shelves")

    for shelf in config.shelves:
        if not shelf.buttons:
            warnings.append(f"Shelf '{shelf.name}' contains no buttons")

        for button in shelf.buttons:
            # Check if tool path exists (for absolute paths)
            tool_path = Path(button.tool_path)
            if tool_path.is_absolute() and not tool_path.exists():
                warnings.append(f"Tool path does not exist for '{button.name}': {button.tool_path}")

    return warnings
