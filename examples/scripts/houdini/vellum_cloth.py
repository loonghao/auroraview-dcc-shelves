# Houdini Vellum Cloth Tool
# Quick cloth simulation setup

import hou

def main():
    """Create Vellum cloth simulation setup."""
    selected = hou.selectedNodes()
    
    choices = [
        "Cloth from Selection",
        "Draped Cloth (Grid)",
        "Flag",
        "Curtain",
    ]
    
    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="Vellum Cloth",
        message="Select cloth setup:"
    )
    
    if not result:
        return
    
    preset = choices[result[0]]
    
    if preset == "Cloth from Selection":
        if not selected:
            hou.ui.displayMessage("Please select a geometry node", title="Vellum Cloth")
            return
        create_vellum_cloth(selected[0])
    else:
        obj = hou.node("/obj")
        cloth_geo = obj.createNode("geo", f"vellum_{preset.lower().replace(' ', '_')}")
        
        if preset == "Draped Cloth (Grid)":
            grid = cloth_geo.createNode("grid", "cloth_grid")
            grid.parm("sizex").set(4)
            grid.parm("sizey").set(4)
            grid.parm("rows").set(30)
            grid.parm("cols").set(30)
            grid.parm("ty").set(3)
            create_vellum_cloth_network(cloth_geo, grid)
            
        elif preset == "Flag":
            grid = cloth_geo.createNode("grid", "flag")
            grid.parm("sizex").set(3)
            grid.parm("sizey").set(2)
            grid.parm("rows").set(20)
            grid.parm("cols").set(30)
            
            # Group for pin constraint (left edge)
            group = cloth_geo.createNode("groupexpression", "pin_edge")
            group.setInput(0, grid)
            group.parm("groupname").set("pinned")
            group.parm("grouptype").set(0)  # Points
            group.parm("group1syntax").set(1)  # VEX
            group.parm("snippet1").set('@P.x < -1.4')
            
            create_vellum_cloth_network(cloth_geo, group, pin_group="pinned")
            
        elif preset == "Curtain":
            grid = cloth_geo.createNode("grid", "curtain")
            grid.parm("sizex").set(4)
            grid.parm("sizey").set(3)
            grid.parm("rows").set(40)
            grid.parm("cols").set(50)
            grid.parm("ty").set(1.5)
            
            # Pin top edge
            group = cloth_geo.createNode("groupexpression", "pin_top")
            group.setInput(0, grid)
            group.parm("groupname").set("pinned")
            group.parm("snippet1").set('@P.y > 1.4')
            
            create_vellum_cloth_network(cloth_geo, group, pin_group="pinned")
        
        cloth_geo.layoutChildren()
        hou.ui.displayMessage(f"Vellum '{preset}' created!", title="Vellum Cloth")

def create_vellum_cloth(input_node):
    """Create vellum cloth from existing geometry."""
    parent = input_node.parent()
    create_vellum_cloth_network(parent, input_node)

def create_vellum_cloth_network(geo_node, source_node, pin_group=""):
    """Create the vellum cloth network."""
    # Vellum configure cloth
    vellum_cloth = geo_node.createNode("vellumcloth", "vellum_cloth")
    vellum_cloth.setInput(0, source_node)
    
    # Add pin constraint if group specified
    if pin_group:
        vellum_cloth.parm("pintargetgroup").set(pin_group)
    
    # Vellum solver
    vellum_solver = geo_node.createNode("vellumsolver", "vellum_solver")
    vellum_solver.setInput(0, vellum_cloth, 0)
    vellum_solver.setInput(1, vellum_cloth, 1)
    
    # Post process
    post = geo_node.createNode("vellumpostprocess", "post_process")
    post.setInput(0, vellum_solver)
    
    post.setDisplayFlag(True)
    post.setRenderFlag(True)
    
    geo_node.layoutChildren()

if __name__ == "__main__":
    main()

