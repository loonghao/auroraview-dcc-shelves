# Houdini Scatter Pro Tool
# Advanced point scattering utilities

import hou

def main():
    """Create advanced scatter setup."""
    # Get selected node
    selected = hou.selectedNodes()
    
    if not selected:
        hou.ui.displayMessage("Please select a geometry node", title="Scatter Pro")
        return
    
    parent = selected[0].parent()
    input_node = selected[0]
    
    # Create scatter network
    scatter = parent.createNode("scatter", "scatter_pro")
    scatter.setInput(0, input_node)
    scatter.parm("npts").set(1000)
    
    # Add attribute randomize for variation
    attr_rand = parent.createNode("attribrandomize", "point_variation")
    attr_rand.setInput(0, scatter)
    attr_rand.parm("name").set("pscale")
    attr_rand.parm("min").set(0.5)
    attr_rand.parm("max").set(1.5)
    
    # Add copy to points (optional setup)
    copy = parent.createNode("copytopoints", "instance_points")
    copy.setInput(1, attr_rand)
    
    # Layout nodes
    scatter.moveToGoodPosition()
    attr_rand.moveToGoodPosition()
    copy.moveToGoodPosition()
    
    # Set display flag on last node
    attr_rand.setDisplayFlag(True)
    attr_rand.setRenderFlag(True)
    
    hou.ui.displayMessage(
        f"Scatter Pro created!\n\n"
        f"• scatter_pro: Point scattering\n"
        f"• point_variation: Random pscale\n"
        f"• instance_points: Ready for instancing",
        title="Scatter Pro"
    )

if __name__ == "__main__":
    main()

