# Translator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `translator` — a Super+E hotkey on Ubuntu 24.04 that reads the PRIMARY selection, translates EN↔ZH via the MiniMax mainland API, and shows the result in a GTK4 popup.

**Architecture:** Single Python 3 CLI invoked fresh on every hotkey press. GNOME custom-keybinding fires the command. Components are 6 small modules: config, clipboard, detect, minimax, popup, cli. Each module is independently unit-tested except popup (GTK, manual verification).

**Tech Stack:** Python 3.12 (Ubuntu 24.04 default), GTK4 via PyGObject, httpx, wl-clipboard, pytest + pytest-httpx.

Spec: [docs/superpowers/specs/2026-05-01-translator-design.md](../specs/2026-05-01-translator-design.md)

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/translator/__init__.py`
- Create: `tests/__init__.py`
- Create: `config.example.toml`
- Create: `.gitignore`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "translator"
version = "0.1.0"
description = "Super+E hotkey translator for Ubuntu, powered by MiniMax"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27"]

[project.scripts]
translator = "translator.cli:main"

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-httpx>=0.30"]

[tool.hatch.build.targets.wheel]
packages = ["src/translator"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty `src/translator/__init__.py` and `tests/__init__.py`**

Both files should be empty.

- [ ] **Step 3: Create `config.example.toml`**

```toml
# Copy this to ~/.config/translator/config.toml and fill in your API key.
api_key  = ""
model    = "abab6.5s-chat"
endpoint = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
```

- [ ] **Step 4: Create `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
build/
dist/
*.egg-info/
.venv/
```

- [ ] **Step 5: Install dev dependencies and verify structure**

```bash
pip install --user -e ".[dev]"
python -c "import translator; print('ok')"
pytest --collect-only
```

Expected: `ok` printed; pytest finds 0 tests but no errors.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/ tests/ config.example.toml .gitignore
git commit -m "scaffold: project structure with hatchling and pytest"
```

---

### Task 2: Direction detection (`detect.py`)

**Files:**
- Create: `src/translator/detect.py`
- Create: `tests/test_detect.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_detect.py`:
```python
from translator.detect import direction


def test_pure_english():
    assert direction("Hello world") == "auto→zh"


def test_pure_chinese():
    assert direction("你好世界") == "zh→en"


def test_mixed_below_threshold():
    # "hello 你好 there" — 14 chars, 2 chinese = 14% < 30%
    assert direction("hello 你好 there") == "auto→zh"


def test_mixed_above_threshold():
    # "hi 你好世界 ok" — 10 chars, 4 chinese = 40% > 30%
    assert direction("hi 你好世界 ok") == "zh→en"


def test_empty():
    assert direction("") == "auto→zh"


def test_whitespace_only():
    assert direction("   \n\t") == "auto→zh"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_detect.py -v`
Expected: 6 errors with `ModuleNotFoundError: No module named 'translator.detect'`.

- [ ] **Step 3: Implement `src/translator/detect.py`**

```python
def direction(text: str) -> str:
    """Return 'zh→en' if text is mostly Chinese, otherwise 'auto→zh'.

    Threshold: ≥30% of characters are CJK Unified Ideographs.
    """
    if not text or text.isspace():
        return "auto→zh"
    chinese = sum(1 for c in text if "一" <= c <= "鿿")
    return "zh→en" if chinese / len(text) >= 0.3 else "auto→zh"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_detect.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/translator/detect.py tests/test_detect.py
git commit -m "feat(detect): add Chinese-ratio based direction detection"
```

---

### Task 3: Config loader (`config.py`)

**Files:**
- Create: `src/translator/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config.py`:
```python
import pytest
import tomllib

from translator.config import ConfigError, load


def test_missing_file(tmp_path):
    p = tmp_path / "noexist.toml"
    with pytest.raises(ConfigError, match="not found"):
        load(p)


def test_missing_api_key(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('model = "x"\n')
    with pytest.raises(ConfigError, match="api_key"):
        load(p)


def test_empty_api_key(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('api_key = ""\n')
    with pytest.raises(ConfigError, match="api_key"):
        load(p)


def test_defaults(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('api_key = "k"\n')
    cfg = load(p)
    assert cfg["api_key"] == "k"
    assert cfg["model"] == "abab6.5s-chat"
    assert cfg["endpoint"] == "https://api.minimaxi.com/v1/text/chatcompletion_v2"


def test_overrides(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(
        'api_key = "k"\n'
        'model = "MiniMax-Text-01"\n'
        'endpoint = "https://x.test"\n'
    )
    cfg = load(p)
    assert cfg["model"] == "MiniMax-Text-01"
    assert cfg["endpoint"] == "https://x.test"


def test_malformed_toml(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text("api_key = unclosed")
    with pytest.raises(tomllib.TOMLDecodeError):
        load(p)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: errors with `ModuleNotFoundError: No module named 'translator.config'`.

- [ ] **Step 3: Implement `src/translator/config.py`**

```python
import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "translator" / "config.toml"

DEFAULT_MODEL = "abab6.5s-chat"
DEFAULT_ENDPOINT = "https://api.minimaxi.com/v1/text/chatcompletion_v2"


class ConfigError(Exception):
    pass


def load(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    data = tomllib.loads(path.read_text())
    api_key = data.get("api_key", "").strip()
    if not api_key:
        raise ConfigError(f"api_key not set in {path}")
    return {
        "api_key": api_key,
        "model": data.get("model", DEFAULT_MODEL),
        "endpoint": data.get("endpoint", DEFAULT_ENDPOINT),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/translator/config.py tests/test_config.py
git commit -m "feat(config): TOML loader with defaults and validation"
```

---

### Task 4: Clipboard reader (`clipboard.py`)

**Files:**
- Create: `src/translator/clipboard.py`
- Create: `tests/test_clipboard.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_clipboard.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clipboard.py -v`
Expected: errors with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/translator/clipboard.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_clipboard.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add src/translator/clipboard.py tests/test_clipboard.py
git commit -m "feat(clipboard): wl-paste --primary wrapper with truncation"
```

---

### Task 5: MiniMax client (`minimax.py`)

**Files:**
- Create: `src/translator/minimax.py`
- Create: `tests/test_minimax.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_minimax.py`:
```python
import json

import httpx
import pytest

from translator.minimax import TranslateError, translate

API_KEY = "test-key"
ENDPOINT = "https://api.test/v1/chat"
MODEL = "test-model"


def _ok(content="你好"):
    return {"choices": [{"message": {"content": content}}]}


def _call(direction="auto→zh", text="hello"):
    return translate(
        text, direction, api_key=API_KEY, model=MODEL, endpoint=ENDPOINT
    )


def test_returns_translation(httpx_mock):
    httpx_mock.add_response(json=_ok("你好"))
    assert _call() == "你好"


def test_request_shape(httpx_mock):
    httpx_mock.add_response(json=_ok())
    _call()
    req = httpx_mock.get_request()
    assert req.url == ENDPOINT
    assert req.method == "POST"
    assert req.headers["authorization"] == f"Bearer {API_KEY}"
    body = json.loads(req.read())
    assert body["model"] == MODEL
    assert body["messages"][1]["content"] == "hello"
    assert "Simplified Chinese" in body["messages"][0]["content"]


def test_zh_to_en_uses_english_prompt(httpx_mock):
    httpx_mock.add_response(json=_ok("hi"))
    _call(direction="zh→en", text="你好")
    body = json.loads(httpx_mock.get_request().read())
    assert "English" in body["messages"][0]["content"]


def test_strips_whitespace_from_translation(httpx_mock):
    httpx_mock.add_response(json=_ok("  hello  \n"))
    assert _call() == "hello"


def test_4xx_raises(httpx_mock):
    httpx_mock.add_response(status_code=401, text="unauthorized")
    with pytest.raises(TranslateError, match="401"):
        _call()


def test_5xx_retries_then_succeeds(httpx_mock):
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(json=_ok("你好"))
    assert _call() == "你好"


def test_5xx_persistent_fails(httpx_mock):
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    with pytest.raises(TranslateError, match="500"):
        _call()


def test_network_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("dns fail"))
    with pytest.raises(TranslateError, match="网络"):
        _call()


def test_malformed_response(httpx_mock):
    httpx_mock.add_response(json={"unexpected": "shape"})
    with pytest.raises(TranslateError, match="解析"):
        _call()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_minimax.py -v`
Expected: errors with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/translator/minimax.py`**

```python
import httpx

PROMPTS = {
    "auto→zh": (
        "You are a translator. Translate the user message to Simplified Chinese. "
        "Output only the translation, no explanation."
    ),
    "zh→en": (
        "You are a translator. Translate the user message to English. "
        "Output only the translation, no explanation."
    ),
}


class TranslateError(Exception):
    pass


def translate(
    text: str,
    direction: str,
    *,
    api_key: str,
    model: str,
    endpoint: str,
    timeout: float = 15.0,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": PROMPTS[direction]},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(2):
        try:
            r = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
        except httpx.RequestError as e:
            raise TranslateError(f"网络错误: {e}") from e

        if r.status_code < 400:
            try:
                return r.json()["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, ValueError) as e:
                raise TranslateError(f"响应解析失败: {r.text[:200]}") from e

        if r.status_code >= 500 and attempt == 0:
            continue

        raise TranslateError(f"HTTP {r.status_code}: {r.text[:200]}")

    raise TranslateError("unreachable")  # pragma: no cover
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_minimax.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add src/translator/minimax.py tests/test_minimax.py
git commit -m "feat(minimax): chat-completion client with 5xx retry and error parsing"
```

---

### Task 6: CLI MVP (no popup yet)

**Files:**
- Create: `src/translator/cli.py`

This task wires config → clipboard → detect → minimax. The popup is added in Task 8.
The MVP prints the translation to stdout so it can be smoke-tested without a display.

- [ ] **Step 1: Implement `src/translator/cli.py`**

```python
"""Translator CLI entry point.

Pipeline: config → read selection → detect direction → translate → display.
v1 prints to stdout; popup is wired in Task 8.
"""
import subprocess
import sys

from translator import clipboard, config, detect, minimax


def notify(message: str) -> None:
    """Best-effort GNOME notification. Silent if notify-send is missing."""
    try:
        subprocess.run(["notify-send", "Translator", message], timeout=2)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"NOTIFY: {message}", file=sys.stderr)


def main() -> int:
    try:
        cfg = config.load()
    except config.ConfigError as e:
        notify(str(e))
        return 1

    try:
        text, truncated = clipboard.read_primary()
    except clipboard.ClipboardError as e:
        notify(str(e))
        return 1

    if not text.strip():
        notify("请先选中要翻译的文字")
        return 0

    direction = detect.direction(text)

    try:
        translation = minimax.translate(text, direction, **cfg)
    except minimax.TranslateError as e:
        notify(f"翻译失败: {e}")
        return 1

    # MVP: print to stdout. Replaced by popup in Task 8.
    if truncated:
        print("[已截断到 2000 字符]")
    print(f"原文: {text}")
    print(f"译文: {translation}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Reinstall and smoke-test missing config**

```bash
pip install --user -e ".[dev]"
mv ~/.config/translator/config.toml ~/.config/translator/config.toml.bak 2>/dev/null || true
translator
echo "exit=$?"
```

Expected: notification (or stderr) about config not found; exit code 1.

- [ ] **Step 3: Smoke-test with real config (requires API key)**

```bash
mkdir -p ~/.config/translator
cp config.example.toml ~/.config/translator/config.toml
chmod 600 ~/.config/translator/config.toml
$EDITOR ~/.config/translator/config.toml   # paste real api_key
```

Then select some English text in any window so it lives in PRIMARY, and:
```bash
translator
```

Expected: stdout shows `原文: ...` and `译文: ...` in Chinese. If it does, the pipeline works end-to-end.

If you can't easily seed PRIMARY from a bash shell, use this to fake it:
```bash
echo -n "Hello, how are you?" | wl-copy --primary
translator
```

- [ ] **Step 4: Commit**

```bash
git add src/translator/cli.py
git commit -m "feat(cli): wire config → clipboard → detect → minimax pipeline"
```

---

### Task 7: GTK4 popup (`popup.py`)

**Files:**
- Create: `src/translator/popup.py`

GTK code isn't unit-tested (no display in CI). Verified manually in Task 8.

- [ ] **Step 1: Verify GTK4 bindings are installed**

```bash
sudo apt install -y python3-gi gir1.2-gtk-4.0 libnotify-bin
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 2: Implement `src/translator/popup.py`**

```python
"""GTK4 popup window for displaying translation results.

The window is positioned by the Wayland compositor; we cannot place it
at the cursor. Original text shown dim above, translation bold below.
Esc closes the window. Translation label is selectable (Ctrl+C to copy)
and a Copy button is provided as a fallback.
"""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402


def show(original: str, translation: str, truncated: bool = False) -> None:
    app = Gtk.Application(application_id="com.xgao.translator")

    def on_activate(application: Gtk.Application) -> None:
        win = Gtk.ApplicationWindow(application=application, title="Translator")
        win.set_default_size(480, 240)

        outer = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )

        if truncated:
            badge = Gtk.Label(label="⚠ 已截断到 2000 字符", xalign=0)
            badge.add_css_class("dim-label")
            outer.append(badge)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        orig_label = Gtk.Label(label=original, xalign=0, wrap=True, selectable=True)
        orig_label.add_css_class("dim-label")
        inner.append(orig_label)

        trans_label = Gtk.Label(
            label=translation, xalign=0, wrap=True, selectable=True
        )
        trans_label.add_css_class("title-3")
        inner.append(trans_label)

        scrolled.set_child(inner)
        outer.append(scrolled)

        def on_copy(_btn: Gtk.Button) -> None:
            display = Gdk.Display.get_default()
            if display is not None:
                display.get_clipboard().set(translation)

        copy_btn = Gtk.Button(label="复制译文")
        copy_btn.connect("clicked", on_copy)
        outer.append(copy_btn)

        controller = Gtk.EventControllerKey()

        def on_key(_ctrl, keyval, _keycode, _state) -> bool:
            if keyval == Gdk.KEY_Escape:
                win.close()
                return True
            return False

        controller.connect("key-pressed", on_key)
        win.add_controller(controller)

        win.set_child(outer)
        win.present()

    app.connect("activate", on_activate)
    app.run([])
```

- [ ] **Step 3: Smoke-test the popup standalone**

```bash
python3 -c "from translator.popup import show; show('Hello world', '你好世界', truncated=False)"
```

Expected: a small window opens showing `Hello world` (dim) above `你好世界` (bold). Press `Esc` to close. Click "复制译文", then paste somewhere — should paste `你好世界`.

Also test truncation flag:
```bash
python3 -c "from translator.popup import show; show('long text', 'translated', truncated=True)"
```

Expected: yellow `⚠ 已截断到 2000 字符` badge appears at top.

- [ ] **Step 4: Commit**

```bash
git add src/translator/popup.py
git commit -m "feat(popup): GTK4 result window with selectable labels and Esc to close"
```

---

### Task 8: Wire popup into CLI

**Files:**
- Modify: `src/translator/cli.py`

- [ ] **Step 1: Update `src/translator/cli.py` to call popup instead of stdout**

Replace the entire file contents with:
```python
"""Translator CLI entry point.

Pipeline: config → read selection → detect direction → translate → popup.
"""
import subprocess
import sys

from translator import clipboard, config, detect, minimax, popup


def notify(message: str) -> None:
    """Best-effort GNOME notification. Silent if notify-send is missing."""
    try:
        subprocess.run(["notify-send", "Translator", message], timeout=2)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"NOTIFY: {message}", file=sys.stderr)


def main() -> int:
    try:
        cfg = config.load()
    except config.ConfigError as e:
        notify(str(e))
        return 1

    try:
        text, truncated = clipboard.read_primary()
    except clipboard.ClipboardError as e:
        notify(str(e))
        return 1

    if not text.strip():
        notify("请先选中要翻译的文字")
        return 0

    direction = detect.direction(text)

    try:
        translation = minimax.translate(text, direction, **cfg)
    except minimax.TranslateError as e:
        popup.show(text, f"❌ {e}", truncated)
        return 1

    popup.show(text, translation, truncated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Manual end-to-end test**

```bash
echo -n "Good morning, how are you doing today?" | wl-copy --primary
translator
```

Expected: GTK popup opens, original English shown dim, Chinese translation shown bold below. Esc closes.

Test the empty-selection path:
```bash
wl-copy --primary --clear
translator
```

Expected: GNOME notification "请先选中要翻译的文字"; no popup.

Test the API-error path (temporarily put a bad key):
```bash
sed -i.bak 's/api_key = ".*"/api_key = "BAD"/' ~/.config/translator/config.toml
echo -n "test" | wl-copy --primary
translator
mv ~/.config/translator/config.toml.bak ~/.config/translator/config.toml
```

Expected: popup with `❌ HTTP 401: ...` (or similar auth error).

- [ ] **Step 3: Run all unit tests one more time**

```bash
pytest -v
```

Expected: all tests pass (28 tests total: 6 detect + 6 config + 7 clipboard + 9 minimax).

- [ ] **Step 4: Commit**

```bash
git add src/translator/cli.py
git commit -m "feat(cli): show results in GTK popup instead of stdout"
```

---

### Task 9: Install script with GNOME hotkey registration

**Files:**
- Create: `install.sh`

- [ ] **Step 1: Create `install.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Installing system dependencies..."
sudo apt install -y \
    python3-gi gir1.2-gtk-4.0 \
    wl-clipboard libnotify-bin \
    python3-pip

echo "==> Installing translator package..."
pip install --user .

TRANSLATOR_BIN="$HOME/.local/bin/translator"
if [ ! -x "$TRANSLATOR_BIN" ]; then
    echo "ERROR: $TRANSLATOR_BIN not found after install" >&2
    exit 1
fi

if ! echo ":$PATH:" | grep -q ":$HOME/.local/bin:"; then
    echo "WARNING: $HOME/.local/bin is not on PATH."
    echo "Add to your ~/.bashrc or ~/.zshrc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo "==> Creating config directory..."
CONFIG_DIR="$HOME/.config/translator"
CONFIG_FILE="$CONFIG_DIR/config.toml"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_FILE" ]; then
    cp config.example.toml "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"
    echo "    Created $CONFIG_FILE"
fi

echo "==> Registering Super+E hotkey..."
SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
KB_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
existing=$(gsettings get $SCHEMA custom-keybindings)

# Find a slot: reuse one already named 'Translator', else use the first free customN.
slot_path=""
i=0
while true; do
    path="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${i}/"
    if echo "$existing" | grep -q "$path"; then
        name=$(gsettings get "${KB_SCHEMA}:${path}" name 2>/dev/null || echo "''")
        if [ "$name" = "'Translator'" ]; then
            slot_path="$path"
            echo "    Reusing existing Translator slot: custom${i}"
            break
        fi
        i=$((i+1))
    else
        slot_path="$path"
        echo "    Using new slot: custom${i}"
        break
    fi
done

# Add to list if not present.
if ! echo "$existing" | grep -q "$slot_path"; then
    if [ "$existing" = "@as []" ]; then
        new_list="['$slot_path']"
    else
        new_list=$(echo "$existing" | sed "s|]|, '$slot_path']|")
    fi
    gsettings set $SCHEMA custom-keybindings "$new_list"
fi

gsettings set "${KB_SCHEMA}:${slot_path}" name 'Translator'
gsettings set "${KB_SCHEMA}:${slot_path}" command "$TRANSLATOR_BIN"
gsettings set "${KB_SCHEMA}:${slot_path}" binding '<Super>e'

echo
echo "Done."
echo "  1. Edit $CONFIG_FILE and paste your MiniMax API key."
echo "  2. Select text anywhere, press Super+E."
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x install.sh
```

- [ ] **Step 3: Run it and verify**

```bash
./install.sh
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```

Expected: list now contains a `customN` path that wasn't there before (or reuses one named 'Translator').

Verify the slot:
```bash
# Replace customN with the slot the script picked, e.g. custom2
gsettings list-recursively \
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom2/"
```

Expected:
```
... name 'Translator'
... command '/home/xgao/.local/bin/translator'
... binding '<Super>e'
```

- [ ] **Step 4: Test idempotency**

```bash
./install.sh
./install.sh
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```

Expected: list does not grow on repeated runs (the Translator slot is reused).

- [ ] **Step 5: End-to-end test of the hotkey**

1. Select some English text in a browser or text editor.
2. Press `Super+E`.

Expected: GTK popup with translation appears within ~1s.

- [ ] **Step 6: Commit**

```bash
git add install.sh
git commit -m "feat(install): apt deps, pip install, and idempotent Super+E registration"
```

---

### Task 10: README and final verification

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# translator

Select text, press **Super+E**, get a translation. Ubuntu 24.04 (GNOME/Wayland) + MiniMax mainland API.

## Install

```bash
./install.sh
```

This:
- installs apt deps (`python3-gi`, `gir1.2-gtk-4.0`, `wl-clipboard`, `libnotify-bin`)
- installs the `translator` command into `~/.local/bin`
- creates `~/.config/translator/config.toml` (mode 600)
- registers Super+E as a GNOME custom keybinding

After install, edit `~/.config/translator/config.toml` and paste your MiniMax API key.

## Usage

1. Select English (or Chinese) text anywhere.
2. Press `Super+E`.
3. A small popup appears with the translation. `Esc` to close, "复制译文" to copy.

Direction is auto-detected: ≥30% Chinese characters → translate to English; otherwise → translate to Chinese.

## Configuration

`~/.config/translator/config.toml`:

```toml
api_key  = "your-minimax-key"
model    = "abab6.5s-chat"
endpoint = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
```

`model` and `endpoint` are optional; defaults shown.

## Development

```bash
pip install --user -e ".[dev]"
pytest -v
```

## Limitations

- The popup is positioned by the Wayland compositor, not the application — usually centred on the active monitor.
- Some GTK4 apps don't write to the PRIMARY selection. If selection-via-Super+E doesn't work, try `Ctrl+C` first to copy then paste into PRIMARY: `wl-paste | wl-copy --primary`.
- Selections over 2000 characters are truncated.
```

- [ ] **Step 2: Run the full integration checklist from the spec**

Three manual scenarios (spec section *Testing*):

1. **English → Chinese**
   ```bash
   echo -n "The quick brown fox jumps over the lazy dog." | wl-copy --primary
   ```
   Press Super+E. Expected: popup with Chinese translation.

2. **Chinese → English**
   ```bash
   echo -n "今天天气真不错，我们去公园散步吧。" | wl-copy --primary
   ```
   Press Super+E. Expected: popup with English translation.

3. **Empty selection**
   ```bash
   wl-copy --primary --clear
   ```
   Press Super+E. Expected: GNOME notification "请先选中要翻译的文字"; no popup.

- [ ] **Step 3: Run all unit tests once more**

```bash
pytest -v
```

Expected: all 28 tests pass.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add README with install, usage, and limitations"
```

---

## Self-review notes

- All spec sections are covered: config (Task 3), clipboard (Task 4), detect (Task 2), minimax (Task 5), popup (Task 7), cli (Tasks 6+8), install (Task 9), README (Task 10).
- Type/name consistency: `read_primary() → (str, bool)`, `direction(str) → str` returning `"auto→zh"` / `"zh→en"`, `translate(...) → str`, `popup.show(original, translation, truncated)`. Names match across tasks.
- No placeholders. Every step has either complete code or a runnable command with expected output.
- TDD: detect, config, clipboard, minimax follow red→green→commit. popup and cli are integration code with manual verification (no automated GUI test).
