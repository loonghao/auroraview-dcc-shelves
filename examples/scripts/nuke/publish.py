# Nuke Publish Tool
# Publish comp to pipeline

import os

import nuke


def main():
    """Publish current script."""
    script_path = nuke.root().name()

    if not script_path or script_path == "Root":
        nuke.message("Please save the script first")
        return

    # Get script info
    script_name = os.path.basename(script_path)
    script_dir = os.path.dirname(script_path)

    # Find all write nodes
    write_nodes = [n for n in nuke.allNodes("Write")]

    if not write_nodes:
        nuke.message("No Write nodes found in script")
        return

    panel = nuke.Panel("Publish Comp")
    panel.addSingleLineInput("Version Comment", "")
    panel.addBooleanCheckBox("Render Before Publish", False)
    panel.addBooleanCheckBox("Include Inputs", True)

    if not panel.show():
        return

    comment = panel.value("Version Comment")
    render_first = panel.value("Render Before Publish")
    include_inputs = panel.value("Include Inputs")

    # Validate write nodes
    errors = []
    for w in write_nodes:
        if not w['file'].getValue():
            errors.append(f"{w.name()}: No file path set")
        if w['disable'].getValue():
            errors.append(f"{w.name()}: Node is disabled")

    if errors:
        nuke.message("Write node issues:\n\n" + "\n".join(errors))
        return

    # Render if requested
    if render_first:
        try:
            for w in write_nodes:
                if not w['disable'].getValue():
                    nuke.execute(w, nuke.root()['first_frame'].value(), nuke.root()['last_frame'].value())
        except Exception as e:
            nuke.message(f"Render failed: {str(e)}")
            return

    # Save publish version
    publish_dir = os.path.join(script_dir, "publish")
    if not os.path.exists(publish_dir):
        os.makedirs(publish_dir)

    # Version up
    base_name = os.path.splitext(script_name)[0]
    existing = [f for f in os.listdir(publish_dir) if f.startswith(base_name)]
    version = len(existing) + 1

    publish_name = f"{base_name}_v{version:03d}.nk"
    publish_path = os.path.join(publish_dir, publish_name)

    nuke.scriptSaveAs(publish_path)

    nuke.message(
        f"Published successfully!\n\n"
        f"Version: v{version:03d}\n"
        f"Path: {publish_path}\n"
        f"Comment: {comment or 'No comment'}"
    )

if __name__ == "__main__":
    main()
