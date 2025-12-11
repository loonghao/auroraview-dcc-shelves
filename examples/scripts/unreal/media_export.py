"""Unreal Media Export - Media export tools."""

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
        unreal.log("Media Export: Media export tools ready")
    else:
        print("Media Export: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
