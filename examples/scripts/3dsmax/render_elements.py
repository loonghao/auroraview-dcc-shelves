"""3ds Max Render Elements - Render element manager."""

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
        rt.messageBox("Render Elements: Render element manager ready", title="Render Elements")
    else:
        print("Render Elements: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
