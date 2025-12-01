# Pipeline Texture Manager
# Manage texture paths (works in Maya, Houdini, Nuke)

import os


def get_dcc():
    """Detect current DCC application."""
    try:
        return "maya"
    except:
        pass
    try:
        return "houdini"
    except:
        pass
    try:
        return "nuke"
    except:
        pass
    return "standalone"

def manage_maya():
    """Texture manager for Maya."""
    import maya.cmds as cmds

    # Find all file nodes
    file_nodes = cmds.ls(type='file')

    if not file_nodes:
        cmds.warning("No file textures found")
        return

    if cmds.window("texManagerWindow", exists=True):
        cmds.deleteUI("texManagerWindow")

    window = cmds.window("texManagerWindow", title="Texture Manager", widthHeight=(500, 300))
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label=f"Found {len(file_nodes)} texture nodes")
    cmds.separator(height=10)

    cmds.textScrollList("texList", numberOfRows=10)

    for node in file_nodes:
        tex_path = cmds.getAttr(f"{node}.fileTextureName")
        status = "✓" if os.path.exists(tex_path) else "✗"
        cmds.textScrollList("texList", e=True, append=f"{status} {node}: {os.path.basename(tex_path)}")

    cmds.separator(height=10)
    cmds.button(label="Repath Missing Textures", command=lambda x: repath_maya_textures())
    cmds.button(label="Copy Textures to Project", command=lambda x: cmds.inViewMessage(
        amg='<span style="color:#00ff00;">Copy</span> feature - implement with your pipeline',
        pos='midCenter', fade=True
    ))

    cmds.showWindow(window)

def repath_maya_textures():
    """Repath missing textures in Maya."""
    import maya.cmds as cmds

    result = cmds.fileDialog2(dialogStyle=2, fileMode=3, caption="Select Texture Folder")
    if not result:
        return

    new_folder = result[0]
    file_nodes = cmds.ls(type='file')
    fixed = 0

    for node in file_nodes:
        tex_path = cmds.getAttr(f"{node}.fileTextureName")
        if not os.path.exists(tex_path):
            filename = os.path.basename(tex_path)
            new_path = os.path.join(new_folder, filename)
            if os.path.exists(new_path):
                cmds.setAttr(f"{node}.fileTextureName", new_path, type="string")
                fixed += 1

    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">Fixed</span> {fixed} texture paths',
        pos='midCenter', fade=True
    )

def manage_houdini():
    """Texture manager for Houdini."""
    import hou

    # Find all file references
    refs = hou.fileReferences()
    tex_refs = [(node, parm, path) for node, parm, path in refs
                if any(ext in str(path).lower() for ext in ['.jpg', '.png', '.exr', '.tif', '.tex'])]

    if not tex_refs:
        hou.ui.displayMessage("No texture references found", title="Texture Manager")
        return

    info = f"Found {len(tex_refs)} texture references:\n\n"
    missing = 0

    for node, parm, path in tex_refs[:20]:  # Show first 20
        exists = os.path.exists(str(path))
        status = "✓" if exists else "✗ MISSING"
        if not exists:
            missing += 1
        info += f"{status}: {os.path.basename(str(path))}\n"

    if len(tex_refs) > 20:
        info += f"\n... and {len(tex_refs) - 20} more"

    info += f"\n\nMissing: {missing}"

    hou.ui.displayMessage(info, title="Texture Manager")

def manage_nuke():
    """Texture manager for Nuke."""
    import nuke

    read_nodes = nuke.allNodes("Read")

    if not read_nodes:
        nuke.message("No Read nodes found")
        return

    info = f"Found {len(read_nodes)} Read nodes:\n\n"
    missing = 0

    for node in read_nodes:
        path = node['file'].getValue()
        # Check first frame
        first_frame = int(node['first'].getValue())
        check_path = path.replace('%04d', str(first_frame).zfill(4))

        exists = os.path.exists(check_path)
        status = "✓" if exists else "✗ MISSING"
        if not exists:
            missing += 1
        info += f"{status}: {node.name()} - {os.path.basename(path)}\n"

    info += f"\nMissing: {missing}"
    nuke.message(info)

def main():
    """Main entry point."""
    dcc = get_dcc()

    if dcc == "maya":
        manage_maya()
    elif dcc == "houdini":
        manage_houdini()
    elif dcc == "nuke":
        manage_nuke()
    else:
        print("Texture Manager - Run inside DCC application")

if __name__ == "__main__":
    main()
