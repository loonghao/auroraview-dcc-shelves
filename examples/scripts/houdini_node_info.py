#!/usr/bin/env python
"""Houdini node info tool - Houdini only.

This script dynamically imports Houdini modules when executed.
"""


def main() -> None:
    """Display selected node information in Houdini."""
    try:
        import hou
    except ImportError:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Houdini Required",
            "This tool requires Houdini.\n\n"
            "Please run this tool from within Houdini.",
        )
        root.destroy()
        return

    # Get selected nodes
    selected = hou.selectedNodes()

    if not selected:
        hou.ui.displayMessage(
            "No nodes selected.\n\nPlease select one or more nodes.",
            title="Node Info",
        )
        return

    info_lines = []
    for node in selected:
        info_lines.extend([
            f"Node: {node.name()}",
            f"  Path: {node.path()}",
            f"  Type: {node.type().name()}",
            f"  Category: {node.type().category().name()}",
            f"  Inputs: {len(node.inputs())}",
            f"  Outputs: {len(node.outputs())}",
            "",
        ])

    hou.ui.displayMessage(
        "\n".join(info_lines),
        title=f"Node Info ({len(selected)} selected)",
    )


if __name__ == "__main__":
    main()
