"""User tools management for DCC shelves.

This module handles saving, loading, and managing user-created tools
in a local YAML configuration file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import yaml

from auroraview_dcc_shelves.settings import _get_settings_dir

logger = logging.getLogger(__name__)

# File name for user tools config
USER_TOOLS_FILE = "user_tools.yaml"
USER_TOOLS_CATEGORY = "My Tools"
USER_TOOLS_CATEGORY_ZH = "我的工具"


@dataclass
class UserTool:
    """Configuration for a user-created tool.

    Attributes:
        id: Unique identifier for the tool.
        name: Display name of the tool.
        name_zh: Chinese translation of the name (optional).
        tool_type: Type of tool (python or executable).
        tool_path: Path to the tool script or executable.
        icon: Icon name for the tool.
        args: Command line arguments to pass to the tool.
        description: Description shown in tooltip.
        description_zh: Chinese translation of the description (optional).
        hosts: List of supported DCC hosts.
        created_at: When the tool was created.
        updated_at: When the tool was last updated.
    """

    id: str
    name: str
    tool_type: str
    tool_path: str
    icon: str = "Wrench"
    name_zh: str = ""
    args: list[str] = field(default_factory=list)
    description: str = ""
    description_zh: str = ""
    hosts: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Remove empty optional fields
        if not data.get("name_zh"):
            del data["name_zh"]
        if not data.get("args"):
            del data["args"]
        if not data.get("description"):
            del data["description"]
        if not data.get("description_zh"):
            del data["description_zh"]
        if not data.get("hosts"):
            del data["hosts"]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserTool:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            tool_type=data.get("tool_type", data.get("toolType", "python")),
            tool_path=data.get("tool_path", data.get("toolPath", "")),
            icon=data.get("icon", "Wrench"),
            name_zh=data.get("name_zh", ""),
            args=data.get("args", []),
            description=data.get("description", ""),
            description_zh=data.get("description_zh", ""),
            hosts=data.get("hosts", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class UserToolsManager:
    """Manager for user-created tools.

    Handles loading, saving, and managing user tools in a local YAML file.
    """

    def __init__(self) -> None:
        """Initialize the user tools manager."""
        self._settings_dir = _get_settings_dir()
        self._tools_file = self._settings_dir / USER_TOOLS_FILE
        self._tools: dict[str, UserTool] = {}
        self._loaded = False

    def _ensure_dir(self) -> None:
        """Ensure the settings directory exists."""
        self._settings_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[UserTool]:
        """Load user tools from file.

        Returns:
            List of user tools.
        """
        if self._loaded:
            return list(self._tools.values())

        try:
            if self._tools_file.exists():
                with open(self._tools_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data and "tools" in data:
                    for tool_data in data["tools"]:
                        try:
                            tool = UserTool.from_dict(tool_data)
                            self._tools[tool.id] = tool
                        except Exception as e:
                            logger.warning(f"Failed to parse user tool: {e}")

                logger.info(f"Loaded {len(self._tools)} user tools from {self._tools_file}")
            else:
                logger.debug("No user tools file found, starting fresh")

            self._loaded = True
        except Exception as e:
            logger.error(f"Failed to load user tools: {e}")

        return list(self._tools.values())

    def save(self) -> bool:
        """Save all user tools to file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self._ensure_dir()

            data = {
                "version": "1.0.0",
                "updated_at": datetime.now().isoformat(),
                "tools": [tool.to_dict() for tool in self._tools.values()],
            }

            with open(self._tools_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            logger.info(f"Saved {len(self._tools)} user tools to {self._tools_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user tools: {e}")
            return False

    def add_tool(self, tool_data: dict[str, Any]) -> UserTool:
        """Add a new user tool.

        Args:
            tool_data: Tool configuration data.

        Returns:
            The created UserTool.
        """
        # Ensure tools are loaded
        self.load()

        # Generate ID if not provided
        if "id" not in tool_data or not tool_data["id"]:
            import random
            import time

            tool_data["id"] = f"user_{int(time.time())}_{random.randint(1000, 9999)}"

        tool = UserTool.from_dict(tool_data)
        self._tools[tool.id] = tool
        self.save()

        logger.info(f"Added user tool: {tool.name} ({tool.id})")
        return tool

    def update_tool(self, tool_id: str, updates: dict[str, Any]) -> UserTool | None:
        """Update an existing user tool.

        Args:
            tool_id: ID of the tool to update.
            updates: Fields to update.

        Returns:
            The updated UserTool, or None if not found.
        """
        self.load()

        if tool_id not in self._tools:
            logger.warning(f"Tool not found: {tool_id}")
            return None

        tool = self._tools[tool_id]
        tool_dict = tool.to_dict()
        tool_dict.update(updates)
        tool_dict["updated_at"] = datetime.now().isoformat()

        updated_tool = UserTool.from_dict(tool_dict)
        self._tools[tool_id] = updated_tool
        self.save()

        logger.info(f"Updated user tool: {updated_tool.name} ({tool_id})")
        return updated_tool

    def delete_tool(self, tool_id: str) -> bool:
        """Delete a user tool.

        Args:
            tool_id: ID of the tool to delete.

        Returns:
            True if deleted, False if not found.
        """
        self.load()

        if tool_id not in self._tools:
            logger.warning(f"Tool not found for deletion: {tool_id}")
            return False

        tool = self._tools.pop(tool_id)
        self.save()

        logger.info(f"Deleted user tool: {tool.name} ({tool_id})")
        return True

    def get_tool(self, tool_id: str) -> UserTool | None:
        """Get a user tool by ID.

        Args:
            tool_id: ID of the tool.

        Returns:
            The UserTool, or None if not found.
        """
        self.load()
        return self._tools.get(tool_id)

    def get_all_tools(self) -> list[UserTool]:
        """Get all user tools.

        Returns:
            List of all user tools.
        """
        return self.load()

    def export_tools(self) -> str:
        """Export all user tools as JSON string.

        Returns:
            JSON string of all tools.
        """
        self.load()

        config = {
            "version": "1.0.0",
            "exportedAt": datetime.now().isoformat(),
            "shelves": [
                {
                    "id": "user_tools",
                    "name": USER_TOOLS_CATEGORY,
                    "name_zh": USER_TOOLS_CATEGORY_ZH,
                    "buttons": [tool.to_dict() for tool in self._tools.values()],
                }
            ],
        }

        return json.dumps(config, indent=2, ensure_ascii=False)

    def import_tools(self, json_config: str, merge: bool = True) -> int:
        """Import tools from JSON config.

        Args:
            json_config: JSON string with tools config.
            merge: If True, merge with existing. If False, replace all.

        Returns:
            Number of tools imported.
        """
        try:
            config = json.loads(json_config)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return 0

        if not merge:
            self._tools.clear()

        count = 0
        for shelf in config.get("shelves", []):
            for button in shelf.get("buttons", []):
                try:
                    tool = UserTool.from_dict(button)
                    # Generate new ID if merging to avoid conflicts
                    if merge:
                        import random
                        import time

                        tool.id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
                    self._tools[tool.id] = tool
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to import tool: {e}")

        self.save()
        logger.info(f"Imported {count} tools")
        return count

    def to_button_configs(self) -> list[dict[str, Any]]:
        """Convert all user tools to ButtonConfig format for frontend.

        Returns:
            List of button config dictionaries.
        """
        self.load()

        buttons = []
        for tool in self._tools.values():
            buttons.append(
                {
                    "id": tool.id,
                    "name": tool.name,
                    "name_zh": tool.name_zh or None,
                    "toolType": tool.tool_type,
                    "toolPath": tool.tool_path,
                    "icon": tool.icon,
                    "args": tool.args,
                    "description": tool.description,
                    "description_zh": tool.description_zh or None,
                    "hosts": tool.hosts,
                    "source": "user",
                }
            )

        return buttons
