"""Tests for the configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from auroraview_dcc_shelves.config import (
    ButtonConfig,
    ConfigError,
    ShelfConfig,
    ShelvesConfig,
    ToolType,
    load_config,
    validate_config,
)


class TestToolType:
    """Tests for ToolType enum."""

    def test_python_type(self) -> None:
        """Test Python tool type."""
        assert ToolType.PYTHON.value == "python"

    def test_executable_type(self) -> None:
        """Test executable tool type."""
        assert ToolType.EXECUTABLE.value == "executable"


class TestButtonConfig:
    """Tests for ButtonConfig dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a basic button config."""
        button = ButtonConfig(
            name="Test Button",
            tool_type=ToolType.PYTHON,
            tool_path="scripts/test.py",
        )
        assert button.name == "Test Button"
        assert button.tool_type == ToolType.PYTHON
        assert button.tool_path == "scripts/test.py"
        assert button.id == "test_button"

    def test_auto_id_generation(self) -> None:
        """Test automatic ID generation from name."""
        button = ButtonConfig(
            name="My Cool Tool",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
        )
        assert button.id == "my_cool_tool"

    def test_custom_id(self) -> None:
        """Test custom ID is preserved."""
        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
            id="custom_id",
        )
        assert button.id == "custom_id"

    def test_string_tool_type_conversion(self) -> None:
        """Test that string tool_type is converted to enum."""
        button = ButtonConfig(
            name="Test",
            tool_type="python",  # type: ignore
            tool_path="test.py",
        )
        assert button.tool_type == ToolType.PYTHON

    def test_hosts_empty_by_default(self) -> None:
        """Test that hosts is empty list by default."""
        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
        )
        assert button.hosts == []

    def test_hosts_list(self) -> None:
        """Test hosts as a list."""
        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
            hosts=["maya", "houdini"],
        )
        assert button.hosts == ["maya", "houdini"]

    def test_is_available_for_host_empty_hosts(self) -> None:
        """Test that empty hosts means available everywhere."""
        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
        )
        assert button.is_available_for_host("maya") is True
        assert button.is_available_for_host("houdini") is True
        assert button.is_available_for_host("standalone") is True

    def test_is_available_for_host_specific(self) -> None:
        """Test host availability with specific hosts."""
        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
            hosts=["maya"],
        )
        assert button.is_available_for_host("maya") is True
        assert button.is_available_for_host("Maya") is True  # Case insensitive
        assert button.is_available_for_host("houdini") is False

    def test_is_available_for_host_multiple(self) -> None:
        """Test host availability with multiple hosts."""
        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path="test.py",
            hosts=["maya", "houdini"],
        )
        assert button.is_available_for_host("maya") is True
        assert button.is_available_for_host("houdini") is True
        assert button.is_available_for_host("nuke") is False


class TestShelfConfig:
    """Tests for ShelfConfig dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a basic shelf config."""
        shelf = ShelfConfig(name="Test Shelf")
        assert shelf.name == "Test Shelf"
        assert shelf.id == "test_shelf"
        assert shelf.buttons == []

    def test_with_buttons(self) -> None:
        """Test shelf with buttons."""
        buttons = [
            ButtonConfig(name="Tool 1", tool_type=ToolType.PYTHON, tool_path="t1.py"),
            ButtonConfig(name="Tool 2", tool_type=ToolType.PYTHON, tool_path="t2.py"),
        ]
        shelf = ShelfConfig(name="My Shelf", buttons=buttons)
        assert len(shelf.buttons) == 2


class TestShelvesConfig:
    """Tests for ShelvesConfig dataclass."""

    def test_get_all_buttons(self) -> None:
        """Test getting all buttons from all shelves."""
        config = ShelvesConfig(
            shelves=[
                ShelfConfig(
                    name="Shelf 1",
                    buttons=[
                        ButtonConfig(name="A", tool_type=ToolType.PYTHON, tool_path="a.py"),
                        ButtonConfig(name="B", tool_type=ToolType.PYTHON, tool_path="b.py"),
                    ],
                ),
                ShelfConfig(
                    name="Shelf 2",
                    buttons=[
                        ButtonConfig(name="C", tool_type=ToolType.PYTHON, tool_path="c.py"),
                    ],
                ),
            ]
        )
        all_buttons = config.get_all_buttons()
        assert len(all_buttons) == 3
        assert [b.name for b in all_buttons] == ["A", "B", "C"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, sample_config_path: Path) -> None:
        """Test loading a valid configuration file."""
        config = load_config(sample_config_path)
        assert len(config.shelves) == 2
        assert config.shelves[0].name == "Test Shelf"
        assert len(config.shelves[0].buttons) == 2

    def test_file_not_found(self) -> None:
        """Test error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_empty_config(self, fs: FakeFilesystem) -> None:
        """Test error when config file is empty."""
        config_path = Path("/test/empty.yaml")
        fs.create_file(config_path, contents="")
        with pytest.raises(ConfigError, match="empty"):
            load_config(config_path)

    def test_missing_shelves_key(self, fs: FakeFilesystem) -> None:
        """Test error when shelves key is missing."""
        config_path = Path("/test/invalid.yaml")
        fs.create_file(config_path, contents="other_key: value")
        with pytest.raises(ConfigError, match="shelves"):
            load_config(config_path)

    def test_invalid_yaml(self, fs: FakeFilesystem) -> None:
        """Test error when YAML is invalid."""
        config_path = Path("/test/invalid.yaml")
        fs.create_file(config_path, contents="invalid: yaml: content:")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(config_path)

    def test_base_path_set(self, sample_config_path: Path) -> None:
        """Test that base_path is set to config file's directory."""
        config = load_config(sample_config_path)
        assert config.base_path == sample_config_path.parent

    def test_load_hosts_as_string(self, fs: FakeFilesystem) -> None:
        """Test loading hosts as a single string."""
        config_path = Path("/test/hosts_string.yaml")
        fs.create_file(
            config_path,
            contents="""
shelves:
  - name: Test
    buttons:
      - name: Maya Tool
        tool_type: python
        tool_path: tool.py
        hosts: maya
""",
        )
        config = load_config(config_path)
        assert config.shelves[0].buttons[0].hosts == ["maya"]

    def test_load_hosts_as_list(self, fs: FakeFilesystem) -> None:
        """Test loading hosts as a list."""
        config_path = Path("/test/hosts_list.yaml")
        fs.create_file(
            config_path,
            contents="""
shelves:
  - name: Test
    buttons:
      - name: Multi-DCC Tool
        tool_type: python
        tool_path: tool.py
        hosts:
          - maya
          - houdini
""",
        )
        config = load_config(config_path)
        assert config.shelves[0].buttons[0].hosts == ["maya", "houdini"]

    def test_load_no_hosts(self, fs: FakeFilesystem) -> None:
        """Test that missing hosts defaults to empty list."""
        config_path = Path("/test/no_hosts.yaml")
        fs.create_file(
            config_path,
            contents="""
shelves:
  - name: Test
    buttons:
      - name: Universal Tool
        tool_type: python
        tool_path: tool.py
""",
        )
        config = load_config(config_path)
        assert config.shelves[0].buttons[0].hosts == []


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_empty_shelves_warning(self) -> None:
        """Test warning for empty shelves list."""
        config = ShelvesConfig(shelves=[])
        warnings = validate_config(config)
        assert any("no shelves" in w for w in warnings)

    def test_empty_buttons_warning(self) -> None:
        """Test warning for shelf with no buttons."""
        config = ShelvesConfig(shelves=[ShelfConfig(name="Empty", buttons=[])])
        warnings = validate_config(config)
        assert any("no buttons" in w for w in warnings)

    def test_valid_config_no_warnings(self) -> None:
        """Test that valid config produces no warnings."""
        config = ShelvesConfig(
            shelves=[
                ShelfConfig(
                    name="Valid",
                    buttons=[
                        ButtonConfig(
                            name="Tool",
                            tool_type=ToolType.PYTHON,
                            tool_path="relative/path.py",
                        )
                    ],
                )
            ]
        )
        warnings = validate_config(config)
        # Only relative paths, so no "does not exist" warnings
        assert len(warnings) == 0
