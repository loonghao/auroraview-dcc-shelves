"""Tests for the launcher module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from auroraview_dcc_shelves.config import ButtonConfig, ShelfConfig, ShelvesConfig, ToolType
from auroraview_dcc_shelves.launcher import LaunchError, ToolLauncher


class TestToolLauncher:
    """Tests for ToolLauncher class."""

    def test_resolve_absolute_path(self) -> None:
        """Test resolving an absolute path."""
        launcher = ToolLauncher()
        path = launcher.resolve_path("/absolute/path/script.py")
        # On Windows, paths get a drive letter, so just check the path parts
        assert path.parts[-3:] == ("absolute", "path", "script.py")

    def test_resolve_relative_path(self, fs: FakeFilesystem) -> None:
        """Test resolving a relative path."""
        base_path = Path("/project/config")
        fs.create_dir(base_path)
        config = ShelvesConfig(shelves=[], base_path=base_path)
        launcher = ToolLauncher(config)

        path = launcher.resolve_path("scripts/tool.py")
        # Check path ends with expected components
        assert path.parts[-4:] == ("project", "config", "scripts", "tool.py")

    def test_launch_python_script(self, sample_python_script: Path) -> None:
        """Test launching a Python script."""
        config = ShelvesConfig(shelves=[], base_path=sample_python_script.parent.parent)
        launcher = ToolLauncher(config)

        button = ButtonConfig(
            name="Test",
            tool_type=ToolType.PYTHON,
            tool_path=str(sample_python_script),
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            launcher.launch(button)
            assert mock_popen.called
            call_args = mock_popen.call_args
            # Check that the script path is in the command (handle Windows path normalization)
            cmd_str = " ".join(call_args[0][0])
            assert "test_tool.py" in cmd_str

    def test_launch_nonexistent_tool(self) -> None:
        """Test error when launching nonexistent tool."""
        launcher = ToolLauncher()
        button = ButtonConfig(
            name="Missing",
            tool_type=ToolType.PYTHON,
            tool_path="/nonexistent/script.py",
        )

        with pytest.raises(LaunchError, match="not found"):
            launcher.launch(button)

    def test_launch_by_id(self, fs: FakeFilesystem) -> None:
        """Test launching a tool by its ID."""
        script_path = Path("/test/scripts/tool.py")
        fs.create_file(script_path, contents="print('hello')")

        button = ButtonConfig(
            name="My Tool",
            tool_type=ToolType.PYTHON,
            tool_path=str(script_path),
            id="my_tool",
        )
        config = ShelvesConfig(
            shelves=[ShelfConfig(name="Test", buttons=[button])],
            base_path=Path("/test"),
        )
        launcher = ToolLauncher(config)

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            launcher.launch_by_id("my_tool")
            assert mock_popen.called

    def test_launch_by_id_not_found(self) -> None:
        """Test error when button ID is not found."""
        config = ShelvesConfig(shelves=[])
        launcher = ToolLauncher(config)

        with pytest.raises(LaunchError, match="not found"):
            launcher.launch_by_id("nonexistent_id")

    def test_launch_by_id_no_config(self) -> None:
        """Test error when no config is loaded."""
        launcher = ToolLauncher()

        with pytest.raises(LaunchError, match="No configuration"):
            launcher.launch_by_id("any_id")

    def test_launch_executable(self, fs: FakeFilesystem) -> None:
        """Test launching an executable."""
        exe_path = Path("/usr/bin/tool")
        fs.create_file(exe_path, contents="")

        launcher = ToolLauncher()
        button = ButtonConfig(
            name="External Tool",
            tool_type=ToolType.EXECUTABLE,
            tool_path=str(exe_path),
            args=["--flag", "value"],
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            launcher.launch(button)
            assert mock_popen.called
            call_args = mock_popen.call_args[0][0]
            # Check that the executable name is in the command
            cmd_str = " ".join(call_args)
            assert "tool" in cmd_str
            assert "--flag" in call_args
            assert "value" in call_args

    def test_python_script_with_args(self, fs: FakeFilesystem) -> None:
        """Test launching Python script with arguments."""
        script_path = Path("/test/script.py")
        fs.create_file(script_path, contents="import sys; print(sys.argv)")

        launcher = ToolLauncher()
        button = ButtonConfig(
            name="Script with Args",
            tool_type=ToolType.PYTHON,
            tool_path=str(script_path),
            args=["--input", "file.txt", "--verbose"],
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            launcher.launch(button)
            call_args = mock_popen.call_args[0][0]
            assert "--input" in call_args
            assert "file.txt" in call_args
            assert "--verbose" in call_args
