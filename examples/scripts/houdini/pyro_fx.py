# Houdini Pyro FX Tool
# Quick pyro simulation setup

import hou

def main():
    """Create pyro simulation setup."""
    selected = hou.selectedNodes()
    
    choices = [
        "Fire (Flames)",
        "Smoke (Billowy)",
        "Explosion",
        "Custom Pyro Source",
    ]
    
    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="Pyro FX",
        message="Select pyro preset:"
    )
    
    if not result:
        return
    
    preset = choices[result[0]]
    
    # Get or create geo context
    obj = hou.node("/obj")
    
    # Create pyro container
    pyro_geo = obj.createNode("geo", f"pyro_{preset.lower().replace(' ', '_')}")
    
    if preset == "Fire (Flames)":
        # Create sphere as source
        sphere = pyro_geo.createNode("sphere", "fire_source")
        sphere.parm("radx").set(0.5)
        sphere.parm("rady").set(0.5)
        sphere.parm("radz").set(0.5)
        
        # Add pyro source
        pyro_source = pyro_geo.createNode("pyrosource", "pyro_source")
        pyro_source.setInput(0, sphere)
        pyro_source.parm("initialize").set(3)  # Flames
        
        # Create DOP network
        create_pyro_dopnet(pyro_geo, pyro_source, "fire")
        
    elif preset == "Smoke (Billowy)":
        sphere = pyro_geo.createNode("sphere", "smoke_source")
        pyro_source = pyro_geo.createNode("pyrosource", "pyro_source")
        pyro_source.setInput(0, sphere)
        pyro_source.parm("initialize").set(2)  # Smoke
        
        create_pyro_dopnet(pyro_geo, pyro_source, "smoke")
        
    elif preset == "Explosion":
        sphere = pyro_geo.createNode("sphere", "explosion_source")
        sphere.parm("radx").set(0.3)
        
        pyro_source = pyro_geo.createNode("pyrosource", "pyro_source")
        pyro_source.setInput(0, sphere)
        pyro_source.parm("initialize").set(1)  # Fireball
        
        create_pyro_dopnet(pyro_geo, pyro_source, "explosion")
        
    elif preset == "Custom Pyro Source":
        if selected:
            # Use selected geometry as source
            pyro_source = pyro_geo.createNode("pyrosource", "pyro_source")
            # User needs to connect their own source
            hou.ui.displayMessage(
                "Connect your source geometry to pyro_source input",
                title="Custom Pyro"
            )
        else:
            hou.ui.displayMessage("Select a geometry node first", title="Custom Pyro")
            return
    
    pyro_geo.layoutChildren()
    hou.ui.displayMessage(f"Pyro FX '{preset}' created!", title="Pyro FX")

def create_pyro_dopnet(geo_node, source_node, sim_type):
    """Create DOP network for pyro simulation."""
    # Create DOP import
    dop_import = geo_node.createNode("dopimport", "import_pyro")
    
    # Create DOP network at OBJ level
    obj = hou.node("/obj")
    dopnet = obj.createNode("dopnet", f"{sim_type}_sim")
    
    # Inside DOP, create pyro solver
    pyro_solver = dopnet.createNode("pyrosolver", f"{sim_type}_solver")
    pyro_solver.parm("resolutionscale").set(0.5)  # Lower res for preview
    
    # Set source reference
    dop_import.parm("doppath").set(dopnet.path())
    
    geo_node.layoutChildren()

if __name__ == "__main__":
    main()

