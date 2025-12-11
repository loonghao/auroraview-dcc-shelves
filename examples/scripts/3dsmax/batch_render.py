"""3ds Max Batch Render - Batch rendering tools."""

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
        rt.messageBox("Batch Render: Batch rendering tools ready", title="Batch Render")
    else:
        print("Batch Render: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
