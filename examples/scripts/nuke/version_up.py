# Nuke Version Up Tool
# Quick version up script

import nuke
import os
import re

def main():
    """Version up current script."""
    script_path = nuke.root().name()
    
    if not script_path or script_path == "Root":
        nuke.message("Please save the script first")
        return
    
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)
    name_no_ext = os.path.splitext(script_name)[0]
    ext = os.path.splitext(script_name)[1]
    
    # Find version pattern
    version_pattern = r'_v(\d+)$'
    match = re.search(version_pattern, name_no_ext)
    
    if match:
        current_version = int(match.group(1))
        new_version = current_version + 1
        new_name = re.sub(version_pattern, f'_v{new_version:03d}', name_no_ext)
    else:
        # No version found, add v001
        new_name = f"{name_no_ext}_v001"
        new_version = 1
    
    new_path = os.path.join(script_dir, new_name + ext)
    
    # Check if already exists
    if os.path.exists(new_path):
        if not nuke.ask(f"Version {new_version:03d} already exists. Overwrite?"):
            return
    
    # Save as new version
    nuke.scriptSaveAs(new_path)
    
    nuke.message(
        f"Version Up Complete!\n\n"
        f"New version: v{new_version:03d}\n"
        f"Saved to: {new_path}"
    )

if __name__ == "__main__":
    main()

