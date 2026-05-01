from unittest.mock import MagicMock, patch

import pytest

from translator.clipboard import MAX_LEN, ClipboardError, read_primary


def _result(stdout="", returncode=0, stderr=""):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


def test_reads_primary_selection():
    with patch("translator.clipboard.subprocess.run", return_value=_result("hello")):
        text, truncated = read_primary()
    assert text == "hello"
    assert truncated is False


def test_empty_selection():
    with patch("translator.clipboard.subprocess.run", return_value=_result("")):
        text, truncated = read_primary()
    assert text == ""
    assert truncated is False


def test_truncates_long_text():
    long = "x" * (MAX_LEN + 500)
    with patch("translator.clipboard.subprocess.run", return_value=_result(long)):
        text, truncated = read_primary()
    assert len(text) == MAX_LEN
    assert truncated is True


def test_at_threshold_not_truncated():
    exact = "x" * MAX_LEN
    with patch("translator.clipboard.subprocess.run", return_value=_result(exact)):
        text, truncated = read_primary()
    assert len(text) == MAX_LEN
    assert truncated is False


def test_wl_paste_not_installed():
    with patch("translator.clipboard.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(ClipboardError, match="wl-paste"):
            read_primary()


def test_wl_paste_failure():
    with patch(
        "translator.clipboard.subprocess.run",
        return_value=_result(returncode=1, stderr="some error"),
    ):
        with pytest.raises(ClipboardError, match="some error"):
            read_primary()


def test_invokes_correct_command():
    with patch("translator.clipboard.subprocess.run", return_value=_result("x")) as m:
        read_primary()
    args, _ = m.call_args
    assert args[0] == ["wl-paste", "--primary", "--no-newline"]
