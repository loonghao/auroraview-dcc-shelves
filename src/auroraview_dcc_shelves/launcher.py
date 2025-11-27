"""Tool launcher module for executing Python scripts and executables.

This module provides the ToolLauncher class for running tools configured
in the shelf system.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auroraview_dcc_shelves.config import ButtonConfig, ShelvesConfig

from auroraview_dcc_shelves.config import ToolType

logger = logging.getLogger(__name__)


class LaunchError(Exception):
    """Exception raised when a tool fails to launch."""


class ToolLauncher:
    """Launcher for executing tools configured in the shelf system.

    This class handles the execution of both Python scripts and
    executable files with proper error handling.

    Args:
        config: The shelves configuration containing base path info.
        python_executable: Path to Python executable. Defaults to sys.executable.
    """

    def __init__(
        self,
        config: ShelvesConfig | None = None,
        python_executable: str | None = None,
    ) -> None:
        self._config = config
        self._python_executable = python_executable or sys.executable
        self._base_path = config.base_path if config else Path.cwd()

    def resolve_path(self, tool_path: str) -> Path:
        """Resolve a tool path to an absolute path.

        Args:
            tool_path: The tool path (can be absolute or relative).

        Returns:
            Resolved absolute path.
        """
        path = Path(tool_path)
        if path.is_absolute():
            return path
        # Resolve relative to config file's directory
        return (self._base_path / path).resolve()

    def launch(self, button: ButtonConfig) -> subprocess.Popen | None:
        """Launch a tool based on its configuration.

        Args:
            button: The button configuration specifying the tool to launch.

        Returns:
            The subprocess.Popen object for the launched process,
            or None if the tool was executed inline (Python script with exec).

        Raises:
            LaunchError: If the tool fails to launch.
        """
        tool_path = self.resolve_path(button.tool_path)
        logger.info(f"Launching tool: {button.name} ({tool_path})")

        if not tool_path.exists():
            raise LaunchError(f"Tool not found: {tool_path}")

        if button.tool_type == ToolType.PYTHON:
            return self._launch_python(tool_path, button.args)
        elif button.tool_type == ToolType.EXECUTABLE:
            return self._launch_executable(tool_path, button.args)
        else:
            raise LaunchError(f"Unknown tool type: {button.tool_type}")

    def _launch_python(self, script_path: Path, args: list[str]) -> subprocess.Popen | None:
        """Launch a Python script.

        Args:
            script_path: Path to the Python script.
            args: Command line arguments to pass.

        Returns:
            The Popen object for the launched process.
        """
        if script_path.suffix.lower() != ".py":
            logger.warning(f"Python tool path does not end with .py: {script_path}")

        try:
            cmd = [self._python_executable, str(script_path), *args]
            logger.debug(f"Executing: {' '.join(cmd)}")

            # Create environment with script's directory in PYTHONPATH
            env = os.environ.copy()
            script_dir = str(script_path.parent)
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = f"{script_dir}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = script_dir

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=script_path.parent,
            )
            return process
        except OSError as e:
            raise LaunchError(f"Failed to launch Python script: {e}") from e

    def _launch_executable(self, exe_path: Path, args: list[str]) -> subprocess.Popen:
        """Launch an executable file.

        Args:
            exe_path: Path to the executable.
            args: Command line arguments to pass.

        Returns:
            The Popen object for the launched process.
        """
        try:
            cmd = [str(exe_path), *args]
            logger.debug(f"Executing: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=exe_path.parent,
            )
            return process
        except PermissionError as e:
            raise LaunchError(f"Permission denied when executing: {exe_path}. Check file permissions.") from e
        except OSError as e:
            raise LaunchError(f"Failed to launch executable: {e}") from e

    def launch_by_id(self, button_id: str) -> subprocess.Popen | None:
        """Launch a tool by its button ID.

        Args:
            button_id: The unique identifier of the button.

        Returns:
            The Popen object for the launched process.

        Raises:
            LaunchError: If the button ID is not found.
        """
        if self._config is None:
            raise LaunchError("No configuration loaded")

        for shelf in self._config.shelves:
            for button in shelf.buttons:
                if button.id == button_id:
                    return self.launch(button)

        raise LaunchError(f"Button not found: {button_id}")
