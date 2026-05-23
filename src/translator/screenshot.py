"""Interactive screenshot capture.

Linux (Wayland): `gnome-screenshot -a -f <path>` — opens GNOME Shell's
native region selector (flameshot is XCB-only and the GNOME Wayland
compositor blocks it).

macOS: `screencapture -i -t png <path>` — opens the system region selector
(crosshair). User can press Esc to cancel; if cancelled the file is not
written.
"""
import os
import subprocess
import sys
import tempfile

TIMEOUT_SECONDS = 120


class ScreenshotError(Exception):
    pass


def _run_and_read(cmd: list[str], missing_msg: str) -> bytes:
    fd, path = tempfile.mkstemp(suffix=".png", prefix="translator-shot-")
    os.close(fd)
    # screencapture won't overwrite an empty existing file as "cancelled"
    # signal — pre-remove so its absence after the run means cancelled.
    try:
        os.unlink(path)
    except OSError:
        pass
    try:
        try:
            result = subprocess.run(
                cmd + [path],
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
            )
        except FileNotFoundError as e:
            raise ScreenshotError(missing_msg) from e
        except subprocess.TimeoutExpired as e:
            raise ScreenshotError("截图超时") from e

        if result.returncode != 0:
            msg = result.stderr.decode(errors="replace").strip() or "screenshot failed"
            raise ScreenshotError(msg)

        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise ScreenshotError("截图为空（可能被取消）")

        with open(path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _capture_linux() -> bytes:
    return _run_and_read(
        ["gnome-screenshot", "-a", "-f"],
        "gnome-screenshot not installed. Run: sudo apt install gnome-screenshot",
    )


def _capture_macos() -> bytes:
    return _run_and_read(
        ["screencapture", "-i", "-t", "png"],
        "screencapture not found (macOS only)",
    )


if sys.platform == "darwin":
    capture = _capture_macos
else:
    capture = _capture_linux
