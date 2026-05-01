"""Translator CLI entry point.

Pipeline: config → read selection → detect direction → translate → popup.
"""
import subprocess
import sys

from translator import clipboard, config, detect, minimax, popup


def notify(message: str) -> None:
    """Best-effort GNOME notification. Silent if notify-send is missing."""
    try:
        subprocess.run(["notify-send", "Translator", message], timeout=2)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"NOTIFY: {message}", file=sys.stderr)


def main() -> int:
    try:
        cfg = config.load()
    except config.ConfigError as e:
        notify(str(e))
        return 1

    try:
        text, truncated = clipboard.read_primary()
    except clipboard.ClipboardError as e:
        notify(str(e))
        return 1

    if not text.strip():
        notify("请先选中要翻译的文字")
        return 0

    direction = detect.direction(text)

    try:
        translation = minimax.translate(text, direction, **cfg)
    except minimax.TranslateError as e:
        popup.show(text, f"❌ {e}", truncated)
        return 1

    popup.show(text, translation, truncated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
