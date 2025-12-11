"""Unreal Foliage Pro - Foliage painting tools."""

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
        unreal.log("Foliage Pro: Foliage painting tools ready")
    else:
        print("Foliage Pro: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
