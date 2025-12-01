# Houdini Mesh Repair Tool
# Fix common mesh issues

import hou


def main():
    """Open mesh repair interface."""
    selected = hou.selectedNodes()

    if not selected:
        hou.ui.displayMessage("Please select a geometry node", title="Mesh Repair")
        return

    choices = [
        "Full Repair (All fixes)",
        "Remove Degenerate Primitives",
        "Fuse Close Points",
        "Reverse Normals",
        "Make Manifold",
        "Clean Mesh",
        "Triangulate",
    ]

    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="Mesh Repair",
        message="Select repair operation:"
    )

    if not result:
        return

    operation = choices[result[0]]
    parent = selected[0].parent()
    input_node = selected[0]

    nodes_created = []
    last_node = input_node

    if operation == "Full Repair (All fixes)":
        # Create a sequence of repair nodes
        fuse = parent.createNode("fuse", "repair_fuse")
        fuse.setInput(0, last_node)
        fuse.parm("dist").set(0.001)
        nodes_created.append(fuse)
        last_node = fuse

        clean = parent.createNode("clean", "repair_clean")
        clean.setInput(0, last_node)
        clean.parm("removedegen").set(True)
        clean.parm("fixoverlap").set(True)
        nodes_created.append(clean)
        last_node = clean

        normal = parent.createNode("normal", "repair_normals")
        normal.setInput(0, last_node)
        normal.parm("type").set(0)  # Point normals
        nodes_created.append(normal)
        last_node = normal

    elif operation == "Remove Degenerate Primitives":
        clean = parent.createNode("clean", "remove_degen")
        clean.setInput(0, last_node)
        clean.parm("removedegen").set(True)
        nodes_created.append(clean)
        last_node = clean

    elif operation == "Fuse Close Points":
        fuse = parent.createNode("fuse", "fuse_points")
        fuse.setInput(0, last_node)
        fuse.parm("dist").set(0.001)
        nodes_created.append(fuse)
        last_node = fuse

    elif operation == "Reverse Normals":
        reverse = parent.createNode("reverse", "reverse_normals")
        reverse.setInput(0, last_node)
        nodes_created.append(reverse)
        last_node = reverse

    elif operation == "Make Manifold":
        # Use polydoctor for manifold check
        doctor = parent.createNode("polydoctor", "make_manifold")
        doctor.setInput(0, last_node)
        doctor.parm("nonmanifold").set(True)
        nodes_created.append(doctor)
        last_node = doctor

    elif operation == "Clean Mesh":
        clean = parent.createNode("clean", "clean_mesh")
        clean.setInput(0, last_node)
        nodes_created.append(clean)
        last_node = clean

    elif operation == "Triangulate":
        divide = parent.createNode("divide", "triangulate")
        divide.setInput(0, last_node)
        divide.parm("usemaxsides").set(True)
        divide.parm("maxsides").set(3)
        nodes_created.append(divide)
        last_node = divide

    # Layout and set flags
    for node in nodes_created:
        node.moveToGoodPosition()

    if nodes_created:
        last_node.setDisplayFlag(True)
        last_node.setRenderFlag(True)
        last_node.setSelected(True, clear_all_selected=True)

        hou.ui.displayMessage(
            f"Mesh repair complete!\nCreated {len(nodes_created)} node(s)",
            title="Mesh Repair"
        )

if __name__ == "__main__":
    main()
