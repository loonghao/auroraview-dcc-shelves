# Nuke Keyer Pro Tool
# Advanced keying utilities

import nuke

def main():
    """Create keyer setup."""
    selected = nuke.selectedNodes()
    
    if not selected:
        nuke.message("Please select a node")
        return
    
    input_node = selected[0]
    
    choices = ["Primatte", "Keylight", "IBK Color + Gizmo", "Difference Key", "Luma Key"]
    panel = nuke.Panel("Keyer Pro")
    panel.addEnumerationPulldown("Keyer Type", " ".join(choices))
    
    if not panel.show():
        return
    
    keyer_type = panel.value("Keyer Type")
    
    if keyer_type == "Primatte":
        keyer = nuke.createNode("Primatte3", inpanel=False)
        keyer.setInput(0, input_node)
        keyer['label'].setValue("Primatte Keyer")
        
    elif keyer_type == "Keylight":
        keyer = nuke.createNode("Keylight", inpanel=False)
        keyer.setInput(0, input_node)
        keyer['label'].setValue("Keylight")
        
    elif keyer_type == "IBK Color + Gizmo":
        # IBK workflow
        ibk_colour = nuke.createNode("IBKColour", inpanel=False)
        ibk_colour.setInput(0, input_node)
        ibk_colour['label'].setValue("IBK Color")
        
        ibk_gizmo = nuke.createNode("IBKGizmo", inpanel=False)
        ibk_gizmo.setInput(0, input_node)
        ibk_gizmo.setInput(1, ibk_colour)
        ibk_gizmo['label'].setValue("IBK Gizmo")
        
    elif keyer_type == "Difference Key":
        diff = nuke.createNode("Difference", inpanel=False)
        diff.setInput(0, input_node)
        diff['label'].setValue("Connect clean plate to input 2")
        
    elif keyer_type == "Luma Key":
        keyer = nuke.createNode("Keyer", inpanel=False)
        keyer.setInput(0, input_node)
        keyer['operation'].setValue('luminance key')
        keyer['label'].setValue("Luma Keyer")
    
    # Add common post-key nodes
    erode = nuke.createNode("FilterErode", inpanel=False)
    erode['label'].setValue("Edge refine")
    
    premult = nuke.createNode("Premult", inpanel=False)
    premult['label'].setValue("Premult output")
    
    nuke.message(f"Keyer Pro '{keyer_type}' created!")

if __name__ == "__main__":
    main()

