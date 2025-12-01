# Nuke Write Manager Tool
# Manage all Write nodes

import os

import nuke


def main():
    """Open Write node manager."""
    write_nodes = [n for n in nuke.allNodes("Write")]

    if not write_nodes:
        nuke.message("No Write nodes found in script")
        return

    # Build info panel
    info = "Write Nodes Status:\n\n"

    for w in write_nodes:
        status = "✓ Active" if not w['disable'].getValue() else "✗ Disabled"
        file_path = w['file'].getValue() or "NO PATH SET"
        file_type = w['file_type'].getValue() or "auto"
        info += f"[{w.name()}] {status}\n"
        info += f"  Path: {file_path}\n"
        info += f"  Format: {file_type}\n\n"

    choices = [
        "Enable All Writes",
        "Disable All Writes",
        "Toggle Selected Write",
        "Set All to EXR",
        "Set All to PNG",
        "Create Output Directories",
        "Render All Active",
    ]

    panel = nuke.Panel("Write Manager")
    panel.addEnumerationPulldown("Action", " ".join(choices))
    panel.addNotepad("Info", info)

    if not panel.show():
        return

    action = panel.value("Action")

    if action == "Enable All Writes":
        for w in write_nodes:
            w['disable'].setValue(False)
        nuke.message(f"Enabled {len(write_nodes)} Write nodes")

    elif action == "Disable All Writes":
        for w in write_nodes:
            w['disable'].setValue(True)
        nuke.message(f"Disabled {len(write_nodes)} Write nodes")

    elif action == "Toggle Selected Write":
        selected = nuke.selectedNodes("Write")
        if not selected:
            nuke.message("Select a Write node")
            return
        for w in selected:
            w['disable'].setValue(not w['disable'].getValue())
        nuke.message(f"Toggled {len(selected)} Write nodes")

    elif action == "Set All to EXR":
        for w in write_nodes:
            w['file_type'].setValue('exr')
        nuke.message("All Write nodes set to EXR")

    elif action == "Set All to PNG":
        for w in write_nodes:
            w['file_type'].setValue('png')
        nuke.message("All Write nodes set to PNG")

    elif action == "Create Output Directories":
        created = 0
        for w in write_nodes:
            file_path = w['file'].getValue()
            if file_path:
                dir_path = os.path.dirname(file_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    created += 1
        nuke.message(f"Created {created} directories")

    elif action == "Render All Active":
        active_writes = [w for w in write_nodes if not w['disable'].getValue()]
        if not active_writes:
            nuke.message("No active Write nodes")
            return

        first = int(nuke.root()['first_frame'].value())
        last = int(nuke.root()['last_frame'].value())

        if nuke.ask(f"Render {len(active_writes)} Write nodes? Frames {first}-{last}"):
            for w in active_writes:
                try:
                    nuke.execute(w, first, last)
                except Exception as e:
                    nuke.message(f"Error rendering {w.name()}: {str(e)}")
                    return
            nuke.message("Render complete!")

if __name__ == "__main__":
    main()
