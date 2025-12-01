# Maya Skin Weights Tool
# Skin weight painting utilities

import maya.cmds as cmds
import maya.mel as mel


def main():
    """Open skin weights tool window."""
    if cmds.window("skinWeightsWindow", exists=True):
        cmds.deleteUI("skinWeightsWindow")

    window = cmds.window("skinWeightsWindow", title="Skin Weights", widthHeight=(280, 250))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.frameLayout(label="Paint Weights", collapsable=False)
    cmds.button(label="Enter Paint Weights Tool", command=lambda x: enter_paint_weights())
    cmds.button(label="Smooth Weights", command=lambda x: smooth_weights())
    cmds.button(label="Prune Small Weights", command=lambda x: prune_weights())
    cmds.setParent('..')

    cmds.frameLayout(label="Weight Transfer", collapsable=False)
    cmds.button(label="Copy Skin Weights", command=lambda x: copy_weights())
    cmds.button(label="Mirror Skin Weights", command=lambda x: mirror_weights())
    cmds.setParent('..')

    cmds.frameLayout(label="Binding", collapsable=False)
    cmds.button(label="Bind Skin (Smooth)", command=lambda x: bind_skin("smooth"))
    cmds.button(label="Bind Skin (Rigid)", command=lambda x: bind_skin("rigid"))
    cmds.button(label="Unbind Skin", command=lambda x: unbind_skin())
    cmds.setParent('..')

    cmds.showWindow(window)

def enter_paint_weights():
    """Enter paint skin weights tool."""
    mel.eval('ArtPaintSkinWeightsTool')
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Paint Weights</span> mode active', pos='midCenter', fade=True)

def smooth_weights():
    """Smooth skin weights on selection."""
    mel.eval('SmoothSkinWeights')
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Weights smoothed</span>', pos='midCenter', fade=True)

def prune_weights():
    """Prune small skin weights."""
    cmds.skinPercent(pruneWeights=0.01)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Small weights pruned</span>', pos='midCenter', fade=True)

def copy_weights():
    """Copy skin weights between meshes."""
    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        cmds.warning("Select source mesh then target mesh")
        return
    cmds.copySkinWeights(noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint")
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Weights copied</span>', pos='midCenter', fade=True)

def mirror_weights():
    """Mirror skin weights."""
    cmds.copySkinWeights(mirrorMode='YZ', mirrorInverse=True, surfaceAssociation="closestPoint")
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Weights mirrored</span>', pos='midCenter', fade=True)

def bind_skin(method):
    """Bind skin to skeleton."""
    selection = cmds.ls(selection=True)
    if len(selection) < 2:
        cmds.warning("Select mesh(es) and root joint")
        return
    if method == "smooth":
        cmds.skinCluster(toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)
    else:
        cmds.skinCluster(toSelectedBones=True, bindMethod=1, skinMethod=0, normalizeWeights=1)
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">{method.title()} bind</span> complete', pos='midCenter', fade=True)

def unbind_skin():
    """Unbind skin."""
    mel.eval('DetachSkin')
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Skin unbound</span>', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()
