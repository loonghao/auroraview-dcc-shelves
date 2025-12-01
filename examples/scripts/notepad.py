#!/usr/bin/env python
"""Simple notepad tool - works everywhere."""

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


class SimplePad:
    """A simple notepad application."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Simple Notepad")
        self.root.geometry("600x400")
        self.current_file = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file)
        file_menu.add_command(label="Open", command=self._open_file)
        file_menu.add_command(label="Save", command=self._save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Text area
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, font=("Consolas", 11)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _new_file(self) -> None:
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("Simple Notepad - New")

    def _open_file(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, encoding="utf-8") as f:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, f.read())
            self.current_file = file_path
            self.root.title(f"Simple Notepad - {file_path}")

    def _save_file(self) -> None:
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            )
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tk.END))
            messagebox.showinfo("Saved", f"File saved to:\n{self.current_file}")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = SimplePad()
    app.run()


if __name__ == "__main__":
    main()
    sys.exit(0)
