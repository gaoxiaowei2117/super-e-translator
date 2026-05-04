"""Interactive screenshot capture via flameshot.

`flameshot gui -r` opens flameshot's region selector and writes the captured
PNG to stdout. We bypass flameshot's own (broken on GNOME Wayland) global
hotkey by invoking the binary directly.
"""
import subprocess

TIMEOUT_SECONDS = 120


class ScreenshotError(Exception):
    pass


def capture() -> bytes:
    """Run flameshot interactively and return PNG bytes.

    Raises ScreenshotError if flameshot is missing, the user cancels, or
    the subprocess fails.
    """
    try:
        result = subprocess.run(
            ["flameshot", "gui", "-r"],
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError as e:
        raise ScreenshotError(
            "flameshot not installed. Run: sudo apt install flameshot"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ScreenshotError("截图超时") from e

    if result.returncode != 0:
        msg = result.stderr.decode(errors="replace").strip() or "flameshot failed"
        raise ScreenshotError(msg)
    if not result.stdout:
        raise ScreenshotError("截图为空（可能被取消）")
    return result.stdout
