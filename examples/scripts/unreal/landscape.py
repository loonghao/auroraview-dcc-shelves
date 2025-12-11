"""Unreal Landscape - Landscape editing tools."""

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
        unreal.log("Landscape: Landscape editing tools ready")
    else:
        print("Landscape: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
