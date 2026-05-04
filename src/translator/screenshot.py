"""Interactive screenshot capture via gnome-screenshot.

`gnome-screenshot -a -f <path>` opens GNOME Shell's native region selector
(works on Wayland; flameshot doesn't because it uses XCB which the GNOME
Wayland compositor blocks).
"""
import os
import subprocess
import tempfile

TIMEOUT_SECONDS = 120


class ScreenshotError(Exception):
    pass


def capture() -> bytes:
    """Run gnome-screenshot interactively and return PNG bytes.

    Raises ScreenshotError if gnome-screenshot is missing, the user cancels,
    or the subprocess fails.
    """
    fd, path = tempfile.mkstemp(suffix=".png", prefix="translator-shot-")
    os.close(fd)
    try:
        try:
            result = subprocess.run(
                ["gnome-screenshot", "-a", "-f", path],
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
            )
        except FileNotFoundError as e:
            raise ScreenshotError(
                "gnome-screenshot not installed. Run: sudo apt install gnome-screenshot"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise ScreenshotError("截图超时") from e

        if result.returncode != 0:
            msg = result.stderr.decode(errors="replace").strip() or "gnome-screenshot failed"
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
