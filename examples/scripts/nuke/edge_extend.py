# Nuke Edge Extend Tool
# Edge extension utilities

import nuke

def main():
    """Create edge extend setup."""
    selected = nuke.selectedNodes()
    
    if not selected:
        nuke.message("Please select a node with alpha")
        return
    
    input_node = selected[0]
    
    choices = ["Blur Extend", "EdgeExtend Node", "Push Pixel", "Dilate + Blur"]
    panel = nuke.Panel("Edge Extend")
    panel.addEnumerationPulldown("Method", " ".join(choices))
    panel.addSingleLineInput("Amount", "10")
    
    if not panel.show():
        return
    
    method = panel.value("Method")
    amount = float(panel.value("Amount"))
    
    if method == "Blur Extend":
        # Unpremult -> Blur -> Clamp -> Premult
        unpremult = nuke.createNode("Unpremult", inpanel=False)
        unpremult.setInput(0, input_node)
        
        blur = nuke.createNode("Blur", inpanel=False)
        blur.setInput(0, unpremult)
        blur['size'].setValue(amount)
        blur['label'].setValue("Edge blur")
        
        copy = nuke.createNode("Copy", inpanel=False)
        copy.setInput(0, blur)
        copy.setInput(1, input_node)
        copy['from0'].setValue('rgba.alpha')
        copy['to0'].setValue('rgba.alpha')
        
        premult = nuke.createNode("Premult", inpanel=False)
        premult.setInput(0, copy)
        
    elif method == "EdgeExtend Node":
        edge_extend = nuke.createNode("EdgeExtend", inpanel=False)
        edge_extend.setInput(0, input_node)
        edge_extend['slices'].setValue(int(amount))
        edge_extend['label'].setValue("Edge Extend")
        
    elif method == "Push Pixel":
        # Simple dilate of RGB
        shuffle = nuke.createNode("Shuffle", inpanel=False)
        shuffle.setInput(0, input_node)
        shuffle['alpha'].setValue('white')
        
        dilate = nuke.createNode("Dilate", inpanel=False)
        dilate.setInput(0, shuffle)
        dilate['size'].setValue(amount)
        
        copy = nuke.createNode("Copy", inpanel=False)
        copy.setInput(0, dilate)
        copy.setInput(1, input_node)
        copy['from0'].setValue('rgba.alpha')
        copy['to0'].setValue('rgba.alpha')
        
    elif method == "Dilate + Blur":
        unpremult = nuke.createNode("Unpremult", inpanel=False)
        unpremult.setInput(0, input_node)
        
        dilate = nuke.createNode("Dilate", inpanel=False)
        dilate.setInput(0, unpremult)
        dilate['size'].setValue(amount / 2)
        
        blur = nuke.createNode("Blur", inpanel=False)
        blur.setInput(0, dilate)
        blur['size'].setValue(amount / 2)
        
        copy = nuke.createNode("Copy", inpanel=False)
        copy.setInput(0, blur)
        copy.setInput(1, input_node)
        copy['from0'].setValue('rgba.alpha')
        copy['to0'].setValue('rgba.alpha')
        
        premult = nuke.createNode("Premult", inpanel=False)
        premult.setInput(0, copy)
    
    nuke.message(f"Edge Extend '{method}' created!")

if __name__ == "__main__":
    main()

