"""3ds Max V-Ray Setup - V-Ray render setup tools."""

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
        rt.messageBox("V-Ray Setup: V-Ray render setup tools ready", title="V-Ray Setup")
    else:
        print("V-Ray Setup: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
