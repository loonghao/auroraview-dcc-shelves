"""Tests for the configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from auroraview_dcc_shelves.config import (
    ButtonConfig,
    CircularReferenceError,
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


class TestYamlReferences:
    """Tests for YAML file reference resolution."""

    def test_basic_ref_resolution(self, fs: FakeFilesystem) -> None:
        """Test basic reference to another YAML file."""
        # Create main config
        main_config = Path("/project/shelf_config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - ref: ./dcc/maya_shelves.yaml
""",
        )

        # Create referenced file (without Chinese characters to avoid encoding issues)
        maya_shelves = Path("/project/dcc/maya_shelves.yaml")
        fs.create_file(
            maya_shelves,
            contents="""
name: Maya Tools
buttons:
  - name: Quad Draw
    tool_type: python
    tool_path: scripts/quad_draw.py
    description: Retopology tool
    hosts: [maya]
""",
        )

        config = load_config(main_config)
        assert len(config.shelves) == 1
        assert config.shelves[0].name == "Maya Tools"
        assert len(config.shelves[0].buttons) == 1
        assert config.shelves[0].buttons[0].name == "Quad Draw"

    def test_ref_with_multiple_shelves(self, fs: FakeFilesystem) -> None:
        """Test reference to file containing multiple shelves."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - ref: ./maya/shelves.yaml
""",
        )

        maya_shelves = Path("/project/maya/shelves.yaml")
        fs.create_file(
            maya_shelves,
            contents="""
shelves:
  - name: Maya Modeling
    buttons:
      - name: Tool 1
        tool_type: python
        tool_path: scripts/tool1.py
  - name: Maya Rigging
    buttons:
      - name: Tool 2
        tool_type: python
        tool_path: scripts/tool2.py
""",
        )

        config = load_config(main_config)
        assert len(config.shelves) == 2
        assert config.shelves[0].name == "Maya Modeling"
        assert config.shelves[1].name == "Maya Rigging"

    def test_mixed_inline_and_ref(self, fs: FakeFilesystem) -> None:
        """Test mixing inline shelves with references."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - name: Universal Tools
    buttons:
      - name: Calculator
        tool_type: python
        tool_path: scripts/calc.py
  - ref: ./maya/tools.yaml
  - name: Pipeline
    buttons:
      - name: Publisher
        tool_type: python
        tool_path: scripts/publish.py
""",
        )

        maya_tools = Path("/project/maya/tools.yaml")
        fs.create_file(
            maya_tools,
            contents="""
name: Maya Tools
buttons:
  - name: Modeler
    tool_type: python
    tool_path: scripts/model.py
""",
        )

        config = load_config(main_config)
        assert len(config.shelves) == 3
        assert config.shelves[0].name == "Universal Tools"
        assert config.shelves[1].name == "Maya Tools"
        assert config.shelves[2].name == "Pipeline"

    def test_nested_refs(self, fs: FakeFilesystem) -> None:
        """Test nested references (ref within a referenced file)."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - ref: ./dcc/all_dcc.yaml
""",
        )

        all_dcc = Path("/project/dcc/all_dcc.yaml")
        fs.create_file(
            all_dcc,
            contents="""
shelves:
  - ref: ./maya/shelves.yaml
  - ref: ./houdini/shelves.yaml
""",
        )

        maya_shelves = Path("/project/dcc/maya/shelves.yaml")
        fs.create_file(
            maya_shelves,
            contents="""
name: Maya Tools
buttons:
  - name: Maya Tool
    tool_type: python
    tool_path: scripts/maya.py
""",
        )

        houdini_shelves = Path("/project/dcc/houdini/shelves.yaml")
        fs.create_file(
            houdini_shelves,
            contents="""
name: Houdini Tools
buttons:
  - name: Houdini Tool
    tool_type: python
    tool_path: scripts/houdini.py
""",
        )

        config = load_config(main_config)
        assert len(config.shelves) == 2
        assert config.shelves[0].name == "Maya Tools"
        assert config.shelves[1].name == "Houdini Tools"

    def test_circular_reference_detection(self, fs: FakeFilesystem) -> None:
        """Test that circular references are detected and raise error."""
        config_a = Path("/project/config_a.yaml")
        fs.create_file(
            config_a,
            contents="""
shelves:
  - ref: ./config_b.yaml
""",
        )

        config_b = Path("/project/config_b.yaml")
        fs.create_file(
            config_b,
            contents="""
shelves:
  - ref: ./config_a.yaml
""",
        )

        with pytest.raises(CircularReferenceError):
            load_config(config_a)

    def test_self_reference_detection(self, fs: FakeFilesystem) -> None:
        """Test that self-referencing files are detected."""
        config = Path("/project/config.yaml")
        fs.create_file(
            config,
            contents="""
shelves:
  - ref: ./config.yaml
""",
        )

        with pytest.raises(CircularReferenceError):
            load_config(config)

    def test_missing_ref_file_warning(self, fs: FakeFilesystem) -> None:
        """Test that missing referenced files produce warnings, not errors."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - name: Existing Shelf
    buttons:
      - name: Tool
        tool_type: python
        tool_path: tool.py
  - ref: ./nonexistent.yaml
""",
        )

        # Should not raise, but skip the missing reference
        config = load_config(main_config)
        assert len(config.shelves) == 1
        assert config.shelves[0].name == "Existing Shelf"

    def test_relative_path_resolution(self, fs: FakeFilesystem) -> None:
        """Test that relative paths in referenced files are resolved correctly."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - ref: ./maya/shelves.yaml
""",
        )

        maya_shelves = Path("/project/maya/shelves.yaml")
        fs.create_file(
            maya_shelves,
            contents="""
name: Maya Tools
buttons:
  - name: Quad Draw
    icon: icons/maya.svg
    tool_type: python
    tool_path: scripts/quad_draw.py
""",
        )

        config = load_config(main_config)
        # The icon path should be adjusted to be relative to root config
        assert config.shelves[0].buttons[0].icon == "maya/icons/maya.svg"
        # Tool path should also be adjusted
        assert config.shelves[0].buttons[0].tool_path == "maya/scripts/quad_draw.py"

    def test_lucide_icon_unchanged(self, fs: FakeFilesystem) -> None:
        """Test that Lucide icon names are not modified."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
shelves:
  - ref: ./dcc/maya.yaml
""",
        )

        maya_config = Path("/project/dcc/maya.yaml")
        fs.create_file(
            maya_config,
            contents="""
name: Maya Tools
buttons:
  - name: Tool
    icon: Smile
    tool_type: python
    tool_path: scripts/tool.py
""",
        )

        config = load_config(main_config)
        # Lucide icon name should remain unchanged (not a local path)
        assert config.shelves[0].buttons[0].icon == "Smile"
        # Tool path should be adjusted relative to root
        assert config.shelves[0].buttons[0].tool_path == "dcc/scripts/tool.py"

    def test_banner_not_affected_by_refs(self, fs: FakeFilesystem) -> None:
        """Test that banner config is taken from main file only."""
        main_config = Path("/project/config.yaml")
        fs.create_file(
            main_config,
            contents="""
banner:
  title: Main Title
  subtitle: Main Subtitle
shelves:
  - ref: ./other.yaml
""",
        )

        other_config = Path("/project/other.yaml")
        fs.create_file(
            other_config,
            contents="""
banner:
  title: Other Title
name: Other Shelf
buttons:
  - name: Tool
    tool_type: python
    tool_path: tool.py
""",
        )

        config = load_config(main_config)
        # Banner should be from main config
        assert config.banner.title == "Main Title"
        assert config.banner.subtitle == "Main Subtitle"
