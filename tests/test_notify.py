import sys
from unittest.mock import patch

from translator import notify as notify_mod


def test_picks_osascript_on_macos():
    with patch.object(notify_mod, "sys") as fake_sys, \
         patch.object(notify_mod.subprocess, "run") as run:
        fake_sys.platform = "darwin"
        fake_sys.stderr = sys.stderr
        notify_mod.notify("hello")
    cmd = run.call_args.args[0]
    assert cmd[0] == "osascript"
    assert "display notification" in cmd[2]
    assert "hello" in cmd[2]


def test_picks_notify_send_on_linux():
    with patch.object(notify_mod, "sys") as fake_sys, \
         patch.object(notify_mod.subprocess, "run") as run:
        fake_sys.platform = "linux"
        fake_sys.stderr = sys.stderr
        notify_mod.notify("hello")
    cmd = run.call_args.args[0]
    assert cmd == ["notify-send", "Translator", "hello"]


def test_osa_quotes_are_escaped():
    with patch.object(notify_mod, "sys") as fake_sys, \
         patch.object(notify_mod.subprocess, "run") as run:
        fake_sys.platform = "darwin"
        fake_sys.stderr = sys.stderr
        notify_mod.notify('he said "hi"')
    script = run.call_args.args[0][2]
    assert '\\"hi\\"' in script
