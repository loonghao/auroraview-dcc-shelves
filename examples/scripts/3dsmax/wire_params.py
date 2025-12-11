"""3ds Max Wire Params - Wire parameters tools."""

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
        rt.messageBox("Wire Params: Wire parameters tools ready", title="Wire Params")
    else:
        print("Wire Params: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
