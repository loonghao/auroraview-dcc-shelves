"""Unreal Engine Asset Import - Batch asset import tool.

Provides batch import functionality for FBX, textures, and other assets.
"""


def get_dcc():
    """Detect which DCC we're running in."""
    try:
        import unreal
        return "unreal"
    except ImportError:
        pass
    return None


def show_message(title, message):
    """Show a message dialog appropriate for the DCC."""
    dcc = get_dcc()
    if dcc == "unreal":
        import unreal
        unreal.log(f"{title}: {message}")
        # Show editor notification
        unreal.EditorDialog.show_message(
            title, message, unreal.AppMsgType.OK
        )
    else:
        print(f"{title}: {message}")


def main():
    """Main entry point."""
    dcc = get_dcc()
    
    if dcc == "unreal":
        import unreal
        
        # Get asset tools
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        
        # Show import dialog info
        msg = "Asset Import Tool\n\n"
        msg += "Supported formats:\n"
        msg += "- FBX (Static Mesh, Skeletal Mesh)\n"
        msg += "- PNG/TGA/EXR (Textures)\n"
        msg += "- WAV/OGG (Audio)\n"
        msg += "- ABC (Alembic Cache)\n\n"
        msg += "Use File > Import to start importing."
        
        show_message("Asset Import", msg)
    else:
        show_message("Asset Import", "This tool requires Unreal Engine")


if __name__ == "__main__":
    main()

