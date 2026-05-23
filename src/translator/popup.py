"""Popup dispatcher — picks GTK4 (Linux) or Tkinter (macOS) at call time."""
import sys


def show(original: str, translation: str, truncated: bool = False) -> None:
    if sys.platform == "darwin":
        from translator._popup_tk import show as _show
    else:
        from translator._popup_gtk import show as _show
    _show(original, translation, truncated)
