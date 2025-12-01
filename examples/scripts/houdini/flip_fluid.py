# Houdini FLIP Fluid Tool
# Quick FLIP simulation setup

import hou


def main():
    """Create FLIP fluid simulation setup."""
    choices = [
        "Basic Water Tank",
        "Waterfall",
        "Ocean Splash",
        "Custom FLIP Source",
    ]

    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="FLIP Fluid",
        message="Select FLIP preset:"
    )

    if not result:
        return

    preset = choices[result[0]]
    obj = hou.node("/obj")

    # Create FLIP container
    flip_geo = obj.createNode("geo", f"flip_{preset.lower().replace(' ', '_')}")

    if preset == "Basic Water Tank":
        # Create box as container
        box = flip_geo.createNode("box", "tank")
        box.parm("sizex").set(4)
        box.parm("sizey").set(3)
        box.parm("sizez").set(4)
        box.parm("ty").set(1.5)

        # Create sphere as initial fluid
        sphere = flip_geo.createNode("sphere", "initial_fluid")
        sphere.parm("radx").set(1)
        sphere.parm("ty").set(2)

        # FLIP source
        flip_source = flip_geo.createNode("flipsource", "flip_source")
        flip_source.setInput(0, sphere)

        # Collision
        collision = flip_geo.createNode("staticobject", "tank_collision")
        collision.setInput(0, box)

    elif preset == "Waterfall":
        # Create emitter plane
        grid = flip_geo.createNode("grid", "emitter")
        grid.parm("sizex").set(2)
        grid.parm("sizey").set(0.5)
        grid.parm("ty").set(4)

        flip_source = flip_geo.createNode("flipsource", "flip_source")
        flip_source.setInput(0, grid)
        flip_source.parm("operation").set(1)  # Continuous emission

    elif preset == "Ocean Splash":
        # Create ocean surface
        grid = flip_geo.createNode("grid", "ocean_surface")
        grid.parm("sizex").set(10)
        grid.parm("sizey").set(10)

        ocean = flip_geo.createNode("oceanspectrum", "ocean_spectrum")
        ocean.setInput(0, grid)

        flip_source = flip_geo.createNode("flipsource", "flip_source")
        flip_source.setInput(0, ocean)

    elif preset == "Custom FLIP Source":
        flip_source = flip_geo.createNode("flipsource", "flip_source")
        hou.ui.displayMessage(
            "Connect your source geometry to flip_source input",
            title="Custom FLIP"
        )

    # Create particle fluid surface
    fluid_surface = flip_geo.createNode("particlefluidsurface", "fluid_surface")

    flip_geo.layoutChildren()
    hou.ui.displayMessage(f"FLIP '{preset}' created!", title="FLIP Fluid")

if __name__ == "__main__":
    main()
