#!/usr/bin/env python
"""Simple calculator - works everywhere."""

import sys
import tkinter as tk


class Calculator:
    """A simple calculator application."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.resizable(False, False)
        self.expression = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        # Display
        self.display = tk.Entry(
            self.root, font=("Arial", 20), justify="right", bd=10
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew")

        # Buttons
        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("C", 4, 2), ("+", 4, 3),
            ("=", 5, 0),
        ]

        for text, row, col in buttons:
            colspan = 4 if text == "=" else 1
            btn = tk.Button(
                self.root,
                text=text,
                font=("Arial", 16),
                width=5,
                height=2,
                command=lambda t=text: self._on_click(t),
            )
            btn.grid(row=row, column=col, columnspan=colspan, sticky="nsew")

    def _on_click(self, char: str) -> None:
        """Handle button clicks."""
        if char == "C":
            self.expression = ""
        elif char == "=":
            try:
                result = eval(self.expression)  # noqa: S307
                self.expression = str(result)
            except Exception:
                self.expression = "Error"
        else:
            self.expression += char

        self.display.delete(0, tk.END)
        self.display.insert(0, self.expression)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    calc = Calculator()
    calc.run()


if __name__ == "__main__":
    main()
    sys.exit(0)
