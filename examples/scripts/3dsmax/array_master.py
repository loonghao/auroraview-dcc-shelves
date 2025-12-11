"""3ds Max Array Master - Advanced array tools."""

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
        rt.messageBox("Array Master: Advanced array tools ready", title="Array Master")
    else:
        print("Array Master: This tool requires 3ds Max")

if __name__ == "__main__":
    main()
