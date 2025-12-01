# Nuke Auto Grade Tool
# Automatic color grading utilities

import nuke


def main():
    """Create auto grade setup."""
    selected = nuke.selectedNodes()

    if not selected:
        nuke.message("Please select a node")
        return

    input_node = selected[0]

    choices = ["Basic Grade", "Match Grade", "Auto White Balance", "Exposure Adjust"]
    panel = nuke.Panel("Auto Grade")
    panel.addEnumerationPulldown("Preset", " ".join(choices))

    if not panel.show():
        return

    preset = panel.value("Preset")

    if preset == "Basic Grade":
        # Create basic grade setup
        grade = nuke.createNode("Grade", inpanel=False)
        grade.setInput(0, input_node)
        grade['blackpoint'].setValue(0.0)
        grade['whitepoint'].setValue(1.0)
        grade['label'].setValue("Basic Grade")

    elif preset == "Match Grade":
        # Create match grade nodes
        colorspace = nuke.createNode("Colorspace", inpanel=False)
        colorspace.setInput(0, input_node)
        colorspace['colorspace_out'].setValue('rec709')

        match = nuke.createNode("MatchGrade", inpanel=False)
        match.setInput(0, colorspace)
        match['label'].setValue("Match to Reference")

    elif preset == "Auto White Balance":
        # Simple white balance
        grade = nuke.createNode("Grade", inpanel=False)
        grade.setInput(0, input_node)
        grade['label'].setValue("White Balance")

        # Add sample picker note
        note = nuke.createNode("StickyNote", inpanel=False)
        note['label'].setValue("Click on a neutral gray area\nand adjust multiply")

    elif preset == "Exposure Adjust":
        exposure = nuke.createNode("EXPTool", inpanel=False)
        exposure.setInput(0, input_node)
        exposure['label'].setValue("Exposure")

    nuke.message(f"Auto Grade '{preset}' created!")

if __name__ == "__main__":
    main()
