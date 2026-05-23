"""Best-effort desktop notification — silent if the backend is missing."""
import subprocess
import sys


def _escape_osa(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(message: str) -> None:
    if sys.platform == "darwin":
        script = (
            f'display notification "{_escape_osa(message)}" '
            f'with title "Translator"'
        )
        cmd = ["osascript", "-e", script]
    else:
        cmd = ["notify-send", "Translator", message]

    try:
        subprocess.run(cmd, timeout=2)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"NOTIFY: {message}", file=sys.stderr)
