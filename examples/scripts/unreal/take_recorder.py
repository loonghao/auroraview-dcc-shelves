"""Unreal Take Recorder - Take recording tools."""

def get_dcc():
    try:
        import unreal
        return "unreal"
    except ImportError:
        return None

def main():
    dcc = get_dcc()
    if dcc == "unreal":
        import unreal
        unreal.log("Take Recorder: Take recording tools ready")
    else:
        print("Take Recorder: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
