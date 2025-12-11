"""3ds Max Arnold Setup - Arnold render setup tools."""

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
        rt.messageBox("Arnold Setup: Arnold render setup tools ready", title="Arnold Setup")
    else:
        print("Arnold Setup: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
