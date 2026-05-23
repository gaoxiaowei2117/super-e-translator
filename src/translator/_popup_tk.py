"""Tkinter popup for translation results (macOS).

Tkinter ships with python.org / Homebrew python, so no extra deps are
needed. We raise the window to the foreground and bind Esc to close.
"""
import tkinter as tk
from tkinter import ttk


def show(original: str, translation: str, truncated: bool = False) -> None:
    root = tk.Tk()
    root.title("Translator")
    root.geometry("520x260")

    # macOS: lifeline so the window actually comes to the front.
    root.lift()
    root.attributes("-topmost", True)
    root.after(150, lambda: root.attributes("-topmost", False))
    root.focus_force()

    root.bind("<Escape>", lambda _e: root.destroy())

    container = ttk.Frame(root, padding=12)
    container.pack(fill="both", expand=True)

    if truncated:
        ttk.Label(
            container,
            text="⚠ 已截断到 2000 字符",
            foreground="#888",
        ).pack(anchor="w")

    orig = tk.Text(container, height=4, wrap="word", borderwidth=0)
    orig.insert("1.0", original)
    orig.configure(state="disabled", foreground="#666", background=root.cget("bg"))
    orig.pack(fill="x", pady=(0, 8))

    trans = tk.Text(container, wrap="word", borderwidth=0, font=("Helvetica", 14, "bold"))
    trans.insert("1.0", translation)
    trans.configure(state="disabled", background=root.cget("bg"))
    trans.pack(fill="both", expand=True, pady=(0, 8))

    def on_copy() -> None:
        root.clipboard_clear()
        root.clipboard_append(translation)

    ttk.Button(container, text="复制译文", command=on_copy).pack(anchor="e")

    root.mainloop()
