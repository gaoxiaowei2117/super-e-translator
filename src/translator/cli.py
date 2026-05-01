"""Translator CLI entry point.

Pipeline: config → read selection → detect direction → translate → display.
v1 prints to stdout; popup is wired in Task 8.
"""
import subprocess
import sys

from translator import clipboard, config, detect, minimax


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
        notify(f"翻译失败: {e}")
        return 1

    # MVP: print to stdout. Replaced by popup in Task 8.
    if truncated:
        print("[已截断到 2000 字符]")
    print(f"原文: {text}")
    print(f"译文: {translation}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
