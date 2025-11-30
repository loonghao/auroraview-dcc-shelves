# Maya Control Curves Library
# Pre-made control curves for rigging

import maya.cmds as cmds

def main():
    """Open control curves library window."""
    if cmds.window("ctrlCurvesWindow", exists=True):
        cmds.deleteUI("ctrlCurvesWindow")
    
    window = cmds.window("ctrlCurvesWindow", title="Control Curves", widthHeight=(280, 280))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.frameLayout(label="Basic Shapes", collapsable=False)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(90, 90, 90))
    cmds.button(label="Circle", command=lambda x: create_ctrl("circle"))
    cmds.button(label="Square", command=lambda x: create_ctrl("square"))
    cmds.button(label="Triangle", command=lambda x: create_ctrl("triangle"))
    cmds.setParent('..')
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(90, 90, 90))
    cmds.button(label="Diamond", command=lambda x: create_ctrl("diamond"))
    cmds.button(label="Cross", command=lambda x: create_ctrl("cross"))
    cmds.button(label="Star", command=lambda x: create_ctrl("star"))
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.frameLayout(label="3D Shapes", collapsable=False)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(90, 90, 90))
    cmds.button(label="Cube", command=lambda x: create_ctrl("cube"))
    cmds.button(label="Sphere", command=lambda x: create_ctrl("sphere"))
    cmds.button(label="Arrow", command=lambda x: create_ctrl("arrow"))
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.frameLayout(label="Rig Controls", collapsable=False)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(135, 135))
    cmds.button(label="COG Control", command=lambda x: create_ctrl("cog"))
    cmds.button(label="Foot Control", command=lambda x: create_ctrl("foot"))
    cmds.setParent('..')
    cmds.setParent('..')
    
    cmds.showWindow(window)

def create_ctrl(shape):
    """Create control curve of specified shape."""
    ctrl = None
    
    if shape == "circle":
        ctrl = cmds.circle(name="circle_ctrl", normal=(0, 1, 0), radius=1)[0]
    elif shape == "square":
        ctrl = cmds.curve(name="square_ctrl", d=1, p=[(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1)])
    elif shape == "triangle":
        ctrl = cmds.curve(name="triangle_ctrl", d=1, p=[(0, 0, 1), (1, 0, -1), (-1, 0, -1), (0, 0, 1)])
    elif shape == "diamond":
        ctrl = cmds.curve(name="diamond_ctrl", d=1, p=[(0, 0, 1), (1, 0, 0), (0, 0, -1), (-1, 0, 0), (0, 0, 1)])
    elif shape == "cross":
        ctrl = cmds.curve(name="cross_ctrl", d=1, p=[(-0.5, 0, -1), (-0.5, 0, -0.5), (-1, 0, -0.5), (-1, 0, 0.5), (-0.5, 0, 0.5), (-0.5, 0, 1), (0.5, 0, 1), (0.5, 0, 0.5), (1, 0, 0.5), (1, 0, -0.5), (0.5, 0, -0.5), (0.5, 0, -1), (-0.5, 0, -1)])
    elif shape == "star":
        ctrl = cmds.curve(name="star_ctrl", d=1, p=[(0, 0, 1), (0.2, 0, 0.3), (1, 0, 0.3), (0.4, 0, -0.1), (0.6, 0, -1), (0, 0, -0.4), (-0.6, 0, -1), (-0.4, 0, -0.1), (-1, 0, 0.3), (-0.2, 0, 0.3), (0, 0, 1)])
    elif shape == "cube":
        ctrl = cmds.curve(name="cube_ctrl", d=1, p=[(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)])
    elif shape == "sphere":
        circles = []
        for axis in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]:
            c = cmds.circle(normal=axis, radius=1)[0]
            circles.append(c)
        ctrl = circles[0]
        for c in circles[1:]:
            shape_node = cmds.listRelatives(c, shapes=True)[0]
            cmds.parent(shape_node, ctrl, relative=True, shape=True)
            cmds.delete(c)
        ctrl = cmds.rename(ctrl, "sphere_ctrl")
    elif shape == "arrow":
        ctrl = cmds.curve(name="arrow_ctrl", d=1, p=[(0, 0, 2), (1, 0, 0), (0.5, 0, 0), (0.5, 0, -2), (-0.5, 0, -2), (-0.5, 0, 0), (-1, 0, 0), (0, 0, 2)])
    elif shape == "cog":
        ctrl = cmds.circle(name="COG_ctrl", normal=(0, 1, 0), radius=2)[0]
        cmds.addAttr(ctrl, ln="CONTROLS", at="enum", en="--------:")
        cmds.setAttr(f"{ctrl}.CONTROLS", e=True, channelBox=True)
    elif shape == "foot":
        ctrl = cmds.curve(name="foot_ctrl", d=1, p=[(-1, 0, -2), (-1, 0, 1), (-0.5, 0, 2), (0.5, 0, 2), (1, 0, 1), (1, 0, -2), (-1, 0, -2)])
    
    if ctrl:
        cmds.select(ctrl)
        cmds.inViewMessage(amg=f'<span style="color:#00ff00;">{shape.title()}</span> control created', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()

