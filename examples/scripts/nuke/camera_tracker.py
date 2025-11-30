# Nuke Camera Tracker Tool
# Camera tracking utilities

import nuke

def main():
    """Create camera tracker setup."""
    selected = nuke.selectedNodes()
    
    if not selected:
        nuke.message("Please select a Read node")
        return
    
    input_node = selected[0]
    
    choices = ["CameraTracker", "PointTracker (2D)", "Planar Tracker", "Tracker4"]
    panel = nuke.Panel("Camera Tracker")
    panel.addEnumerationPulldown("Tracker Type", " ".join(choices))
    
    if not panel.show():
        return
    
    tracker_type = panel.value("Tracker Type")
    
    if tracker_type == "CameraTracker":
        # Create 3D camera tracker
        tracker = nuke.createNode("CameraTracker", inpanel=False)
        tracker.setInput(0, input_node)
        tracker['label'].setValue("Camera Track")
        
        # Create scene and camera nodes
        scene = nuke.createNode("Scene", inpanel=False)
        scene['label'].setValue("Tracked Scene")
        
        camera = nuke.createNode("Camera2", inpanel=False)
        camera['label'].setValue("Tracked Camera")
        
        nuke.message(
            "Camera Tracker created!\n\n"
            "Steps:\n"
            "1. Set frame range\n"
            "2. Click 'Track'\n"
            "3. Click 'Solve'\n"
            "4. Export to Camera/Scene"
        )
        
    elif tracker_type == "PointTracker (2D)":
        tracker = nuke.createNode("Tracker4", inpanel=False)
        tracker.setInput(0, input_node)
        tracker['label'].setValue("Point Tracker")
        
        # Add transform node linked to tracker
        transform = nuke.createNode("Transform", inpanel=False)
        transform.setInput(0, input_node)
        transform['label'].setValue("Tracked Transform")
        
        nuke.message("2D Point Tracker created!\nLink transform to tracker as needed")
        
    elif tracker_type == "Planar Tracker":
        tracker = nuke.createNode("PlanarTracker1_0", inpanel=False)
        tracker.setInput(0, input_node)
        tracker['label'].setValue("Planar Tracker")
        
        corner_pin = nuke.createNode("CornerPin2D", inpanel=False)
        corner_pin['label'].setValue("Tracked CornerPin")
        
        nuke.message("Planar Tracker created!\nExport to CornerPin when done")
        
    elif tracker_type == "Tracker4":
        tracker = nuke.createNode("Tracker4", inpanel=False)
        tracker.setInput(0, input_node)
        tracker['label'].setValue("Tracker")
        
        nuke.message("Tracker4 created!\nAdd tracks and start tracking")

if __name__ == "__main__":
    main()

