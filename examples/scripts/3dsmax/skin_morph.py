"""3ds Max Skin Morph - Skin morphing tools."""

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
        rt.messageBox("Skin Morph: Skin morphing tools ready", title="Skin Morph")
    else:
        print("Skin Morph: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
