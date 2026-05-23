"""Image-translate CLI entry point.

Pipeline: config → interactive screenshot → MiniMax VLM → popup.
Bound to Super+R (Linux) / a Shortcut (macOS) — see install.sh.
"""
import sys

from translator import config, minimax, popup, screenshot
from translator.notify import notify


def main() -> int:
    try:
        cfg = config.load()
    except config.ConfigError as e:
        notify(str(e))
        return 1

    try:
        png_bytes = screenshot.capture()
    except screenshot.ScreenshotError as e:
        notify(str(e))
        return 1

    try:
        translation = minimax.translate_image(png_bytes, api_key=cfg["api_key"])
    except minimax.TranslateError as e:
        popup.show("[图片]", f"❌ {e}")
        return 1

    popup.show("[图片]", translation)
    return 0


if __name__ == "__main__":
    sys.exit(main())
