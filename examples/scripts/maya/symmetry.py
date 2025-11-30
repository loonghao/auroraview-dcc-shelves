# Maya Symmetry Tool
# Symmetry modeling utilities

import maya.cmds as cmds
import maya.mel as mel

def main():
    """Open symmetry tool window."""
    if cmds.window("symmetryToolWindow", exists=True):
        cmds.deleteUI("symmetryToolWindow")
    
    window = cmds.window("symmetryToolWindow", title="Symmetry Tools", widthHeight=(250, 180))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.frameLayout(label="Symmetry Modeling", collapsable=False)
    cmds.button(label="Enable X Symmetry", command=lambda x: toggle_symmetry('x'))
    cmds.button(label="Enable Y Symmetry", command=lambda x: toggle_symmetry('y'))
    cmds.button(label="Enable Z Symmetry", command=lambda x: toggle_symmetry('z'))
    cmds.button(label="Disable Symmetry", command=lambda x: toggle_symmetry(None))
    cmds.setParent('..')
    
    cmds.frameLayout(label="Mirror Geometry", collapsable=False)
    cmds.button(label="Mirror X (Positive)", command=lambda x: mirror_geo('x', 1))
    cmds.button(label="Mirror X (Negative)", command=lambda x: mirror_geo('x', -1))
    cmds.setParent('..')
    
    cmds.showWindow(window)

def toggle_symmetry(axis):
    """Toggle symmetry for modeling."""
    if axis is None:
        cmds.symmetricModelling(e=True, symmetry=False)
        cmds.inViewMessage(amg='Symmetry <span style="color:#ff6666;">disabled</span>', pos='midCenter', fade=True)
    else:
        axis_map = {'x': 0, 'y': 1, 'z': 2}
        cmds.symmetricModelling(e=True, symmetry=True, axis=axis_map[axis])
        cmds.inViewMessage(amg=f'<span style="color:#00ff00;">{axis.upper()} Symmetry</span> enabled', pos='midCenter', fade=True)

def mirror_geo(axis, direction):
    """Mirror geometry."""
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Please select a mesh")
        return
    cmds.polyMirrorFace(selection, direction=direction, mergeMode=1, mirrorAxis=0 if axis == 'x' else (1 if axis == 'y' else 2))
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Mirrored</span> on {axis.upper()} axis', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()

