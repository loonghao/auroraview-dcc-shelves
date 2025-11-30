"""3ds Max Spline Pro - Advanced spline tools."""

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
        rt.messageBox("Spline Pro: Advanced spline editing tools loaded", title="Spline Pro")
    else:
        print("Spline Pro: This tool requires 3ds Max")

if __name__ == "__main__":
    main()

