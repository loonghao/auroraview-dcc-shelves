"""Unreal Material Master - Material instance manager."""

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
        unreal.log("Material Master: Material instance manager ready")
    else:
        print("Material Master: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()

