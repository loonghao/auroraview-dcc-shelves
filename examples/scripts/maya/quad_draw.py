# Maya Quad Draw Tool
# Activates the Quad Draw retopology tool

import maya.cmds as cmds
import maya.mel as mel

def main():
    """Activate Quad Draw tool for retopology."""
    # Enter Modeling Toolkit Quad Draw mode
    mel.eval('dR_quadDrawTool')
    cmds.inViewMessage(
        amg='<span style="color:#00ff00;">Quad Draw</span> activated - Click to place vertices',
        pos='midCenter',
        fade=True
    )

if __name__ == "__main__":
    main()

