# Maya Graph Editor Plus
# Enhanced graph editor utilities

import maya.cmds as cmds
import maya.mel as mel


def main():
    """Open graph editor plus window."""
    if cmds.window("graphEditorPlusWindow", exists=True):
        cmds.deleteUI("graphEditorPlusWindow")

    window = cmds.window("graphEditorPlusWindow", title="Graph Editor+", widthHeight=(280, 280))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.button(label="Open Graph Editor", command=lambda x: mel.eval('GraphEditor'), height=30)
    cmds.separator(height=10)

    cmds.frameLayout(label="Tangent Types", collapsable=False)
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(90, 90, 90))
    cmds.button(label="Auto", command=lambda x: set_tangent("auto"))
    cmds.button(label="Spline", command=lambda x: set_tangent("spline"))
    cmds.button(label="Linear", command=lambda x: set_tangent("linear"))
    cmds.setParent('..')
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(90, 90, 90))
    cmds.button(label="Flat", command=lambda x: set_tangent("flat"))
    cmds.button(label="Stepped", command=lambda x: set_tangent("step"))
    cmds.button(label="Plateau", command=lambda x: set_tangent("plateau"))
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.frameLayout(label="Curve Operations", collapsable=False)
    cmds.button(label="Flatten Curves", command=lambda x: flatten_curves())
    cmds.button(label="Snap Keys to Integer Frames", command=lambda x: snap_keys())
    cmds.button(label="Delete Static Channels", command=lambda x: delete_static())
    cmds.setParent('..')

    cmds.frameLayout(label="Key Operations", collapsable=False)
    cmds.button(label="Copy Keys", command=lambda x: mel.eval('timeSliderCopyKey'))
    cmds.button(label="Paste Keys", command=lambda x: mel.eval('timeSliderPasteKey false'))
    cmds.setParent('..')

    cmds.showWindow(window)

def set_tangent(tangent_type):
    """Set tangent type on selected keys."""
    cmds.keyTangent(inTangentType=tangent_type, outTangentType=tangent_type)
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">{tangent_type.title()}</span> tangents applied', pos='midCenter', fade=True)

def flatten_curves():
    """Flatten selected animation curves."""
    cmds.keyTangent(inTangentType="flat", outTangentType="flat")
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Curves flattened</span>', pos='midCenter', fade=True)

def snap_keys():
    """Snap keys to nearest integer frame."""
    cmds.snapKey(timeMultiple=1)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Keys snapped</span> to frames', pos='midCenter', fade=True)

def delete_static():
    """Delete static animation channels."""
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Please select animated objects")
        return
    cmds.delete(staticChannels=True)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Static channels deleted</span>', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()
