"""Unreal Texture Importer - Bulk texture import."""

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
        unreal.log("Texture Importer: Bulk texture import ready")
    else:
        print("Texture Importer: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
