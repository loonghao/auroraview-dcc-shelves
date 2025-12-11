"""Unreal Collision Setup - Collision mesh setup."""

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
        unreal.log("Collision Setup: Collision mesh setup ready")
    else:
        print("Collision Setup: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
