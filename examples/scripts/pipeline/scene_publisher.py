# Pipeline Scene Publisher
# Publish current scene (works in Maya, Houdini, Nuke)

import os
import sys
from datetime import datetime

def get_dcc():
    """Detect current DCC application."""
    try:
        import maya.cmds
        return "maya"
    except:
        pass
    try:
        import hou
        return "houdini"
    except:
        pass
    try:
        import nuke
        return "nuke"
    except:
        pass
    return "standalone"

def publish_maya():
    """Publish Maya scene."""
    import maya.cmds as cmds
    
    scene_path = cmds.file(q=True, sceneName=True)
    if not scene_path:
        cmds.warning("Save scene first")
        return
    
    if cmds.window("publishWindow", exists=True):
        cmds.deleteUI("publishWindow")
    
    window = cmds.window("publishWindow", title="Scene Publisher", widthHeight=(350, 200))
    cmds.columnLayout(adjustableColumn=True)
    
    cmds.text(label=f"Scene: {os.path.basename(scene_path)}")
    cmds.separator(height=10)
    
    cmds.textFieldGrp("commentField", label="Comment:", text="")
    cmds.checkBoxGrp("exportCheck", label="Export:", 
                     labelArray2=["Alembic", "FBX"], valueArray2=[True, False])
    cmds.separator(height=10)
    
    cmds.button(label="Publish", command=lambda x: do_publish_maya())
    cmds.showWindow(window)

def do_publish_maya():
    """Execute Maya publish."""
    import maya.cmds as cmds
    
    comment = cmds.textFieldGrp("commentField", q=True, text=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">Published!</span> {timestamp}',
        pos='midCenter', fade=True
    )
    cmds.deleteUI("publishWindow")

def publish_houdini():
    """Publish Houdini scene."""
    import hou
    
    hip_path = hou.hipFile.path()
    if hip_path == "untitled.hip":
        hou.ui.displayMessage("Save file first", title="Publish")
        return
    
    result = hou.ui.readMultiInput(
        "Publish Scene",
        ("Comment",),
        buttons=("Publish", "Cancel"),
        title="Scene Publisher"
    )
    
    if result[0] == 0:  # Publish pressed
        comment = result[1][0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hou.ui.displayMessage(
            f"Published!\n\n"
            f"Time: {timestamp}\n"
            f"Comment: {comment or 'No comment'}",
            title="Publish Complete"
        )

def publish_nuke():
    """Publish Nuke script."""
    import nuke
    
    script_path = nuke.root().name()
    if script_path == "Root":
        nuke.message("Save script first")
        return
    
    panel = nuke.Panel("Scene Publisher")
    panel.addSingleLineInput("Comment", "")
    
    if panel.show():
        comment = panel.value("Comment")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuke.message(f"Published!\n\nTime: {timestamp}\nComment: {comment or 'No comment'}")

def main():
    """Main entry point."""
    dcc = get_dcc()
    
    if dcc == "maya":
        publish_maya()
    elif dcc == "houdini":
        publish_houdini()
    elif dcc == "nuke":
        publish_nuke()
    else:
        print("Scene Publisher - Standalone mode not supported")

if __name__ == "__main__":
    main()

