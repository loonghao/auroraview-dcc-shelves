#!/usr/bin/env python
"""Maya scene info tool - Maya only.

This script dynamically imports Maya modules when executed,
so it has no dependency at import time.
"""


def main() -> None:
    """Display Maya scene information."""
    try:
        import maya.cmds as cmds
    except ImportError:
        # Fallback for standalone testing
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

    # Get scene info
    scene_name = cmds.file(q=True, sceneName=True) or "Untitled"
    obj_count = len(cmds.ls(dag=True, type="transform"))
    mesh_count = len(cmds.ls(type="mesh"))
    camera_count = len(cmds.ls(type="camera"))
    light_count = len(cmds.ls(type="light"))
    material_count = len(cmds.ls(materials=True))

    # Frame range
    start_frame = cmds.playbackOptions(q=True, minTime=True)
    end_frame = cmds.playbackOptions(q=True, maxTime=True)

    info = (
        f"Scene: {scene_name}\n\n"
        f"Objects: {obj_count}\n"
        f"Meshes: {mesh_count}\n"
        f"Cameras: {camera_count}\n"
        f"Lights: {light_count}\n"
        f"Materials: {material_count}\n\n"
        f"Frame Range: {int(start_frame)} - {int(end_frame)}"
    )

    cmds.confirmDialog(
        title="Maya Scene Info",
        message=info,
        button=["OK"],
        defaultButton="OK",
    )


if __name__ == "__main__":
    main()

