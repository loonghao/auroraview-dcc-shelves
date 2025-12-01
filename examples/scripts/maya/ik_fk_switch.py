# Maya IK/FK Switch Tool
# IK/FK creation and switching utilities

import maya.cmds as cmds


def main():
    """Open IK/FK tool window."""
    if cmds.window("ikfkWindow", exists=True):
        cmds.deleteUI("ikfkWindow")

    window = cmds.window("ikfkWindow", title="IK/FK Tools", widthHeight=(280, 200))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.frameLayout(label="Create IK Handle", collapsable=False)
    cmds.button(label="IK Rotate Plane (RP)", command=lambda x: create_ik("ikRPsolver"))
    cmds.button(label="IK Single Chain (SC)", command=lambda x: create_ik("ikSCsolver"))
    cmds.button(label="IK Spline", command=lambda x: create_spline_ik())
    cmds.setParent('..')

    cmds.frameLayout(label="IK Handle Options", collapsable=False)
    cmds.button(label="Create Pole Vector", command=lambda x: create_pole_vector())
    cmds.button(label="Set Preferred Angle", command=lambda x: set_preferred_angle())
    cmds.setParent('..')

    cmds.showWindow(window)

def create_ik(solver):
    """Create IK handle with specified solver."""
    selection = cmds.ls(selection=True, type='joint')
    if len(selection) != 2:
        cmds.warning("Select start joint and end joint")
        return

    ik_handle = cmds.ikHandle(startJoint=selection[0], endEffector=selection[1], solver=solver)
    cmds.select(ik_handle[0])
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">IK Handle</span> created ({solver})', pos='midCenter', fade=True)

def create_spline_ik():
    """Create spline IK."""
    selection = cmds.ls(selection=True, type='joint')
    if len(selection) != 2:
        cmds.warning("Select start joint and end joint")
        return

    ik_result = cmds.ikHandle(startJoint=selection[0], endEffector=selection[1], solver="ikSplineSolver", createCurve=True)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Spline IK</span> created with curve', pos='midCenter', fade=True)

def create_pole_vector():
    """Create pole vector constraint for selected IK handle."""
    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        cmds.warning("Select locator/control then IK handle")
        return

    cmds.poleVectorConstraint(selection[0], selection[1])
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Pole Vector</span> constraint created', pos='midCenter', fade=True)

def set_preferred_angle():
    """Set preferred angle on selected joints."""
    selection = cmds.ls(selection=True, type='joint')
    if not selection:
        cmds.warning("Select joints")
        return

    for joint in selection:
        cmds.joint(joint, e=True, setPreferredAngles=True)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Preferred angle</span> set', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()
