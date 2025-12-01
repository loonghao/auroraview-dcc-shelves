# Maya Auto Rig Tool
# Quick biped skeleton creation

import maya.cmds as cmds


def main():
    """Create a basic biped skeleton."""
    if cmds.window("autoRigWindow", exists=True):
        cmds.deleteUI("autoRigWindow")

    window = cmds.window("autoRigWindow", title="Auto Rig", widthHeight=(280, 200))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    cmds.text(label="Quick Skeleton Generator")
    cmds.separator(height=10)

    cmds.floatSliderGrp("heightSlider", label="Height:", field=True, minValue=100, maxValue=250, value=170)
    cmds.separator(height=10)

    cmds.button(label="Create Biped Skeleton", command=lambda x: create_biped())
    cmds.button(label="Create Quadruped Skeleton", command=lambda x: create_quadruped())
    cmds.separator(height=10)
    cmds.button(label="Mirror Joints (L to R)", command=lambda x: mirror_joints())

    cmds.showWindow(window)

def create_biped():
    """Create biped skeleton."""
    height = cmds.floatSliderGrp("heightSlider", q=True, value=True)
    scale = height / 170.0

    # Create spine
    cmds.select(clear=True)
    root = cmds.joint(name="root_jnt", p=(0, 100*scale, 0))
    spine1 = cmds.joint(name="spine_01_jnt", p=(0, 110*scale, 0))
    spine2 = cmds.joint(name="spine_02_jnt", p=(0, 125*scale, 0))
    chest = cmds.joint(name="chest_jnt", p=(0, 140*scale, 0))
    neck = cmds.joint(name="neck_jnt", p=(0, 155*scale, 0))
    head = cmds.joint(name="head_jnt", p=(0, 165*scale, 0))
    head_end = cmds.joint(name="head_end_jnt", p=(0, height*scale, 0))

    # Left arm
    cmds.select(chest)
    l_clavicle = cmds.joint(name="L_clavicle_jnt", p=(5*scale, 150*scale, 0))
    l_shoulder = cmds.joint(name="L_shoulder_jnt", p=(18*scale, 148*scale, 0))
    l_elbow = cmds.joint(name="L_elbow_jnt", p=(40*scale, 148*scale, -2*scale))
    l_wrist = cmds.joint(name="L_wrist_jnt", p=(60*scale, 148*scale, 0))

    # Left leg
    cmds.select(root)
    l_hip = cmds.joint(name="L_hip_jnt", p=(10*scale, 95*scale, 0))
    l_knee = cmds.joint(name="L_knee_jnt", p=(10*scale, 52*scale, 2*scale))
    l_ankle = cmds.joint(name="L_ankle_jnt", p=(10*scale, 8*scale, 0))
    l_ball = cmds.joint(name="L_ball_jnt", p=(10*scale, 0, 8*scale))
    l_toe = cmds.joint(name="L_toe_jnt", p=(10*scale, 0, 15*scale))

    cmds.select(root)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Biped Skeleton</span> created - Mirror to complete', pos='midCenter', fade=True)

def create_quadruped():
    """Create simple quadruped skeleton."""
    cmds.select(clear=True)
    root = cmds.joint(name="root_jnt", p=(0, 80, 0))
    cmds.joint(name="spine_01_jnt", p=(0, 82, -20))
    cmds.joint(name="spine_02_jnt", p=(0, 85, -40))
    cmds.joint(name="chest_jnt", p=(0, 88, -60))
    cmds.joint(name="neck_jnt", p=(0, 95, -75))
    cmds.joint(name="head_jnt", p=(0, 100, -90))

    cmds.select(root)
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Quadruped Skeleton</span> created', pos='midCenter', fade=True)

def mirror_joints():
    """Mirror joints from left to right."""
    cmds.mirrorJoint("L_clavicle_jnt", mirrorYZ=True, mirrorBehavior=True, searchReplace=("L_", "R_"))
    cmds.mirrorJoint("L_hip_jnt", mirrorYZ=True, mirrorBehavior=True, searchReplace=("L_", "R_"))
    cmds.inViewMessage(amg='<span style="color:#00ff00;">Joints Mirrored</span> L -> R', pos='midCenter', fade=True)

if __name__ == "__main__":
    main()
