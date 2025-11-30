# Maya Boolean Pro Tool
# Advanced boolean operations with cleanup

import maya.cmds as cmds

def main():
    """Perform boolean operations with automatic cleanup."""
    selection = cmds.ls(selection=True, type='transform')
    
    if len(selection) != 2:
        cmds.warning("Please select exactly 2 mesh objects")
        return
    
    # Create UI window
    if cmds.window("booleanProWindow", exists=True):
        cmds.deleteUI("booleanProWindow")
    
    window = cmds.window("booleanProWindow", title="Boolean Pro", widthHeight=(250, 120))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.text(label=f"Object A: {selection[0]}")
    cmds.text(label=f"Object B: {selection[1]}")
    cmds.separator(height=10)
    
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(80, 80, 80))
    cmds.button(label="Union", command=lambda x: do_boolean(selection, 1))
    cmds.button(label="Difference", command=lambda x: do_boolean(selection, 2))
    cmds.button(label="Intersect", command=lambda x: do_boolean(selection, 3))
    cmds.setParent('..')
    
    cmds.showWindow(window)

def do_boolean(objects, operation):
    """Execute boolean and cleanup."""
    ops = {1: "union", 2: "difference", 3: "intersection"}
    result = cmds.polyCBoolOp(objects[0], objects[1], op=operation, ch=False)
    cmds.delete(result, constructionHistory=True)
    cmds.select(result)
    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">Boolean {ops[operation]}</span> complete',
        pos='midCenter',
        fade=True
    )

if __name__ == "__main__":
    main()

