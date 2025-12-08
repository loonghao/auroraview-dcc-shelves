#!/usr/bin/env python
"""Example: Run AuroraView DCC Shelves as a standalone desktop application.

This example demonstrates how to run the shelf system as a native desktop
application without any DCC software. Uses tao/wry native window directly
without Qt dependency.

Usage:
    python run_desktop.py

Or with command line:
    python -m auroraview_dcc_shelves -c ../shelf_config.yaml
    auroraview-shelves -c ../shelf_config.yaml
"""

from pathlib import Path


def main():
    """Run the shelf as a desktop application."""
    # Get the path to the example configuration
    examples_dir = Path(__file__).parent.parent
    config_path = examples_dir / "shelf_config.yaml"

    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        print("Please ensure shelf_config.yaml exists in the examples directory.")
        return 1

    print(f"Loading configuration from: {config_path}")
    print("Starting AuroraView DCC Shelves in desktop mode...")

    # Using run_desktop function (recommended)
    # This uses native tao/wry window without Qt dependency
    from auroraview_dcc_shelves.apps.desktop import run_desktop

    return run_desktop(
        config_path=str(config_path),
        debug=True,  # Enable DevTools for debugging
        title="Pipeline Studio - Desktop",
    )


def main_alternative():
    """Alternative method using ShelfApp directly.

    This gives more control over the application lifecycle.
    Note: This method also uses native tao/wry window (no Qt).
    """
    from pathlib import Path

    from auroraview_dcc_shelves import ShelfApp, load_config

    # Load configuration
    examples_dir = Path(__file__).parent.parent
    config_path = examples_dir / "shelf_config.yaml"
    config = load_config(str(config_path))

    # Create ShelfApp
    app = ShelfApp(
        config=config,
        title="Pipeline Studio - Desktop",
        width=900,
        height=700,
    )

    # Show using desktop adapter
    # app="desktop" triggers the DesktopAdapter which uses native tao/wry window
    # The show() call is BLOCKING in desktop mode - it runs the event loop
    app.show(debug=True, app="desktop")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
