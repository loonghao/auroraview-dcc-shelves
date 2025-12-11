#!/usr/bin/env python
"""Color picker tool - works everywhere."""

import sys
import tkinter as tk
from tkinter import colorchooser


def main() -> None:
    """Show a color picker dialog."""
    root = tk.Tk()
    root.withdraw()

    color = colorchooser.askcolor(title="Choose a Color")

    if color[1]:  # If user selected a color
        # Show the selected color
        result_window = tk.Toplevel()
        result_window.title("Selected Color")
        result_window.geometry("300x150")

        # Color preview
        preview = tk.Frame(result_window, bg=color[1], width=280, height=80)
        preview.pack(pady=10, padx=10)
        preview.pack_propagate(False)

        # Color info
        rgb = color[0]
        info_text = f"HEX: {color[1]}\nRGB: ({int(rgb[0])}, {int(rgb[1])}, {int(rgb[2])})"
        label = tk.Label(result_window, text=info_text, font=("Arial", 11))
        label.pack()

        result_window.mainloop()
    else:
        root.destroy()


if __name__ == "__main__":
    main()
    sys.exit(0)
