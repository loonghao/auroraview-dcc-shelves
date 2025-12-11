"""3ds Max Light Lister - Scene light lister."""

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
        rt.messageBox("Light Lister: Scene light lister ready", title="Light Lister")
    else:
        print("Light Lister: This tool requires 3ds Max")

if __name__ == "__main__":
    main()

