"""Unreal MoCap Import - Motion capture import."""

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
        unreal.log("MoCap Import: Motion capture import ready")
    else:
        print("MoCap Import: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
