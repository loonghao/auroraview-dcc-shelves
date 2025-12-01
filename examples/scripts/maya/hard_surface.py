# Maya Hard Surface Kit
# Hard surface modeling utilities

import maya.cmds as cmds


def main():
    """Open hard surface toolkit window."""
    if cmds.window("hardSurfaceWindow", exists=True):
        cmds.deleteUI("hardSurfaceWindow")

    window = cmds.window("hardSurfaceWindow", title="Hard Surface Kit", widthHeight=(280, 250))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.frameLayout(label="Edge Operations", collapsable=False)
    cmds.button(label="Bevel Selected Edges", command=lambda x: bevel_edges())
    cmds.button(label="Crease Selected Edges", command=lambda x: crease_edges(1.0))
    cmds.button(label="Remove Crease", command=lambda x: crease_edges(0.0))
    cmds.setParent('..')

    cmds.frameLayout(label="Face Operations", collapsable=False)
    cmds.button(label="Extrude Faces", command=lambda x: extrude_faces())
    cmds.button(label="Inset Faces", command=lambda x: inset_faces())
    cmds.setParent('..')

    cmds.frameLayout(label="Subdivision", collapsable=False)
    cmds.button(label="Smooth Preview (1)", command=lambda x: set_subdiv(1))
    cmds.button(label="Smooth Preview (2)", command=lambda x: set_subdiv(2))
    cmds.button(label="No Smooth Preview", command=lambda x: set_subdiv(0))
    cmds.setParent('..')

    cmds.showWindow(window)

def bevel_edges():
    """Bevel selected edges."""
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Please select edges")
        return
    cmds.polyBevel3(offset=0.1, segments=2, depth=1, mitering=0, miteringAngle=180, chamfer=False)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Bevel</span> applied', pos='midCenter', fade=True)

def crease_edges(value):
    """Set crease on selected edges."""
    selection = cmds.ls(selection=True, flatten=True)
    if not selection:
        cmds.warning("Please select edges")
        return
    cmds.polyCrease(value=value)
    msg = "Crease applied" if value > 0 else "Crease removed"
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">{msg}</span>', pos='midCenter', fade=True)

def extrude_faces():
    """Extrude selected faces."""
    cmds.polyExtrudeFacet(localTranslateZ=0.2)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Extrude</span> - drag to adjust', pos='midCenter', fade=True)

def inset_faces():
    """Inset selected faces."""
    cmds.polyExtrudeFacet(offset=0.1, localTranslateZ=0)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Inset</span> applied', pos='midCenter', fade=True)

def set_subdiv(level):
    """Set subdivision preview level."""
    selection = cmds.ls(selection=True, type='transform')
    if not selection:
        cmds.warning("Please select a mesh")
        return
    for obj in selection:
        shapes = cmds.listRelatives(obj, shapes=True) or []
        for shape in shapes:
            cmds.setAttr(f"{shape}.displaySmoothMesh", level)
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Subdiv Level {level}</span>', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()
