# Maya Blend Shapes Tool
# Blend shape creation and management

import maya.cmds as cmds

def main():
    """Open blend shapes tool window."""
    if cmds.window("blendShapesWindow", exists=True):
        cmds.deleteUI("blendShapesWindow")
    
    window = cmds.window("blendShapesWindow", title="Blend Shapes", widthHeight=(300, 220))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    
    cmds.frameLayout(label="Create Blend Shape", collapsable=False)
    cmds.text(label="Select targets then base mesh", align='left')
    cmds.button(label="Create Blend Shape Node", command=lambda x: create_blendshape())
    cmds.button(label="Add Target to Existing", command=lambda x: add_target())
    cmds.setParent('..')
    
    cmds.frameLayout(label="Blend Shape Tools", collapsable=False)
    cmds.button(label="Open Blend Shape Editor", command=lambda x: open_editor())
    cmds.button(label="Bake to New Mesh", command=lambda x: bake_blendshape())
    cmds.button(label="Extract Target", command=lambda x: extract_target())
    cmds.setParent('..')
    
    cmds.showWindow(window)

def create_blendshape():
    """Create blend shape from selection."""
    selection = cmds.ls(selection=True, type='transform')
    if len(selection) < 2:
        cmds.warning("Select target shapes then base mesh (last)")
        return
    
    targets = selection[:-1]
    base = selection[-1]
    
    bs_node = cmds.blendShape(targets, base, name=f"{base}_blendShape")[0]
    cmds.select(base)
    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">Blend Shape</span> created with {len(targets)} targets',
        pos='midCenter', fade=True
    )

def add_target():
    """Add target to existing blend shape."""
    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        cmds.warning("Select new target then base mesh with blend shape")
        return
    
    new_target = selection[0]
    base = selection[1]
    
    # Find blend shape node
    history = cmds.listHistory(base) or []
    bs_nodes = cmds.ls(history, type='blendShape')
    
    if not bs_nodes:
        cmds.warning("No blend shape found on base mesh")
        return
    
    bs_node = bs_nodes[0]
    
    # Get next available index
    existing = cmds.blendShape(bs_node, q=True, target=True) or []
    next_index = len(existing)
    
    cmds.blendShape(bs_node, edit=True, target=(base, next_index, new_target, 1.0))
    cmds.inViewMessage(amg=f'<span style="color:#00ff00;">Target added</span> to {bs_node}', pos='midCenter', fade=True)

def open_editor():
    """Open blend shape editor."""
    from maya import mel
    mel.eval('ShapeEditor')

def bake_blendshape():
    """Bake current blend shape state to new mesh."""
    selection = cmds.ls(selection=True, type='transform')
    if not selection:
        cmds.warning("Select mesh with blend shape")
        return
    
    duplicate = cmds.duplicate(selection[0], name=f"{selection[0]}_baked")[0]
    cmds.delete(duplicate, constructionHistory=True)
    cmds.select(duplicate)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Baked</span> to new mesh', pos='midCenter', fade=True)

def extract_target():
    """Extract blend shape target as separate mesh."""
    selection = cmds.ls(selection=True, type='transform')
    if not selection:
        cmds.warning("Select mesh with blend shape")
        return
    
    # Duplicate and delete history
    extracted = cmds.duplicate(selection[0], name=f"{selection[0]}_extracted")[0]
    cmds.delete(extracted, constructionHistory=True)
    cmds.select(extracted)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Target extracted</span>', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()

