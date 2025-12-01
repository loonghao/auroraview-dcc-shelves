# Maya UV Master Tool
# Auto UV unwrapping utilities

import maya.cmds as cmds


def main():
    """Open UV Master window with quick actions."""
    selection = cmds.ls(selection=True, type='transform')

    if cmds.window("uvMasterWindow", exists=True):
        cmds.deleteUI("uvMasterWindow")

    window = cmds.window("uvMasterWindow", title="UV Master", widthHeight=(280, 200))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.frameLayout(label="Quick UV Actions", collapsable=False)
    cmds.button(label="Auto Unwrap (Automatic)", command=lambda x: auto_uv("automatic"))
    cmds.button(label="Planar Projection", command=lambda x: auto_uv("planar"))
    cmds.button(label="Cylindrical Projection", command=lambda x: auto_uv("cylindrical"))
    cmds.button(label="Spherical Projection", command=lambda x: auto_uv("spherical"))
    cmds.setParent('..')

    cmds.frameLayout(label="UV Tools", collapsable=False)
    cmds.button(label="Open UV Editor", command=lambda x: cmds.TextureViewWindow())
    cmds.button(label="Unfold UVs", command=lambda x: cmds.unfold())
    cmds.button(label="Layout UVs", command=lambda x: cmds.polyLayoutUV(scale=1))
    cmds.setParent('..')

    cmds.showWindow(window)

def auto_uv(method):
    """Apply UV projection method."""
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Please select a mesh")
        return

    if method == "automatic":
        cmds.polyAutoProjection(selection, lm=0, pb=0, ibd=1, cm=0, l=2, sc=1, o=1, p=6, ps=0.2, ws=0)
    elif method == "planar":
        cmds.polyPlanarProjection(selection)
    elif method == "cylindrical":
        cmds.polyCylindricalProjection(selection)
    elif method == "spherical":
        cmds.polySphericalProjection(selection)

    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">{method.title()} UV</span> applied',
        pos='midCenter',
        fade=True
    )

if __name__ == "__main__":
    main()
