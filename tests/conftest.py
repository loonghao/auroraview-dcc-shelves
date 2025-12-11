"""Pytest configuration and fixtures for auroraview-dcc-shelves tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem


@pytest.fixture
def sample_config_yaml() -> str:
    """Return a sample YAML configuration string."""
    return """
shelves:
  - name: "Test Shelf"
    buttons:
      - name: "Test Tool"
        icon: "box"
        tool_type: "python"
        tool_path: "scripts/test_tool.py"
        description: "A test tool"
        args: ["--verbose"]

      - name: "Another Tool"
        icon: "wrench"
        tool_type: "executable"
        tool_path: "/usr/bin/tool"
        description: "Another test tool"

  - name: "Empty Shelf"
    buttons: []
"""


@pytest.fixture
def sample_config_path(fs: FakeFilesystem, sample_config_yaml: str) -> Path:
    """Create a sample config file in the fake filesystem."""
    config_path = Path("/test/config/shelf_config.yaml")
    fs.create_file(config_path, contents=sample_config_yaml)
    return config_path


@pytest.fixture
def sample_python_script(fs: FakeFilesystem) -> Path:
    """Create a sample Python script in the fake filesystem."""
    script_path = Path("/test/config/scripts/test_tool.py")
    script_content = """
import sys
print("Test tool executed")
print(f"Args: {sys.argv[1:]}")
"""
    fs.create_file(script_path, contents=script_content)
    return script_path
