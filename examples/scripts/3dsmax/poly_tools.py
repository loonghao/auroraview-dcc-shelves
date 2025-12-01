"""3ds Max Poly Tools - Editable Poly toolkit.

Provides quick access to common Editable Poly operations.
"""


def get_dcc():
    """Detect which DCC we're running in."""
    try:
        import pymxs
        return "3dsmax"
    except ImportError:
        pass
    return None


def show_message(title, message):
    """Show a message dialog appropriate for the DCC."""
    dcc = get_dcc()
    if dcc == "3dsmax":
        from pymxs import runtime as rt
        rt.messageBox(message, title=title)
    else:
        print(f"{title}: {message}")


def main():
    """Main entry point."""
    dcc = get_dcc()

    if dcc == "3dsmax":
        from pymxs import runtime as rt

        # Get current selection
        sel = rt.selection
        if len(sel) == 0:
            show_message("Poly Tools", "Please select an Editable Poly object")
            return

        obj = sel[0]

        # Check if it's Editable Poly
        if rt.classOf(obj) == rt.Editable_Poly:
            # Show poly info
            num_verts = rt.polyop.getNumVerts(obj)
            num_faces = rt.polyop.getNumFaces(obj)
            num_edges = rt.polyop.getNumEdges(obj)

            msg = f"Object: {obj.name}\n"
            msg += f"Vertices: {num_verts}\n"
            msg += f"Edges: {num_edges}\n"
            msg += f"Faces: {num_faces}"

            show_message("Poly Tools - Stats", msg)
        else:
            show_message("Poly Tools", f"Object is not Editable Poly: {rt.classOf(obj)}")
    else:
        show_message("Poly Tools", "This tool requires 3ds Max")


if __name__ == "__main__":
    main()
