"""YAML configuration parser for DCC tool shelves.

This module provides functions and classes for loading and validating
shelf configuration from YAML files.

Supports YAML file references via 'ref' field for modular configuration:
- ref: ./maya/shelves.yaml  # Reference another YAML file
- Relative paths are resolved based on the current YAML file's directory
- Circular references are detected and raise ConfigError
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class CircularReferenceError(Exception):
    """Exception raised when circular reference is detected in YAML files."""


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


def _load_yaml_file(file_path: Path) -> dict[str, Any]:
    """Load and parse a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Parsed YAML data as dictionary.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ConfigError: If YAML is invalid or empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration file {file_path}: {e}") from e

    if data is None:
        raise ConfigError(f"Configuration file is empty: {file_path}")

    return data


def _resolve_ref_path(ref_path: str, base_dir: Path) -> Path:
    """Resolve a reference path relative to base directory.

    Args:
        ref_path: The reference path (can be relative or absolute).
        base_dir: The base directory for resolving relative paths.

    Returns:
        Resolved absolute path.
    """
    ref = Path(ref_path)
    if ref.is_absolute():
        return ref
    return (base_dir / ref).resolve()


def _resolve_references(
    data: dict[str, Any],
    current_file: Path,
    visited_files: set[Path] | None = None,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    """Recursively resolve 'ref' references in configuration data.

    This function processes the configuration data and resolves any 'ref' fields
    that point to other YAML files. The referenced files are loaded and their
    content is merged into the parent configuration.

    Args:
        data: The configuration data dictionary.
        current_file: Path to the current YAML file (for resolving relative paths).
        visited_files: Set of already visited files (for circular reference detection).
        root_dir: Root directory of the main config file (for asset path resolution).

    Returns:
        Configuration data with all references resolved.

    Raises:
        CircularReferenceError: If a circular reference is detected.
        ConfigError: If referenced file is invalid.
    """
    if visited_files is None:
        visited_files = set()

    current_file_resolved = current_file.resolve()
    if current_file_resolved in visited_files:
        raise CircularReferenceError(f"Circular reference detected: {current_file} has already been processed")

    visited_files.add(current_file_resolved)
    current_dir = current_file.parent

    if root_dir is None:
        root_dir = current_dir

    # Process shelves list - may contain ref items
    if "shelves" in data:
        resolved_shelves = []
        for shelf_item in data["shelves"]:
            if isinstance(shelf_item, dict):
                if "ref" in shelf_item:
                    # This is a reference to another file
                    ref_path = _resolve_ref_path(shelf_item["ref"], current_dir)
                    logger.debug(f"Resolving reference: {shelf_item['ref']} -> {ref_path}")

                    try:
                        ref_data = _load_yaml_file(ref_path)
                        # Recursively resolve references in the referenced file
                        ref_data = _resolve_references(ref_data, ref_path, visited_files.copy(), root_dir)

                        # The referenced file can contain:
                        # 1. A list of shelves directly (shelves: [...])
                        # 2. A single shelf definition (name: ..., buttons: [...])
                        if "shelves" in ref_data:
                            # File contains multiple shelves
                            for shelf in ref_data["shelves"]:
                                shelf = _adjust_asset_paths(shelf, ref_path.parent, root_dir)
                                resolved_shelves.append(shelf)
                        elif "name" in ref_data and "buttons" in ref_data:
                            # File is a single shelf definition
                            shelf = _adjust_asset_paths(ref_data, ref_path.parent, root_dir)
                            resolved_shelves.append(shelf)
                        else:
                            logger.warning(f"Referenced file {ref_path} does not contain valid shelf data")
                    except FileNotFoundError:
                        logger.warning(f"Referenced file not found: {ref_path}")
                    except CircularReferenceError:
                        raise
                    except ConfigError as e:
                        logger.warning(f"Error loading referenced file {ref_path}: {e}")
                else:
                    # Regular shelf definition - adjust paths if needed
                    shelf = _adjust_asset_paths(shelf_item, current_dir, root_dir)
                    resolved_shelves.append(shelf)
            else:
                resolved_shelves.append(shelf_item)

        data["shelves"] = resolved_shelves

    return data


def _adjust_asset_paths(
    shelf_data: dict[str, Any],
    source_dir: Path,
    root_dir: Path,
) -> dict[str, Any]:
    """Adjust relative asset paths in shelf data to be relative to root config.

    When a shelf is loaded from a referenced file, its relative paths (like icons)
    need to be adjusted to work correctly from the main config's perspective.

    Args:
        shelf_data: The shelf data dictionary.
        source_dir: Directory where the shelf data was loaded from.
        root_dir: Root directory of the main config file.

    Returns:
        Shelf data with adjusted paths.
    """
    # Don't modify the original data
    shelf_data = dict(shelf_data)

    if "buttons" in shelf_data:
        adjusted_buttons = []
        for button in shelf_data["buttons"]:
            button = dict(button)

            # Adjust icon path if it's a relative local path
            if "icon" in button and button["icon"]:
                icon_path = button["icon"]
                # Check if it's a local file path (not a Lucide icon name)
                if _is_local_asset_path(icon_path):
                    button["icon"] = _make_relative_to_root(icon_path, source_dir, root_dir)

            # Adjust tool_path if it's relative
            if "tool_path" in button and button["tool_path"]:
                tool_path = button["tool_path"]
                if not Path(tool_path).is_absolute():
                    button["tool_path"] = _make_relative_to_root(tool_path, source_dir, root_dir)

            adjusted_buttons.append(button)

        shelf_data["buttons"] = adjusted_buttons

    return shelf_data


def _is_local_asset_path(path: str) -> bool:
    """Check if a path is a local asset path (not a Lucide icon name).

    Args:
        path: The path to check.

    Returns:
        True if it's a local file path, False if it's an icon name.
    """
    # Check for file extensions commonly used for icons
    if any(path.lower().endswith(ext) for ext in [".svg", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp"]):
        return True
    # Check for relative path indicators
    if path.startswith("./") or path.startswith("../") or path.startswith("icons/"):
        return True
    # Check if it contains path separators
    return bool("/" in path or "\\" in path)


def _make_relative_to_root(rel_path: str, source_dir: Path, root_dir: Path) -> str:
    """Convert a path relative to source_dir to be relative to root_dir.

    Args:
        rel_path: Path relative to source_dir.
        source_dir: The directory the path is currently relative to.
        root_dir: The root directory to make the path relative to.

    Returns:
        Path relative to root_dir (always with forward slashes for consistency).
    """
    # Resolve the absolute path
    abs_path = (source_dir / rel_path).resolve()
    try:
        # Make it relative to root_dir
        result = str(abs_path.relative_to(root_dir.resolve()))
        # Normalize to forward slashes for cross-platform consistency
        return result.replace("\\", "/")
    except ValueError:
        # Path is not under root_dir, return absolute path
        return str(abs_path)


def load_config(config_path: str | Path) -> ShelvesConfig:
    """Load shelf configuration from a YAML file with reference resolution.

    Supports 'ref' field in shelves list to reference other YAML files.
    Relative paths in referenced files are automatically adjusted.

    Example:
        shelves:
          - ref: ./maya/shelves.yaml     # Load shelves from another file
          - ref: ./houdini/shelves.yaml  # Load more shelves
          - name: Direct Shelf           # Regular inline shelf definition
            buttons: [...]

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        ShelvesConfig object containing all parsed configuration.

    Raises:
        ConfigError: If the configuration file is invalid or cannot be read.
        CircularReferenceError: If circular reference is detected.
        FileNotFoundError: If the configuration file does not exist.
    """
    config_path = Path(config_path)
    data = _load_yaml_file(config_path)

    if "shelves" not in data:
        raise ConfigError("Configuration must contain 'shelves' key")

    # Resolve all references
    data = _resolve_references(data, config_path)

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
