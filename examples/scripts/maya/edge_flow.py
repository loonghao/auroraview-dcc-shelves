# Maya Edge Flow Tool
# Optimizes edge flow on selected edges

import maya.cmds as cmds

def main():
    """Optimize edge flow on selected edges."""
    selection = cmds.ls(selection=True, flatten=True)
    
    if not selection:
        cmds.warning("Please select edges to optimize")
        return
    
    # Filter to edges only
    edges = cmds.filterExpand(selection, sm=32)  # 32 = edges
    
    if not edges:
        cmds.warning("Please select edges")
        return
    
    # Apply edge flow
    cmds.polyEditEdgeFlow(adjustEdgeFlow=1)
    
    cmds.inViewMessage(
        amg=f'<span style="color:#00ff00;">Edge Flow</span> applied to {len(edges)} edges',
        pos='midCenter',
        fade=True
    )

if __name__ == "__main__":
    main()

