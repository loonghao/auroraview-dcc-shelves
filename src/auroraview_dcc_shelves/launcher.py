"""Tool launcher module for executing Python scripts and executables.

This module provides the ToolLauncher class for running tools configured
in the shelf system.

For DCC applications (Maya, Houdini, Nuke), scripts are executed inline
using exec() to run in the same Python environment.

For standalone mode, scripts are launched as separate processes.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

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
        dcc_mode: If True, execute Python scripts inline using exec().
                  This is used for DCC apps (Maya, Houdini, Nuke) to run
                  scripts in the same Python environment.
    """

    def __init__(
        self,
        config: ShelvesConfig | None = None,
        python_executable: str | None = None,
        dcc_mode: bool = False,
    ) -> None:
        self._config = config
        self._python_executable = python_executable or sys.executable
        self._base_path = config.base_path if config else Path.cwd()
        self._dcc_mode = dcc_mode

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

    def launch(self, button: ButtonConfig) -> subprocess.Popen | dict[str, Any] | None:
        """Launch a tool based on its configuration.

        Execution behavior by tool type:
        - PYTHON: exec() in DCC mode, subprocess in standalone
        - EXECUTABLE: Always subprocess.Popen
        - MEL: maya.mel.eval() - Maya only
        - JAVASCRIPT: Returns script for WebView eval() - caller handles execution

        Args:
            button: The button configuration specifying the tool to launch.

        Returns:
            - subprocess.Popen for external process launches
            - dict for JavaScript (contains 'script' key for WebView eval)
            - None if executed inline (Python exec, MEL eval)

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
            # Executables always use subprocess
            return self._launch_executable(tool_path, button.args)
        elif button.tool_type == ToolType.MEL:
            return self._launch_mel(tool_path)
        elif button.tool_type == ToolType.JAVASCRIPT:
            return self._launch_javascript(tool_path)
        else:
            raise LaunchError(f"Unknown tool type: {button.tool_type}")

    def _launch_python(self, script_path: Path, args: list[str]) -> subprocess.Popen | None:
        """Launch a Python script.

        In DCC mode, scripts are executed inline using exec() to run in the
        same Python environment (e.g., Maya's Python interpreter).

        In standalone mode, scripts are launched as separate processes.

        Args:
            script_path: Path to the Python script.
            args: Command line arguments to pass.

        Returns:
            The Popen object for the launched process, or None if executed inline.
        """
        if script_path.suffix.lower() != ".py":
            logger.warning(f"Python tool path does not end with .py: {script_path}")

        # DCC mode: execute inline using exec()
        if self._dcc_mode:
            return self._exec_python_inline(script_path, args)

        # Standalone mode: launch as subprocess
        return self._launch_python_subprocess(script_path, args)

    def _exec_python_inline(self, script_path: Path, args: list[str]) -> None:
        """Execute a Python script inline using exec().

        This runs the script in the current Python environment, which is
        necessary for DCC applications like Maya, Houdini, and Nuke.

        Args:
            script_path: Path to the Python script.
            args: Command line arguments (set as sys.argv).

        Returns:
            None (script is executed inline).

        Raises:
            LaunchError: If the script fails to execute.
        """
        logger.info(f"Executing inline (DCC mode): {script_path}")

        # Save original sys.argv and sys.path
        original_argv = sys.argv.copy()
        original_path = sys.path.copy()

        try:
            # Set up sys.argv for the script
            sys.argv = [str(script_path), *args]

            # Add script's directory to sys.path
            script_dir = str(script_path.parent)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)

            # Read and execute the script
            script_content = script_path.read_text(encoding="utf-8")

            # Create globals dict with __file__ set correctly
            script_globals = {
                "__name__": "__main__",
                "__file__": str(script_path),
                "__builtins__": __builtins__,
            }

            # Execute the script
            exec(compile(script_content, str(script_path), "exec"), script_globals)  # noqa: S102

            logger.info(f"Script executed successfully: {script_path}")
            return None

        except Exception as e:
            logger.error(f"Error executing script {script_path}: {e}")
            raise LaunchError(f"Failed to execute script: {e}") from e

        finally:
            # Restore original sys.argv and sys.path
            sys.argv = original_argv
            sys.path = original_path

    def _launch_python_subprocess(self, script_path: Path, args: list[str]) -> subprocess.Popen:
        """Launch a Python script as a subprocess.

        Args:
            script_path: Path to the Python script.
            args: Command line arguments to pass.

        Returns:
            The Popen object for the launched process.
        """
        try:
            cmd = [self._python_executable, str(script_path), *args]
            logger.debug(f"Executing subprocess: {' '.join(cmd)}")

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

    def _launch_mel(self, script_path: Path) -> None:
        """Execute a MEL script in Maya.

        MEL scripts are executed via maya.mel.eval() and only work in Maya.

        Args:
            script_path: Path to the MEL script.

        Returns:
            None (script is executed inline).

        Raises:
            LaunchError: If Maya is not available or script fails.
        """
        logger.info(f"Executing MEL script: {script_path}")

        try:
            import maya.mel  # type: ignore[import-not-found]

            script_content = script_path.read_text(encoding="utf-8")
            maya.mel.eval(script_content)
            logger.info(f"MEL script executed successfully: {script_path}")
            return None

        except ImportError as e:
            raise LaunchError(
                "MEL scripts can only be executed in Maya. "
                "Please run this tool inside Maya."
            ) from e
        except Exception as e:
            logger.error(f"Error executing MEL script {script_path}: {e}")
            raise LaunchError(f"Failed to execute MEL script: {e}") from e

    def _launch_javascript(self, script_path: Path) -> dict[str, Any]:
        """Prepare JavaScript for WebView execution.

        JavaScript scripts are returned for the caller to execute via WebView.
        The actual eval() happens in the UI layer.

        Args:
            script_path: Path to the JavaScript file.

        Returns:
            Dict with 'type': 'javascript' and 'script' containing the code.

        Raises:
            LaunchError: If script cannot be read.
        """
        logger.info(f"Preparing JavaScript: {script_path}")

        try:
            script_content = script_path.read_text(encoding="utf-8")
            return {
                "type": "javascript",
                "script": script_content,
                "path": str(script_path),
            }
        except Exception as e:
            logger.error(f"Error reading JavaScript file {script_path}: {e}")
            raise LaunchError(f"Failed to read JavaScript file: {e}") from e
