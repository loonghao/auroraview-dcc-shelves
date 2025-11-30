# Pipeline Shot Loader
# Load shot context (works in Maya, Houdini, Nuke)

import os
import sys

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

def show_maya_loader():
    """Show shot loader in Maya."""
    import maya.cmds as cmds
    
    if cmds.window("shotLoaderWindow", exists=True):
        cmds.deleteUI("shotLoaderWindow")
    
    window = cmds.window("shotLoaderWindow", title="Shot Loader", widthHeight=(350, 250))
    cmds.columnLayout(adjustableColumn=True)
    
    cmds.text(label="Shot Loader", font="boldLabelFont")
    cmds.separator(height=10)
    
    cmds.textFieldGrp("projectField", label="Project:", text="MyProject")
    cmds.textFieldGrp("sequenceField", label="Sequence:", text="SEQ010")
    cmds.textFieldGrp("shotField", label="Shot:", text="SH0010")
    cmds.separator(height=10)
    
    cmds.button(label="Load Shot Context", command=lambda x: load_shot_maya())
    cmds.button(label="Open Latest Workfile", command=lambda x: cmds.inViewMessage(
        amg='<span style="color:#00ff00;">Loading</span> latest workfile...',
        pos='midCenter', fade=True
    ))
    
    cmds.showWindow(window)

def load_shot_maya():
    """Load shot context in Maya."""
    import maya.cmds as cmds
    
    project = cmds.textFieldGrp("projectField", q=True, text=True)
    sequence = cmds.textFieldGrp("sequenceField", q=True, text=True)
    shot = cmds.textFieldGrp("shotField", q=True, text=True)
    
    # Set environment (example)
    os.environ["PIPELINE_PROJECT"] = project
    os.environ["PIPELINE_SEQUENCE"] = sequence
    os.environ["PIPELINE_SHOT"] = shot
    
    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">Shot loaded:</span> {project}/{sequence}/{shot}',
        pos='midCenter', fade=True
    )

def show_houdini_loader():
    """Show shot loader in Houdini."""
    import hou
    
    # Simple dialog
    result = hou.ui.readMultiInput(
        "Load Shot",
        ("Project", "Sequence", "Shot"),
        initial_contents=("MyProject", "SEQ010", "SH0010"),
        title="Shot Loader"
    )
    
    if result[0] == 0:  # OK pressed
        project, sequence, shot = result[1]
        os.environ["PIPELINE_PROJECT"] = project
        os.environ["PIPELINE_SEQUENCE"] = sequence
        os.environ["PIPELINE_SHOT"] = shot
        
        hou.ui.displayMessage(
            f"Shot loaded!\n\n"
            f"Project: {project}\n"
            f"Sequence: {sequence}\n"
            f"Shot: {shot}",
            title="Shot Loader"
        )

def show_nuke_loader():
    """Show shot loader in Nuke."""
    import nuke
    
    panel = nuke.Panel("Shot Loader")
    panel.addSingleLineInput("Project", "MyProject")
    panel.addSingleLineInput("Sequence", "SEQ010")
    panel.addSingleLineInput("Shot", "SH0010")
    
    if panel.show():
        project = panel.value("Project")
        sequence = panel.value("Sequence")
        shot = panel.value("Shot")
        
        os.environ["PIPELINE_PROJECT"] = project
        os.environ["PIPELINE_SEQUENCE"] = sequence
        os.environ["PIPELINE_SHOT"] = shot
        
        nuke.message(f"Shot loaded: {project}/{sequence}/{shot}")

def main():
    """Main entry point."""
    dcc = get_dcc()
    
    if dcc == "maya":
        show_maya_loader()
    elif dcc == "houdini":
        show_houdini_loader()
    elif dcc == "nuke":
        show_nuke_loader()
    else:
        print("Shot Loader - Standalone mode")
        print("Enter: project sequence shot")

if __name__ == "__main__":
    main()

