#!/usr/bin/env python
"""Example: Minimal desktop application with custom configuration.

This example shows how to create a minimal shelf with custom buttons
programmatically, without using a YAML file.

Uses native tao/wry window without Qt dependency.
"""

from auroraview_dcc_shelves import ShelfApp
from auroraview_dcc_shelves.config import (
    BannerConfig,
    ButtonConfig,
    ShelfConfig,
    ShelvesConfig,
    ToolType,
)


def main():
    """Create and run a minimal desktop shelf."""
    # Create configuration programmatically
    config = ShelvesConfig(
        banner=BannerConfig(
            title="My Tools",
            subtitle="Custom Desktop Shelf",
            gradient_from="rgba(59, 130, 246, 0.35)",  # Blue
            gradient_to="rgba(147, 51, 234, 0.35)",  # Purple
        ),
        shelves=[
            ShelfConfig(
                name="Quick Tools",
                buttons=[
                    ButtonConfig(
                        name="Hello World",
                        icon="Smile",
                        tool_type=ToolType.PYTHON,
                        tool_path="print('Hello from Desktop!')",
                        description="A simple hello world example",
                    ),
                    ButtonConfig(
                        name="System Info",
                        icon="Monitor",
                        tool_type=ToolType.PYTHON,
                        tool_path="import platform; print(f'Python {platform.python_version()} on {platform.system()}')",
                        description="Show system information",
                    ),
                    ButtonConfig(
                        name="Calculator",
                        icon="Hash",
                        tool_type=ToolType.EXECUTABLE,
                        tool_path="calc.exe",  # Windows calculator
                        description="Open system calculator",
                    ),
                ],
            ),
        ],
    )

    # Create and show the app
    app = ShelfApp(
        config=config,
        title="My Desktop Tools",
        width=600,
        height=400,
    )

    # Show in desktop mode
    # app="desktop" triggers native tao/wry window
    # The show() call is BLOCKING - it runs the event loop until window closes
    app.show(debug=True, app="desktop")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
