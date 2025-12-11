#!/usr/bin/env python
"""File browser tool - standalone utility."""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox


def main() -> None:
    """Open file browser and show selected file info."""
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=[
            ("All Files", "*.*"),
            ("Python Files", "*.py"),
            ("Text Files", "*.txt"),
            ("Image Files", "*.png *.jpg *.jpeg *.gif"),
        ],
    )

    if file_path:
        # Get file info
        stat = os.stat(file_path)
        size_kb = stat.st_size / 1024

        info = (
            f"File: {os.path.basename(file_path)}\n"
            f"Path: {file_path}\n"
            f"Size: {size_kb:.2f} KB\n"
            f"Extension: {os.path.splitext(file_path)[1] or 'None'}"
        )

        messagebox.showinfo("File Information", info)

    root.destroy()


if __name__ == "__main__":
    main()
    sys.exit(0)
