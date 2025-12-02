"""Script to add icon path resolution functions to ui.py."""

from pathlib import Path

ui_path = Path("src/auroraview_dcc_shelves/ui.py")
content = ui_path.read_text(encoding="utf-8")

# New helper functions to add before _config_to_dict
new_functions = '''def _is_local_icon_path(icon: str) -> bool:
    """Check if an icon string is a local file path (not a Lucide icon name).

    Args:
        icon: The icon string to check.

    Returns:
        True if it's a local file path, False if it's an icon name.
    """
    if not icon:
        return False
    # Check for file extensions commonly used for icons
    extensions = [".svg", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp"]
    if any(icon.lower().endswith(ext) for ext in extensions):
        return True
    # Check for relative path indicators
    if icon.startswith("./") or icon.startswith("../") or icon.startswith("icons/"):
        return True
    # Check if it contains path separators
    return "/" in icon or "\\\\" in icon


def _resolve_icon_path(icon: str, base_path: Path | None) -> str:
    """Resolve icon path to absolute path if it is a local file.

    Args:
        icon: The icon string (could be Lucide name or local path).
        base_path: Base path of the config file for resolving relative paths.

    Returns:
        Resolved absolute path for local icons, or original icon name.
    """
    if not _is_local_icon_path(icon) or not base_path:
        return icon

    # Resolve relative path against config base path
    icon_path = Path(icon)
    if not icon_path.is_absolute():
        icon_path = (base_path / icon).resolve()

    # Return as normalized path string with forward slashes
    return str(icon_path).replace("\\\\", "/")


'''

# Check if functions already exist
if "_is_local_icon_path" not in content:
    # Insert the new functions before _config_to_dict
    old_func_def = 'def _config_to_dict(config: ShelvesConfig, current_host: str = "") -> dict[str, Any]:'
    content = content.replace(old_func_def, new_functions + old_func_def)
    ui_path.write_text(content, encoding="utf-8")
    print("Functions added successfully!")
else:
    print("Functions already exist, skipping.")

