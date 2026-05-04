from unittest.mock import MagicMock, patch

import pytest

from translator.screenshot import ScreenshotError, capture


def _result(stdout=b"", stderr=b"", returncode=0):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


def test_returns_png_bytes():
    fake_png = b"\x89PNG\r\n\x1a\nbody"
    with patch("translator.screenshot.subprocess.run", return_value=_result(stdout=fake_png)):
        assert capture() == fake_png


def test_invokes_flameshot_gui_raw():
    with patch("translator.screenshot.subprocess.run", return_value=_result(stdout=b"x")) as m:
        capture()
    args, _ = m.call_args
    assert args[0] == ["flameshot", "gui", "-r"]


def test_flameshot_not_installed():
    with patch("translator.screenshot.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(ScreenshotError, match="flameshot"):
            capture()


def test_flameshot_failure():
    with patch(
        "translator.screenshot.subprocess.run",
        return_value=_result(stderr=b"some error", returncode=1),
    ):
        with pytest.raises(ScreenshotError, match="some error"):
            capture()


def test_empty_stdout_means_cancelled():
    with patch("translator.screenshot.subprocess.run", return_value=_result(stdout=b"")):
        with pytest.raises(ScreenshotError, match="取消"):
            capture()


def test_timeout():
    import subprocess
    with patch(
        "translator.screenshot.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="flameshot", timeout=120),
    ):
        with pytest.raises(ScreenshotError, match="超时"):
            capture()
