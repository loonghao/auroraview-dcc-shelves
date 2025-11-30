"""3ds Max UVW Editor - UVW editing tools."""

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
        rt.messageBox("UVW Editor: UVW editing tools ready", title="UVW Editor")
    else:
        print("UVW Editor: This tool requires 3ds Max")

if __name__ == "__main__":
    main()

