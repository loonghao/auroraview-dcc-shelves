# Houdini Hair Groom Tool
# Quick hair/fur grooming setup

import hou


def main():
    """Create hair grooming setup."""
    selected = hou.selectedNodes()

    if not selected:
        hou.ui.displayMessage("Please select a geometry node for hair growth", title="Hair Groom")
        return

    choices = [
        "Basic Hair Setup",
        "Fur Setup",
        "Grass/Vegetation",
        "Custom Guides",
    ]

    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="Hair Groom",
        message="Select hair type:"
    )

    if not result:
        return

    preset = choices[result[0]]
    parent = selected[0].parent()
    input_node = selected[0]

    nodes = []

    if preset == "Basic Hair Setup":
        # Add fur
        add_fur = parent.createNode("add", "hair_roots")
        add_fur.setInput(0, input_node)
        nodes.append(add_fur)

        # Scatter for roots
        scatter = parent.createNode("scatter", "root_points")
        scatter.setInput(0, input_node)
        scatter.parm("npts").set(5000)
        nodes.append(scatter)

        # Hair generate
        hair_gen = parent.createNode("hairgen", "hair_generate")
        hair_gen.setInput(0, input_node)
        hair_gen.setInput(1, scatter)
        hair_gen.parm("length").set(0.5)
        hair_gen.parm("segments").set(8)
        nodes.append(hair_gen)

        last_node = hair_gen

    elif preset == "Fur Setup":
        scatter = parent.createNode("scatter", "fur_roots")
        scatter.setInput(0, input_node)
        scatter.parm("npts").set(20000)
        nodes.append(scatter)

        hair_gen = parent.createNode("hairgen", "fur_generate")
        hair_gen.setInput(0, input_node)
        hair_gen.setInput(1, scatter)
        hair_gen.parm("length").set(0.1)
        hair_gen.parm("segments").set(4)
        nodes.append(hair_gen)

        last_node = hair_gen

    elif preset == "Grass/Vegetation":
        scatter = parent.createNode("scatter", "grass_roots")
        scatter.setInput(0, input_node)
        scatter.parm("npts").set(10000)
        nodes.append(scatter)

        hair_gen = parent.createNode("hairgen", "grass_generate")
        hair_gen.setInput(0, input_node)
        hair_gen.setInput(1, scatter)
        hair_gen.parm("length").set(0.3)
        hair_gen.parm("lengthnoise").set(0.5)
        hair_gen.parm("segments").set(5)
        nodes.append(hair_gen)

        last_node = hair_gen

    elif preset == "Custom Guides":
        # Create guide curves for manual styling
        guide_groom = parent.createNode("guidegroom", "guide_groom")
        guide_groom.setInput(0, input_node)
        nodes.append(guide_groom)

        hair_gen = parent.createNode("hairgen", "hair_from_guides")
        hair_gen.setInput(0, input_node)
        hair_gen.setInput(2, guide_groom)
        nodes.append(hair_gen)

        last_node = hair_gen

    # Layout nodes
    for node in nodes:
        node.moveToGoodPosition()

    last_node.setDisplayFlag(True)
    last_node.setRenderFlag(True)

    hou.ui.displayMessage(
        f"Hair '{preset}' created!\n\n"
        f"Tip: Use Guide Groom node to style hair",
        title="Hair Groom"
    )

if __name__ == "__main__":
    main()
