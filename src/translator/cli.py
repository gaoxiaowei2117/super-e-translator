"""Translator CLI entry point.

Pipeline: config → read selection → detect direction → translate → popup.
"""
import sys

from translator import clipboard, config, detect, minimax, popup
from translator.notify import notify


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

    stripped = text.strip()
    if not stripped:
        notify("请先选中要翻译的文字")
        return 0

    try:
        if detect.is_single_word(stripped):
            result = minimax.lookup_word(stripped, **cfg)
        else:
            result = minimax.translate(text, detect.direction(text), **cfg)
    except minimax.TranslateError as e:
        popup.show(text, f"❌ {e}", truncated)
        return 1

    popup.show(text, result, truncated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
