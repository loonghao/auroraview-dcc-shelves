"""3ds Max CAT Rig - CAT rigging tools."""

def get_dcc():
    try:
        import pymxs
        return "3dsmax"
    except ImportError:
        return None

def main():
    dcc = get_dcc()
    if dcc == "3dsmax":
        from pymxs import runtime as rt
        rt.messageBox("CAT Rig: Character Animation Toolkit ready", title="CAT Rig")
    else:
        print("CAT Rig: This tool requires 3ds Max")

if __name__ == "__main__":
    main()

