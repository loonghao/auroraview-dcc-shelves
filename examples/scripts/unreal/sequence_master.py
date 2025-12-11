"""Unreal Sequence Master - Sequence management tools."""

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
        unreal.log("Sequence Master: Sequence management tools ready")
    else:
        print("Sequence Master: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
