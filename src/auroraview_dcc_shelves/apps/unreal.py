"""Unreal Engine DCC Adapter.

Handles Unreal Engine-specific integration including:
- Main window detection via unreal module
- HWND integration for Slate embedding
- Fast timer settings for game engine responsiveness
"""

from __future__ import annotations

import logging
from typing import Any

from .base import DCCAdapter, register_adapter

logger = logging.getLogger(__name__)


@register_adapter
class UnrealAdapter(DCCAdapter):
    """Adapter for Epic Games Unreal Engine."""

    name = "Unreal"
    aliases = ["unreal", "ue", "ue4", "ue5"]
    timer_interval_ms = 16  # 60 FPS - game engine needs responsiveness
    recommended_mode = "hwnd"  # HWND mode works better with Slate

    def get_main_window(self) -> Any | None:
        """Get Unreal Engine main window as QWidget.

        Unreal uses Slate UI, not Qt, so this mainly searches
        for any Qt wrapper around the editor window.
        """
        try:
            from qtpy.QtWidgets import QApplication
        except ImportError:
            logger.warning("Qt not available")
            return None

        # Try to access Unreal to verify we're in UE
        try:
            import unreal
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        except Exception:
            pass

        # Search for Unreal window in Qt widgets (if using Qt wrapper)
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                title = widget.windowTitle()
                class_name = widget.metaObject().className()
                if ("Unreal" in title or "UE" in title or
                    "SWindow" in class_name or "FSlateApplication" in class_name):
                    return widget

        logger.warning("Could not find Unreal main window")
        return None

    def get_additional_api_methods(self) -> dict[str, callable]:
        """Add Unreal-specific API methods."""
        return {
            "execute_python": self._execute_python,
            "get_project_name": self._get_project_name,
            "get_hwnd_for_slate": self._get_hwnd_for_slate,
        }

    def _execute_python(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Python code in Unreal's context.

        Args:
            params: Dict with "code" key containing Python code.

        Returns:
            Dict with success status and result/error.
        """
        if not params or "code" not in params:
            return {"success": False, "error": "No code provided"}

        try:
            exec_globals = {"unreal": __import__("unreal")}
            exec(params["code"], exec_globals)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_project_name(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get current Unreal project name.

        Returns:
            Dict with project name or error.
        """
        try:
            import unreal
            project_file = unreal.Paths.get_project_file_path()
            return {"success": True, "project_name": project_file}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_hwnd_for_slate(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get HWND that can be used for Slate embedding.

        This is called from JavaScript to get the HWND for embedding
        the AuroraView window into Unreal's Slate UI.

        Returns:
            Dict with hwnd value or error.
        """
        # This will be populated by ShelfApp after window creation
        return {"success": False, "error": "HWND not available yet"}

    def on_show(self, shelf_app: Any) -> None:
        """Unreal-specific post-show setup.

        Provides HWND for Slate embedding if using HWND mode.
        """
        if hasattr(shelf_app, "get_hwnd"):
            hwnd = shelf_app.get_hwnd()
            if hwnd:
                logger.info(f"Unreal HWND available for Slate: {hwnd}")
                # Could auto-embed into Slate here if desired

    def embed_in_slate(self, hwnd: int) -> bool:
        """Embed the given HWND into Unreal's Slate UI.

        Args:
            hwnd: Native window handle to embed.

        Returns:
            True if embedding succeeded.
        """
        try:
            import unreal
            unreal.parent_external_window_to_slate(hwnd)
            logger.info(f"Embedded HWND {hwnd} into Slate")
            return True
        except Exception as e:
            logger.error(f"Failed to embed in Slate: {e}")
            return False

