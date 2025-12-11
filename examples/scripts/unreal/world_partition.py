"""Unreal World Partition - World partition manager."""

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
        unreal.log("World Partition: World partition manager ready")
    else:
        print("World Partition: This tool requires Unreal Engine")

if __name__ == "__main__":
    main()
