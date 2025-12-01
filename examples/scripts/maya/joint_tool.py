# Maya Joint Tool
# Advanced joint creation utilities

import maya.cmds as cmds
import maya.mel as mel


def main():
    """Open joint tool window."""
    if cmds.window("jointToolWindow", exists=True):
        cmds.deleteUI("jointToolWindow")

    window = cmds.window("jointToolWindow", title="Joint Tools", widthHeight=(280, 220))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.frameLayout(label="Joint Creation", collapsable=False)
    cmds.button(label="Enter Joint Tool", command=lambda x: mel.eval('JointTool'))
    cmds.button(label="Insert Joint", command=lambda x: insert_joint())
    cmds.setParent('..')

    cmds.frameLayout(label="Joint Orientation", collapsable=False)
    cmds.button(label="Orient Joints (XYZ)", command=lambda x: orient_joints('xyz'))
    cmds.button(label="Orient Joints (XZY)", command=lambda x: orient_joints('xzy'))
    cmds.button(label="Zero Joint Orient", command=lambda x: zero_orient())
    cmds.setParent('..')

    cmds.frameLayout(label="Joint Display", collapsable=False)
    cmds.button(label="Show Local Axes", command=lambda x: toggle_axes(True))
    cmds.button(label="Hide Local Axes", command=lambda x: toggle_axes(False))
    cmds.setParent('..')

    cmds.showWindow(window)

def insert_joint():
    """Insert joint between selected joints."""
    selection = cmds.ls(selection=True, type='joint')
    if len(selection) != 2:
        cmds.warning("Please select 2 joints")
        return
    mel.eval('InsertJointTool')
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Insert Joint</span> - click between joints', pos='midCenter', fade=True)

def orient_joints(order):
    """Orient selected joints."""
    selection = cmds.ls(selection=True, type='joint')
    if not selection:
        cmds.warning("Please select joints")
        return
    for joint in selection:
        cmds.joint(joint, e=True, orientJoint=order, secondaryAxisOrient='yup', zeroScaleOrient=True)
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Joints oriented</span> ({order.upper()})', pos='midCenter', fade=True)

def zero_orient():
    """Zero out joint orientation."""
    selection = cmds.ls(selection=True, type='joint')
    if not selection:
        cmds.warning("Please select joints")
        return
    for joint in selection:
        cmds.setAttr(f"{joint}.jointOrientX", 0)
        cmds.setAttr(f"{joint}.jointOrientY", 0)
        cmds.setAttr(f"{joint}.jointOrientZ", 0)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Joint orient zeroed</span>', pos='midCenter', fade=True)

def toggle_axes(show):
    """Toggle local rotation axes display."""
    selection = cmds.ls(selection=True, type='joint')
    if not selection:
        cmds.warning("Please select joints")
        return
    for joint in selection:
        cmds.setAttr(f"{joint}.displayLocalAxis", show)
    status = "shown" if show else "hidden"
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Local axes {status}</span>', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()
