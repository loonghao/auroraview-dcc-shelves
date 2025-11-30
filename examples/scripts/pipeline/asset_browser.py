# Pipeline Asset Browser
# Browse and load pipeline assets (works in Maya, Houdini, Nuke)

import os
import sys

def get_dcc():
    """Detect current DCC application."""
    if "maya" in sys.executable.lower() or "maya" in str(sys.modules.keys()):
        try:
            import maya.cmds
            return "maya"
        except:
            pass
    if "houdini" in sys.executable.lower():
        try:
            import hou
            return "houdini"
        except:
            pass
    try:
        import nuke
        return "nuke"
    except:
        pass
    return "standalone"

def show_maya_browser():
    """Show asset browser in Maya."""
    import maya.cmds as cmds
    
    if cmds.window("assetBrowserWindow", exists=True):
        cmds.deleteUI("assetBrowserWindow")
    
    window = cmds.window("assetBrowserWindow", title="Asset Browser", widthHeight=(400, 300))
    cmds.columnLayout(adjustableColumn=True)
    
    cmds.text(label="Pipeline Asset Browser", font="boldLabelFont")
    cmds.separator(height=10)
    
    cmds.frameLayout(label="Asset Types")
    cmds.textScrollList("assetList", numberOfRows=10,
                        append=["Characters", "Props", "Environments", "Vehicles", "FX Elements"])
    cmds.setParent('..')
    
    cmds.button(label="Import Selected Asset", command=lambda x: cmds.inViewMessage(
        amg='<span style="color:#00ff00;">Asset import</span> - Connect to your pipeline API',
        pos='midCenter', fade=True
    ))
    
    cmds.showWindow(window)

def show_houdini_browser():
    """Show asset browser in Houdini."""
    import hou
    
    choices = ["Characters", "Props", "Environments", "Vehicles", "FX Elements"]
    result = hou.ui.selectFromList(
        choices,
        exclusive=True,
        title="Asset Browser",
        message="Select asset type to browse:"
    )
    
    if result:
        asset_type = choices[result[0]]
        hou.ui.displayMessage(
            f"Asset type: {asset_type}\n\n"
            "Connect this to your pipeline API to browse actual assets.",
            title="Asset Browser"
        )

def show_nuke_browser():
    """Show asset browser in Nuke."""
    import nuke
    
    panel = nuke.Panel("Asset Browser")
    panel.addEnumerationPulldown("Asset Type", "Characters Props Environments Vehicles FX_Elements")
    panel.addSingleLineInput("Search", "")
    
    if panel.show():
        asset_type = panel.value("Asset Type")
        search = panel.value("Search")
        nuke.message(
            f"Searching {asset_type}...\n"
            f"Query: {search or 'All'}\n\n"
            "Connect to your pipeline API for actual results."
        )

def main():
    """Main entry point."""
    dcc = get_dcc()
    
    if dcc == "maya":
        show_maya_browser()
    elif dcc == "houdini":
        show_houdini_browser()
    elif dcc == "nuke":
        show_nuke_browser()
    else:
        print("Asset Browser - Standalone mode")
        print("Run inside Maya, Houdini, or Nuke for full functionality")

if __name__ == "__main__":
    main()

