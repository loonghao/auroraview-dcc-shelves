"""Unreal Light Bake - Light baking tools."""

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
        unreal.log("Light Bake: Light baking tools ready")
    else:
        print("Light Bake: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()

