# Translator — Design Spec

Date: 2026-05-01
Status: Approved (pending implementation plan)

## Goal

A global hotkey on Ubuntu 24.04 (GNOME/Wayland) that translates currently-selected
text and shows the result in a small popup window. Powered by the MiniMax chat
completion API (mainland endpoint).

## User flow

1. User selects text in any application (browser, editor, terminal, PDF reader…).
2. User presses **`Super+E`**.
3. A small popup window appears showing original text and translation.
4. User reads it, optionally `Ctrl+C` to copy the translation, presses `Esc` to close.

Direction is auto-detected: if the selection contains ≥30% Chinese characters,
translate to English; otherwise translate to Chinese.

## Architecture

Single Python 3 CLI entry point (`translator`), invoked fresh on every hotkey
press by a GNOME custom keybinding. No long-running daemon in v1.

```
[Super+E pressed]
       │
       ▼
GNOME custom-keybinding executes `translator`
       │
       ▼
┌──────────────────────────────────────────┐
│ translator/cli.py (entry point)          │
│   1. read PRIMARY selection              │
│   2. detect direction                    │
│   3. call MiniMax API                    │
│   4. open GTK popup with result          │
└──────────────────────────────────────────┘
```

## Modules

| Module                  | Responsibility                                                                          |
|-------------------------|-----------------------------------------------------------------------------------------|
| `translator/cli.py`     | Entry point. Wires the pipeline. Handles top-level errors via notifications.            |
| `translator/clipboard.py` | Wrap `wl-paste --primary --no-newline`. Detect empty selection. Truncate at 2000 chars. |
| `translator/detect.py`  | Count CJK code points; return `"zh→en"` or `"auto→zh"`.                                 |
| `translator/minimax.py` | MiniMax client. Build chat-completion request, parse response, handle HTTP errors.      |
| `translator/popup.py`   | GTK4 window: shows original + translation, supports Ctrl+C and Esc.                     |
| `translator/config.py`  | Load `~/.config/translator/config.toml`. Validate required keys.                        |

Each module is small (target <150 lines) with a single responsibility, importable
and testable in isolation.

## Configuration

File: `~/.config/translator/config.toml`, mode `0600`.

```toml
api_key  = "your-minimax-key"
model    = "abab6.5s-chat"
endpoint = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
```

`api_key` is required; `model` and `endpoint` have the defaults shown above.

## MiniMax API call

Endpoint: `POST https://api.minimaxi.com/v1/text/chatcompletion_v2`
Headers: `Authorization: Bearer <api_key>`, `Content-Type: application/json`.

Body (translate-to-Chinese example):
```json
{
  "model": "abab6.5s-chat",
  "messages": [
    {"role": "system", "content": "You are a translator. Translate the user message to Simplified Chinese. Output only the translation, no explanation."},
    {"role": "user",   "content": "<selected text>"}
  ],
  "temperature": 0.3,
  "max_tokens": 2048
}
```

System prompt swaps to English direction when source is Chinese.

Translation is read from `choices[0].message.content`.

## Popup window (GTK4)

- Plain `Gtk.Window`, not modal, decorated, ~480×240 default size.
- Two `Gtk.Label`s: original (dim) on top, translation (bold, selectable) below.
- Close on `Escape` key.
- Translation label is `selectable=True`; standard `Ctrl+C` works on selected text.
- A small "Copy" button as a fallback for users who want one click.
- Position: compositor-decided. **On Wayland the application cannot place a
  window at the cursor.** v1 accepts whatever GNOME chooses (typically center of
  active monitor).

## Error handling

| Situation                       | Behaviour                                                       |
|---------------------------------|------------------------------------------------------------------|
| PRIMARY selection empty         | `notify-send` "请先选中要翻译的文字"; exit 0.                     |
| Selection > 2000 chars          | Truncate; popup shows badge "已截断 N → 2000 字符".               |
| Config missing / `api_key` empty | `notify-send` with the path to expected config file; exit 1.    |
| Network / DNS error             | Popup with the error message and "请检查网络".                    |
| HTTP 4xx (auth, quota)          | Popup with status code and MiniMax error message.                |
| HTTP 5xx                        | One retry after 1s; if still failing, popup with error.          |
| Malformed JSON response         | Popup with "响应解析失败" and the raw first 200 chars for debug.   |

No silent failures. Every error path either ends in a popup or a notification.

## Installation

`install.sh` does, in order:

1. `apt install -y python3-gi gir1.2-gtk-4.0 wl-clipboard libnotify-bin python3-pip`
2. `pip install --user .` (installs `translator` command into `~/.local/bin`)
3. Verify `~/.local/bin` is on `PATH`; warn if not.
4. Create `~/.config/translator/config.toml` from `config.example.toml` if missing.
5. Append a new entry to GNOME `custom-keybindings`:
   - Find next free slot (`custom0`, `custom1`, … already taken → use next).
   - Set `name="Translator"`, `command="<full path>/translator"`, `binding="<Super>e"`.
   - Update the parent `custom-keybindings` list to include the new path.
6. Print "Done. Select text and press Super+E."

The script is idempotent: if a keybinding named "Translator" already exists, it
updates rather than appending.

## Dependencies

- System: `python3-gi`, `gir1.2-gtk-4.0`, `wl-clipboard`, `libnotify-bin`.
- Python: `httpx` (only). `tomllib` is stdlib in 3.11+; Ubuntu 24.04 ships 3.12.

## Testing

Unit tests (`pytest`):
- `test_detect.py` — Chinese ratio threshold around boundary cases (pure English,
  pure Chinese, mixed at 29% / 31%, empty).
- `test_clipboard.py` — Mock subprocess; verify empty handling, truncation,
  `wl-paste` not installed error.
- `test_minimax.py` — Mock httpx; verify request shape, response parsing, error
  paths for 4xx/5xx/network.
- `test_config.py` — Missing file, missing key, malformed TOML, mode-600 check.

GTK code in `popup.py` is not unit-tested (would need a display). Covered by manual
integration testing.

Manual integration tests (3 scenarios, run once before declaring done):
1. English selection → popup shows Chinese translation.
2. Chinese selection → popup shows English translation.
3. No selection → notification appears, no popup.

## Out of scope (v1)

- Window positioning at cursor (Wayland limitation).
- Streaming/incremental output.
- Multi-language target picker (English ↔ Chinese only).
- History / past-translation panel.
- Daemon mode for sub-100ms response.
- Any GUI for editing config — edit the TOML file directly.

These can be revisited if v1 ships and the user wants more.

## File layout

```
translator/
├── docs/
│   └── superpowers/specs/2026-05-01-translator-design.md
├── src/translator/
│   ├── __init__.py
│   ├── cli.py
│   ├── clipboard.py
│   ├── config.py
│   ├── detect.py
│   ├── minimax.py
│   └── popup.py
├── tests/
│   ├── test_clipboard.py
│   ├── test_config.py
│   ├── test_detect.py
│   └── test_minimax.py
├── config.example.toml
├── install.sh
├── pyproject.toml
└── README.md
```
