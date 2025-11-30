"""3ds Max Biped Setup - Biped rig setup tools."""

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
        rt.messageBox("Biped Setup: Biped rigging tools ready", title="Biped Setup")
    else:
        print("Biped Setup: This tool requires 3ds Max")

if __name__ == "__main__":
    main()

