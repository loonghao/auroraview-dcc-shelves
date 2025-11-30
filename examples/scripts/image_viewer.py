#!/usr/bin/env python
"""Simple image viewer - standalone utility."""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# Try to import PIL for better image support
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def main() -> None:
    """Open and display an image."""
    root = tk.Tk()
    root.withdraw()

    if HAS_PIL:
        filetypes = [
            ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
            ("All Files", "*.*"),
        ]
    else:
        filetypes = [
            ("GIF/PNG Files", "*.gif *.png"),
            ("All Files", "*.*"),
        ]

    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=filetypes,
    )

    if not file_path:
        root.destroy()
        return

    # Create viewer window
    viewer = tk.Toplevel()
    viewer.title(f"Image Viewer - {Path(file_path).name}")

    try:
        if HAS_PIL:
            img = Image.open(file_path)
            # Resize if too large
            max_size = (800, 600)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        else:
            photo = tk.PhotoImage(file=file_path)

        label = tk.Label(viewer, image=photo)
        label.image = photo  # Keep reference
        label.pack()

        # Add info label
        info = f"File: {Path(file_path).name}"
        if HAS_PIL:
            orig_img = Image.open(file_path)
            info += f" | Size: {orig_img.width}x{orig_img.height}"
        tk.Label(viewer, text=info).pack(pady=5)

        viewer.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open image:\n{e}")
        root.destroy()


if __name__ == "__main__":
    main()
    sys.exit(0)

