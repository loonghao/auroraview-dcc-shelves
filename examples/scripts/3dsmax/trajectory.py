"""3ds Max Trajectory - Trajectory editor."""

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
        rt.messageBox("Trajectory: Trajectory editor ready", title="Trajectory")
    else:
        print("Trajectory: This tool requires 3ds Max")

if __name__ == "__main__":
    main()

