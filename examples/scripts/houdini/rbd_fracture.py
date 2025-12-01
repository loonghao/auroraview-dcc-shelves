# Houdini RBD Fracture Tool
# Quick destruction setup

import hou


def main():
    """Create RBD fracture setup."""
    selected = hou.selectedNodes()

    if not selected:
        hou.ui.displayMessage("Please select a geometry node to fracture", title="RBD Fracture")
        return

    choices = [
        "Voronoi Fracture (Uniform)",
        "Voronoi Fracture (Clustered)",
        "Boolean Fracture",
        "Edge Fracture",
    ]

    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="RBD Fracture",
        message="Select fracture type:"
    )

    if not result:
        return

    fracture_type = choices[result[0]]
    parent = selected[0].parent()
    input_node = selected[0]

    nodes_created = []
    last_node = input_node

    if fracture_type == "Voronoi Fracture (Uniform)":
        # Scatter points
        scatter = parent.createNode("scatter", "fracture_points")
        scatter.setInput(0, input_node)
        scatter.parm("npts").set(50)
        nodes_created.append(scatter)

        # Voronoi fracture
        voronoi = parent.createNode("voronoifracture", "voronoi_fracture")
        voronoi.setInput(0, input_node)
        voronoi.setInput(1, scatter)
        nodes_created.append(voronoi)
        last_node = voronoi

    elif fracture_type == "Voronoi Fracture (Clustered)":
        # Scatter with clustering
        scatter = parent.createNode("scatter", "fracture_points")
        scatter.setInput(0, input_node)
        scatter.parm("npts").set(100)
        nodes_created.append(scatter)

        # Cluster
        cluster = parent.createNode("cluster", "cluster_points")
        cluster.setInput(0, scatter)
        cluster.parm("numclusters").set(20)
        nodes_created.append(cluster)

        # Voronoi
        voronoi = parent.createNode("voronoifracture", "voronoi_fracture")
        voronoi.setInput(0, input_node)
        voronoi.setInput(1, cluster)
        voronoi.parm("cuspnormals").set(True)
        nodes_created.append(voronoi)
        last_node = voronoi

    elif fracture_type == "Boolean Fracture":
        bool_frac = parent.createNode("booleanfracture", "boolean_fracture")
        bool_frac.setInput(0, input_node)
        bool_frac.parm("numpieces").set(30)
        nodes_created.append(bool_frac)
        last_node = bool_frac

    elif fracture_type == "Edge Fracture":
        # Use edge groups for controlled breaking
        edge_frac = parent.createNode("edgefracture", "edge_fracture")
        edge_frac.setInput(0, input_node)
        nodes_created.append(edge_frac)
        last_node = edge_frac

    # Add assemble for packing
    assemble = parent.createNode("assemble", "pack_pieces")
    assemble.setInput(0, last_node)
    assemble.parm("create_packed").set(True)
    nodes_created.append(assemble)
    last_node = assemble

    # Layout
    for node in nodes_created:
        node.moveToGoodPosition()

    last_node.setDisplayFlag(True)
    last_node.setRenderFlag(True)

    hou.ui.displayMessage(
        f"Fracture complete!\n\n"
        f"• {len(nodes_created)} nodes created\n"
        f"• Ready for RBD simulation",
        title="RBD Fracture"
    )

if __name__ == "__main__":
    main()
