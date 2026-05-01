import subprocess

MAX_LEN = 2000


class ClipboardError(Exception):
    pass


def read_primary() -> tuple[str, bool]:
    """Read the Wayland PRIMARY selection.

    Returns (text, truncated). Raises ClipboardError if wl-paste is missing
    or fails for reasons other than an empty selection.
    """
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

    text = result.stdout
    truncated = False
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN]
        truncated = True
    return text, truncated
