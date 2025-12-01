# Houdini VDB Tools
# VDB conversion and editing utilities

import hou


def main():
    """Open VDB tools interface."""
    selected = hou.selectedNodes()

    if not selected:
        hou.ui.displayMessage("Please select a geometry node", title="VDB Tools")
        return

    choices = [
        "Convert to VDB",
        "VDB Smooth",
        "VDB Reshape (Dilate)",
        "VDB Reshape (Erode)",
        "VDB to Polygons",
        "VDB Combine (Union)",
    ]

    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="VDB Tools",
        message="Select operation:"
    )

    if not result:
        return

    operation = choices[result[0]]
    parent = selected[0].parent()
    input_node = selected[0]

    new_node = None

    if operation == "Convert to VDB":
        new_node = parent.createNode("vdbfrompolygons", "mesh_to_vdb")
        new_node.setInput(0, input_node)
        new_node.parm("voxelsize").set(0.05)

    elif operation == "VDB Smooth":
        new_node = parent.createNode("vdbsmooth", "vdb_smooth")
        new_node.setInput(0, input_node)
        new_node.parm("iterations").set(3)

    elif operation == "VDB Reshape (Dilate)":
        new_node = parent.createNode("vdbreshapesdf", "vdb_dilate")
        new_node.setInput(0, input_node)
        new_node.parm("operation").set(0)  # Dilate
        new_node.parm("offset").set(0.1)

    elif operation == "VDB Reshape (Erode)":
        new_node = parent.createNode("vdbreshapesdf", "vdb_erode")
        new_node.setInput(0, input_node)
        new_node.parm("operation").set(1)  # Erode
        new_node.parm("offset").set(0.1)

    elif operation == "VDB to Polygons":
        new_node = parent.createNode("convertvdb", "vdb_to_poly")
        new_node.setInput(0, input_node)
        new_node.parm("conversion").set(0)  # To polygons

    elif operation == "VDB Combine (Union)":
        new_node = parent.createNode("vdbcombine", "vdb_combine")
        new_node.setInput(0, input_node)
        new_node.parm("operation").set(0)  # Union

    if new_node:
        new_node.moveToGoodPosition()
        new_node.setDisplayFlag(True)
        new_node.setRenderFlag(True)
        new_node.setSelected(True, clear_all_selected=True)

        hou.ui.displayMessage(f"Created: {new_node.name()}", title="VDB Tools")

if __name__ == "__main__":
    main()
