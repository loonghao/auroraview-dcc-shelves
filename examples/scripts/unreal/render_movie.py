"""Unreal Render Movie - Render movie queue."""

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
        unreal.log("Render Movie: Render movie queue ready")
    else:
        print("Render Movie: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()

