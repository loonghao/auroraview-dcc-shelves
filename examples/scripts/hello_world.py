#!/usr/bin/env python
"""Simple hello world script - works in any environment."""

import sys
import tkinter as tk
from tkinter import messagebox


def main() -> None:
    """Show a hello world message box."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    messagebox.showinfo(
        "Hello from DCC Shelves",
        "Hello World!\n\n"
        "This tool works in any environment:\n"
        "- Standalone Python\n"
        "- Maya\n"
        "- Houdini\n"
        "- Any DCC with Python support",
    )

    root.destroy()


if __name__ == "__main__":
    main()
    sys.exit(0)
