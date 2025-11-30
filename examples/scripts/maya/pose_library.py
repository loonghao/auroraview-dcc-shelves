# Maya Pose Library
# Save and load animation poses

import maya.cmds as cmds
import json
import os

# Store poses in a temporary location
POSE_DIR = os.path.join(os.path.expanduser("~"), ".maya_poses")

def main():
    """Open pose library window."""
    if not os.path.exists(POSE_DIR):
        os.makedirs(POSE_DIR)
    
    if cmds.window("poseLibraryWindow", exists=True):
        cmds.deleteUI("poseLibraryWindow")
    
    window = cmds.window("poseLibraryWindow", title="Pose Library", widthHeight=(300, 300))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.frameLayout(label="Save Pose", collapsable=False)
    cmds.textFieldGrp("poseNameField", label="Pose Name:", text="pose_01")
    cmds.button(label="Save Current Pose", command=lambda x: save_pose())
    cmds.setParent('..')
    
    cmds.frameLayout(label="Load Pose", collapsable=True)
    cmds.textScrollList("poseList", numberOfRows=8, allowMultiSelection=False, height=120)
    cmds.button(label="Load Selected Pose", command=lambda x: load_pose())
    cmds.button(label="Delete Selected Pose", command=lambda x: delete_pose())
    cmds.button(label="Refresh List", command=lambda x: refresh_list())
    cmds.setParent('..')
    
    cmds.showWindow(window)
    refresh_list()

def save_pose():
    """Save current pose."""
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Select controls to save pose")
        return
    
    pose_name = cmds.textFieldGrp("poseNameField", q=True, text=True)
    if not pose_name:
        cmds.warning("Enter a pose name")
        return
    
    pose_data = {}
    for obj in selection:
        attrs = cmds.listAttr(obj, keyable=True) or []
        pose_data[obj] = {}
        for attr in attrs:
            try:
                value = cmds.getAttr(f"{obj}.{attr}")
                pose_data[obj][attr] = value
            except:
                pass
    
    pose_file = os.path.join(POSE_DIR, f"{pose_name}.json")
    with open(pose_file, 'w') as f:
        json.dump(pose_data, f, indent=2)
    
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Pose saved:</span> {pose_name}', pos='midCenter', fade=True)
    refresh_list()

def load_pose():
    """Load selected pose."""
    selected = cmds.textScrollList("poseList", q=True, selectItem=True)
    if not selected:
        cmds.warning("Select a pose to load")
        return
    
    pose_name = selected[0]
    pose_file = os.path.join(POSE_DIR, f"{pose_name}.json")
    
    if not os.path.exists(pose_file):
        cmds.warning("Pose file not found")
        return
    
    with open(pose_file, 'r') as f:
        pose_data = json.load(f)
    
    for obj, attrs in pose_data.items():
        if not cmds.objExists(obj):
            continue
        for attr, value in attrs.items():
            try:
                cmds.setAttr(f"{obj}.{attr}", value)
            except:
                pass
    
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Pose loaded:</span> {pose_name}', pos='midCenter', fade=True)

def delete_pose():
    """Delete selected pose."""
    selected = cmds.textScrollList("poseList", q=True, selectItem=True)
    if not selected:
        cmds.warning("Select a pose to delete")
        return
    
    pose_file = os.path.join(POSE_DIR, f"{selected[0]}.json")
    if os.path.exists(pose_file):
        os.remove(pose_file)
    refresh_list()
    cmds.inViewMessage(amg='<span style="color:#ff6666;">Pose deleted</span>', pos='midCenter', fade=True)

def refresh_list():
    """Refresh pose list."""
    cmds.textScrollList("poseList", e=True, removeAll=True)
    if os.path.exists(POSE_DIR):
        poses = [f[:-5] for f in os.listdir(POSE_DIR) if f.endswith('.json')]
        for pose in sorted(poses):
            cmds.textScrollList("poseList", e=True, append=pose)

if __name__ == "__main__":
    main()

