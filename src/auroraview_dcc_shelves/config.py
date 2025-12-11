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
    """Type of tool to execute.

    - PYTHON: Python script (.py) - executed via exec() in DCC mode or subprocess
    - EXECUTABLE: Binary executable or shell script - always via subprocess
    - MEL: Maya MEL script (.mel) - executed via maya.mel.eval() in Maya
    - JAVASCRIPT: JavaScript code (.js) - executed via WebView eval()
    """

    PYTHON = "python"
    EXECUTABLE = "executable"
    MEL = "mel"
    JAVASCRIPT = "javascript"


class ConfigError(Exception):
    """Exception raised for configuration errors."""


@dataclass
class ButtonConfig:
    """Configuration for a single shelf button.

    Attributes:
        name: Display name of the button.
        name_zh: Chinese translation of the name (optional).
        tool_type: Type of tool (python or executable).
        tool_path: Path to the tool script or executable.
        icon: Icon name for the button.
        args: Command line arguments to pass to the tool.
        description: Description shown in tooltip.
        description_zh: Chinese translation of the description (optional).
        id: Unique identifier (auto-generated from name if not provided).
        hosts: List of supported DCC hosts (e.g., ["maya", "houdini"]).
               If empty or not specified, tool is available in all hosts.
               Special value "standalone" means the tool works without any DCC.
    """

    name: str
    tool_type: ToolType
    tool_path: str
    icon: str = ""
    args: list[str] = field(default_factory=list)
    description: str = ""
    description_zh: str = ""
    id: str = ""
    hosts: list[str] = field(default_factory=list)
    name_zh: str = ""

    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            # Generate a simple ID from the name
            self.id = self.name.lower().replace(" ", "_").replace("-", "_")
        # Ensure tool_type is enum
        if isinstance(self.tool_type, str):
            self.tool_type = ToolType(self.tool_type.lower())

    def is_available_for_host(self, host: str) -> bool:
        """Check if the tool is available for a specific host.

        Args:
            host: The host name to check (e.g., "maya", "houdini", "standalone").

        Returns:
            True if the tool is available for the host, False otherwise.
        """
        # If no hosts specified, available everywhere
        if not self.hosts:
            return True
        # Check if host is in the list (case-insensitive)
        return host.lower() in [h.lower() for h in self.hosts]


@dataclass
class ShelfConfig:
    """Configuration for a tool shelf (group of buttons).

    Attributes:
        name: Display name of the shelf.
        name_zh: Chinese translation of the name (optional).
        buttons: List of button configurations.
        id: Unique identifier (auto-generated from name if not provided).
    """

    name: str
    buttons: list[ButtonConfig] = field(default_factory=list)
    id: str = ""
    name_zh: str = ""

    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            self.id = self.name.lower().replace(" ", "_").replace("-", "_")


@dataclass
class BannerConfig:
    """Configuration for the UI banner."""

    title: str = "Toolbox"
    subtitle: str = "Production Tools & Scripts"
    image: str = ""  # URL or path to banner image
    gradient_from: str = ""  # CSS color for gradient start
    gradient_to: str = ""  # CSS color for gradient end


@dataclass
class ShelvesConfig:
    """Root configuration containing all shelves."""

    shelves: list[ShelfConfig] = field(default_factory=list)
    banner: BannerConfig = field(default_factory=BannerConfig)
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

    # Parse hosts field (can be string or list)
    hosts_raw = data.get("hosts", [])
    if isinstance(hosts_raw, str):
        hosts = [hosts_raw]
    else:
        hosts = list(hosts_raw) if hosts_raw else []

    return ButtonConfig(
        name=data["name"],
        name_zh=data.get("name_zh", ""),
        tool_type=tool_type,
        tool_path=data["tool_path"],
        icon=data.get("icon", ""),
        args=data.get("args", []),
        description=data.get("description", ""),
        description_zh=data.get("description_zh", ""),
        id=data.get("id", ""),
        hosts=hosts,
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
        name_zh=data.get("name_zh", ""),
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

    # Parse banner configuration if present
    banner = BannerConfig()
    if "banner" in data and isinstance(data["banner"], dict):
        banner_data = data["banner"]
        banner = BannerConfig(
            title=banner_data.get("title", "Toolbox"),
            subtitle=banner_data.get("subtitle", "Production Tools & Scripts"),
            image=banner_data.get("image", ""),
            gradient_from=banner_data.get("gradient_from", ""),
            gradient_to=banner_data.get("gradient_to", ""),
        )

    config = ShelvesConfig(shelves=shelves, banner=banner, base_path=config_path.parent)
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
