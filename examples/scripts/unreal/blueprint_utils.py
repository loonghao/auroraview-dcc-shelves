"""Unreal Blueprint Utils - Blueprint utilities."""

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
        unreal.log("Blueprint Utils: Blueprint utilities ready")
    else:
        print("Blueprint Utils: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
