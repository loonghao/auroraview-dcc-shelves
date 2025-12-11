#!/usr/bin/env python
"""Select all meshes in Maya scene - Maya only.

This script dynamically imports Maya modules when executed.
"""


def main() -> None:
    """Select all mesh objects in the scene."""
    try:
        import maya.cmds as cmds
    except ImportError:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Maya Required",
            "This tool requires Maya.\n\n"
            "Please run this tool from within Maya.",
        )
        root.destroy()
        return

    # Get all mesh transforms
    meshes = cmds.ls(type="mesh")
    if not meshes:
        cmds.confirmDialog(
            title="Select All Meshes",
            message="No meshes found in scene.",
            button=["OK"],
        )
        return

    # Get parent transforms
    transforms = list(set(cmds.listRelatives(meshes, parent=True, fullPath=True) or []))

    # Select them
    cmds.select(transforms, replace=True)

    cmds.confirmDialog(
        title="Select All Meshes",
        message=f"Selected {len(transforms)} mesh object(s).",
        button=["OK"],
    )


if __name__ == "__main__":
    main()

