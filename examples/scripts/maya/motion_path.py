# Maya Motion Path Tool
# Attach objects to motion paths

import maya.cmds as cmds

def main():
    """Open motion path tool window."""
    if cmds.window("motionPathWindow", exists=True):
        cmds.deleteUI("motionPathWindow")
    
    window = cmds.window("motionPathWindow", title="Motion Path", widthHeight=(280, 200))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.text(label="Select object(s) then curve", align='left')
    cmds.separator(height=5)
    
    cmds.frameLayout(label="Attach to Path", collapsable=False)
    cmds.checkBoxGrp("followCheck", label="Follow:", value1=True)
    cmds.checkBoxGrp("bankCheck", label="Bank:", value1=False)
    cmds.floatSliderGrp("startFrame", label="Start Frame:", field=True, minValue=1, maxValue=200, value=1)
    cmds.floatSliderGrp("endFrame", label="End Frame:", field=True, minValue=1, maxValue=200, value=100)
    cmds.button(label="Attach to Motion Path", command=lambda x: attach_to_path())
    cmds.setParent('..')
    
    cmds.frameLayout(label="Tools", collapsable=False)
    cmds.button(label="Create Curve from Animation", command=lambda x: curve_from_anim())
    cmds.setParent('..')
    
    cmds.showWindow(window)

def attach_to_path():
    """Attach selected objects to curve."""
    selection = cmds.ls(selection=True)
    if len(selection) < 2:
        cmds.warning("Select object(s) then curve")
        return
    
    curve = selection[-1]
    objects = selection[:-1]
    
    # Check if last selection is a curve
    shapes = cmds.listRelatives(curve, shapes=True) or []
    is_curve = any(cmds.nodeType(s) == 'nurbsCurve' for s in shapes)
    
    if not is_curve:
        cmds.warning("Last selected must be a NURBS curve")
        return
    
    follow = cmds.checkBoxGrp("followCheck", q=True, value1=True)
    bank = cmds.checkBoxGrp("bankCheck", q=True, value1=True)
    start = cmds.floatSliderGrp("startFrame", q=True, value=True)
    end = cmds.floatSliderGrp("endFrame", q=True, value=True)
    
    for obj in objects:
        motion_path = cmds.pathAnimation(
            obj, curve,
            follow=follow,
            bank=bank,
            startTimeU=start,
            endTimeU=end,
            fractionMode=True
        )
    
    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">{len(objects)} object(s)</span> attached to path',
        pos='midCenter', fade=True
    )

def curve_from_anim():
    """Create curve from object animation."""
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Select animated object")
        return
    
    obj = selection[0]
    start = int(cmds.playbackOptions(q=True, minTime=True))
    end = int(cmds.playbackOptions(q=True, maxTime=True))
    
    points = []
    for frame in range(start, end + 1, 5):  # Sample every 5 frames
        cmds.currentTime(frame)
        pos = cmds.xform(obj, q=True, worldSpace=True, translation=True)
        points.append(pos)
    
    if len(points) < 2:
        cmds.warning("Not enough points")
        return
    
    curve = cmds.curve(name=f"{obj}_path", d=3, p=points)
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Path curve</span> created', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()

