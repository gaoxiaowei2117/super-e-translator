"""Read the user's current text selection.

Linux (Wayland): `wl-paste --primary` reads the PRIMARY selection — set by
any text highlight, no Ctrl+C needed.

macOS: there is no PRIMARY selection. We dispatch ⌘C to the frontmost app
via AppleScript, briefly wait for the pasteboard to update, then read
`pbpaste`. Requires Accessibility permission for the process that invokes
us (Shortcuts / skhd / Terminal — first run will prompt).
"""
import subprocess
import sys
import time

MAX_LEN = 2000


class ClipboardError(Exception):
    pass


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) > MAX_LEN:
        return text[:MAX_LEN], True
    return text, False


def _read_primary_linux() -> tuple[str, bool]:
    try:
        result = subprocess.run(
            ["wl-paste", "--primary", "--no-newline"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except FileNotFoundError as e:
        raise ClipboardError(
            "wl-paste not installed. Run: sudo apt install wl-clipboard"
        ) from e
    if result.returncode != 0:
        raise ClipboardError(result.stderr.strip() or "wl-paste failed")
    return _truncate(result.stdout)


def _pbpaste() -> str:
    try:
        result = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=2
        )
    except FileNotFoundError as e:
        raise ClipboardError("pbpaste not found (macOS only)") from e
    if result.returncode != 0:
        raise ClipboardError(result.stderr.strip() or "pbpaste failed")
    return result.stdout


def _read_primary_macos() -> tuple[str, bool]:
    # Snapshot the clipboard so we can tell if ⌘C actually changed it.
    before = _pbpaste()

    osa = (
        'tell application "System Events" to keystroke "c" using {command down}'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", osa],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except FileNotFoundError as e:
        raise ClipboardError("osascript not found (macOS only)") from e
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "not allowed assistive access" in stderr or "1002" in stderr:
            raise ClipboardError(
                "需要辅助功能权限：系统设置 → 隐私与安全性 → 辅助功能 → "
                "勾选调用 translator 的程序（如 Shortcuts/Terminal/skhd）"
            )
        raise ClipboardError(stderr or "osascript failed")

    # Poll briefly for the pasteboard to update — apps need a moment.
    deadline = time.monotonic() + 0.5
    text = before
    while time.monotonic() < deadline:
        text = _pbpaste()
        if text != before:
            break
        time.sleep(0.04)

    return _truncate(text)


if sys.platform == "darwin":
    read_primary = _read_primary_macos
else:
    read_primary = _read_primary_linux
