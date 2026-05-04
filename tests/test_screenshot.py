import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from translator.screenshot import ScreenshotError, capture


def _fake_run_writes_file(payload: bytes, *, returncode=0, stderr=b""):
    """Build a subprocess.run side_effect that writes `payload` to the
    output path passed in cmd[-1] (gnome-screenshot's -f argument)."""
    def runner(cmd, **kwargs):
        out_path = cmd[-1]
        if payload is not None:
            with open(out_path, "wb") as f:
                f.write(payload)
        m = MagicMock()
        m.returncode = returncode
        m.stderr = stderr
        m.stdout = b""
        return m
    return runner


def test_returns_png_bytes():
    fake_png = b"\x89PNG\r\n\x1a\nbody"
    with patch(
        "translator.screenshot.subprocess.run",
        side_effect=_fake_run_writes_file(fake_png),
    ):
        assert capture() == fake_png


def test_invokes_gnome_screenshot_a_f():
    captured_cmd = []

    def runner(cmd, **kwargs):
        captured_cmd[:] = cmd
        with open(cmd[-1], "wb") as f:
            f.write(b"\x89PNG")
        m = MagicMock()
        m.returncode = 0
        m.stderr = b""
        return m

    with patch("translator.screenshot.subprocess.run", side_effect=runner):
        capture()
    assert captured_cmd[0] == "gnome-screenshot"
    assert "-a" in captured_cmd
    assert "-f" in captured_cmd


def test_temp_file_is_cleaned_up():
    written_path = []

    def runner(cmd, **kwargs):
        written_path.append(cmd[-1])
        with open(cmd[-1], "wb") as f:
            f.write(b"\x89PNG")
        m = MagicMock()
        m.returncode = 0
        m.stderr = b""
        return m

    with patch("translator.screenshot.subprocess.run", side_effect=runner):
        capture()
    assert written_path
    assert not os.path.exists(written_path[0])


def test_gnome_screenshot_not_installed():
    with patch("translator.screenshot.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(ScreenshotError, match="gnome-screenshot"):
            capture()


def test_gnome_screenshot_failure():
    with patch(
        "translator.screenshot.subprocess.run",
        side_effect=_fake_run_writes_file(None, returncode=1, stderr=b"some error"),
    ):
        with pytest.raises(ScreenshotError, match="some error"):
            capture()


def test_empty_file_means_cancelled():
    # Returncode 0 but no file written (or zero-size) → user cancelled
    with patch(
        "translator.screenshot.subprocess.run",
        side_effect=_fake_run_writes_file(b""),
    ):
        with pytest.raises(ScreenshotError, match="取消"):
            capture()


def test_no_file_written_means_cancelled():
    with patch(
        "translator.screenshot.subprocess.run",
        side_effect=_fake_run_writes_file(None),
    ):
        with pytest.raises(ScreenshotError, match="取消"):
            capture()


def test_timeout():
    with patch(
        "translator.screenshot.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gnome-screenshot", timeout=120),
    ):
        with pytest.raises(ScreenshotError, match="超时"):
            capture()
