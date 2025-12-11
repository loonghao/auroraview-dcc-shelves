#!/usr/bin/env python
"""Display system information - standalone only."""

import os
import platform
import sys
import tkinter as tk
from tkinter import scrolledtext


def get_system_info() -> str:
    """Collect system information."""
    info_lines = [
        "=== System Information ===",
        "",
        f"Platform: {platform.system()} {platform.release()}",
        f"Machine: {platform.machine()}",
        f"Processor: {platform.processor()}",
        f"Python Version: {sys.version}",
        f"Python Executable: {sys.executable}",
        "",
        "=== Environment Variables ===",
        "",
    ]

    # Add some useful environment variables
    env_vars = ["PATH", "PYTHONPATH", "HOME", "USER", "USERNAME", "TEMP", "TMP"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        # Truncate long values
        if len(value) > 100:
            value = value[:100] + "..."
        info_lines.append(f"{var}: {value}")

    return "\n".join(info_lines)


def main() -> None:
    """Show system info in a window."""
    root = tk.Tk()
    root.title("System Information")
    root.geometry("600x400")

    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10))
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_area.insert(tk.END, get_system_info())
    text_area.config(state=tk.DISABLED)

    # Add close button
    close_btn = tk.Button(root, text="Close", command=root.destroy)
    close_btn.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
