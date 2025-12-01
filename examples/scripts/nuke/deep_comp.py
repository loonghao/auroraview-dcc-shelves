# Nuke Deep Comp Tool
# Deep compositing utilities

import nuke


def main():
    """Create deep compositing setup."""
    selected = nuke.selectedNodes()

    choices = ["Deep Merge", "Deep to Image", "Image to Deep", "Deep Recolor", "Deep Holdout"]
    panel = nuke.Panel("Deep Comp")
    panel.addEnumerationPulldown("Operation", " ".join(choices))

    if not panel.show():
        return

    operation = panel.value("Operation")
    input_node = selected[0] if selected else None

    if operation == "Deep Merge":
        merge = nuke.createNode("DeepMerge", inpanel=False)
        merge['label'].setValue("Deep Merge")
        if input_node:
            merge.setInput(0, input_node)
        nuke.message("Deep Merge created!\nConnect deep inputs")

    elif operation == "Deep to Image":
        if not input_node:
            nuke.message("Select a deep node")
            return
        flatten = nuke.createNode("DeepToImage", inpanel=False)
        flatten.setInput(0, input_node)
        flatten['label'].setValue("Flatten Deep")

    elif operation == "Image to Deep":
        if not input_node:
            nuke.message("Select an image node")
            return
        to_deep = nuke.createNode("DeepFromImage", inpanel=False)
        to_deep.setInput(0, input_node)
        to_deep['label'].setValue("Convert to Deep")

    elif operation == "Deep Recolor":
        if not input_node:
            nuke.message("Select a deep node")
            return
        recolor = nuke.createNode("DeepRecolor", inpanel=False)
        recolor.setInput(0, input_node)
        recolor['label'].setValue("Deep Recolor\n(Connect 2D color)")
        nuke.message("Connect your 2D color pass to input 2")

    elif operation == "Deep Holdout":
        if not input_node:
            nuke.message("Select a deep node")
            return
        holdout = nuke.createNode("DeepHoldout", inpanel=False)
        holdout.setInput(0, input_node)
        holdout['label'].setValue("Deep Holdout")
        nuke.message("Connect holdout matte to input 2")

    nuke.message(f"Deep '{operation}' created!")

if __name__ == "__main__":
    main()
