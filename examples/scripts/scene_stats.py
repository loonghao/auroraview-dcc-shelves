#!/usr/bin/env python
"""Universal scene statistics - Maya and Houdini.

This script detects the current DCC environment and displays
appropriate scene statistics.
"""


def get_maya_stats() -> str:
    """Get Maya scene statistics."""
    import maya.cmds as cmds

    scene_name = cmds.file(q=True, sceneName=True) or "Untitled"
    stats = {
        "Scene": scene_name,
        "Transforms": len(cmds.ls(type="transform")),
        "Meshes": len(cmds.ls(type="mesh")),
        "Curves": len(cmds.ls(type="nurbsCurve")),
        "Cameras": len(cmds.ls(type="camera")),
        "Lights": len(cmds.ls(type="light")),
        "Materials": len(cmds.ls(materials=True)),
        "Textures": len(cmds.ls(textures=True)),
    }
    return "\n".join(f"{k}: {v}" for k, v in stats.items())


def get_houdini_stats() -> str:
    """Get Houdini scene statistics."""
    import hou

    stats = {
        "Hip File": hou.hipFile.name() or "Untitled",
        "Total Nodes": len(hou.node("/").allSubChildren()),
        "OBJ Nodes": len(hou.node("/obj").children()) if hou.node("/obj") else 0,
        "SOP Nodes": sum(1 for n in hou.node("/").allSubChildren() 
                        if n.type().category().name() == "Sop"),
        "Materials": len(hou.node("/mat").children()) if hou.node("/mat") else 0,
    }
    return "\n".join(f"{k}: {v}" for k, v in stats.items())


def show_fallback_error() -> None:
    """Show error for unsupported environment."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Unsupported Environment",
        "This tool requires Maya or Houdini.\n\n"
        "Supported DCCs:\n"
        "- Autodesk Maya\n"
        "- SideFX Houdini",
    )
    root.destroy()


def main() -> None:
    """Detect environment and show scene statistics."""
    # Try Maya first
    try:
        import maya.cmds as cmds
        stats = get_maya_stats()
        cmds.confirmDialog(
            title="Scene Statistics (Maya)",
            message=stats,
            button=["OK"],
        )
        return
    except ImportError:
        pass

    # Try Houdini
    try:
        import hou
        stats = get_houdini_stats()
        hou.ui.displayMessage(stats, title="Scene Statistics (Houdini)")
        return
    except ImportError:
        pass

    # Fallback
    show_fallback_error()


if __name__ == "__main__":
    main()

