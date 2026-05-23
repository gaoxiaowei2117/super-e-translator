from unittest.mock import MagicMock, patch

import pytest

from translator import clipboard
from translator.clipboard import (
    MAX_LEN,
    ClipboardError,
    _read_primary_linux,
    _read_primary_macos,
)


def _result(stdout="", returncode=0, stderr=""):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


# -- Linux backend -----------------------------------------------------------

def test_reads_primary_selection():
    with patch("translator.clipboard.subprocess.run", return_value=_result("hello")):
        text, truncated = _read_primary_linux()
    assert text == "hello"
    assert truncated is False


def test_empty_selection():
    with patch("translator.clipboard.subprocess.run", return_value=_result("")):
        text, truncated = _read_primary_linux()
    assert text == ""
    assert truncated is False


def test_truncates_long_text():
    long = "x" * (MAX_LEN + 500)
    with patch("translator.clipboard.subprocess.run", return_value=_result(long)):
        text, truncated = _read_primary_linux()
    assert len(text) == MAX_LEN
    assert truncated is True


def test_at_threshold_not_truncated():
    exact = "x" * MAX_LEN
    with patch("translator.clipboard.subprocess.run", return_value=_result(exact)):
        text, truncated = _read_primary_linux()
    assert len(text) == MAX_LEN
    assert truncated is False


def test_wl_paste_not_installed():
    with patch("translator.clipboard.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(ClipboardError, match="wl-paste"):
            _read_primary_linux()


def test_wl_paste_failure():
    with patch(
        "translator.clipboard.subprocess.run",
        return_value=_result(returncode=1, stderr="some error"),
    ):
        with pytest.raises(ClipboardError, match="some error"):
            _read_primary_linux()


def test_invokes_correct_command():
    with patch("translator.clipboard.subprocess.run", return_value=_result("x")) as m:
        _read_primary_linux()
    args, _ = m.call_args
    assert args[0] == ["wl-paste", "--primary", "--no-newline"]


# -- macOS backend -----------------------------------------------------------

def _macos_run_factory(*, before_clip="", after_clip="hello", osa_rc=0, osa_stderr=""):
    """Returns a subprocess.run double for the macOS path.

    pbpaste is called twice (before / after osascript). osascript is called
    in the middle. We dispatch based on cmd[0].
    """
    pbpaste_calls = {"n": 0}

    def runner(cmd, **_kw):
        if cmd[0] == "pbpaste":
            pbpaste_calls["n"] += 1
            text = before_clip if pbpaste_calls["n"] == 1 else after_clip
            return _result(stdout=text)
        if cmd[0] == "osascript":
            return _result(returncode=osa_rc, stderr=osa_stderr)
        raise AssertionError(f"unexpected cmd: {cmd}")

    return runner


def test_macos_reads_changed_clipboard():
    with patch(
        "translator.clipboard.subprocess.run",
        side_effect=_macos_run_factory(before_clip="old", after_clip="selected text"),
    ):
        text, truncated = _read_primary_macos()
    assert text == "selected text"
    assert truncated is False


def test_macos_truncates():
    long = "x" * (MAX_LEN + 100)
    with patch(
        "translator.clipboard.subprocess.run",
        side_effect=_macos_run_factory(before_clip="", after_clip=long),
    ):
        text, truncated = _read_primary_macos()
    assert len(text) == MAX_LEN
    assert truncated is True


def test_macos_no_change_returns_existing():
    # If ⌘C doesn't change the clipboard (e.g. focused app has no selection),
    # we still return whatever was there.
    with patch(
        "translator.clipboard.subprocess.run",
        side_effect=_macos_run_factory(before_clip="prev", after_clip="prev"),
    ):
        text, _ = _read_primary_macos()
    assert text == "prev"


def test_macos_accessibility_denied():
    with patch(
        "translator.clipboard.subprocess.run",
        side_effect=_macos_run_factory(
            osa_rc=1, osa_stderr="osascript: not allowed assistive access"
        ),
    ):
        with pytest.raises(ClipboardError, match="辅助功能"):
            _read_primary_macos()


def test_dispatch_picks_platform():
    import sys
    expected = _read_primary_macos if sys.platform == "darwin" else _read_primary_linux
    assert clipboard.read_primary is expected
