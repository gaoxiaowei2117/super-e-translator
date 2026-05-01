# translator

Select text, press **Super+E**, get a translation. Ubuntu 24.04 (GNOME/Wayland) + MiniMax mainland API.

## Install

```bash
./install.sh
```

This:
- installs apt deps (`python3-gi`, `gir1.2-gtk-4.0`, `wl-clipboard`, `libnotify-bin`, `pipx`)
- installs the `translator` command into `~/.local/bin` via pipx (with `--system-site-packages` so the venv can use apt-installed PyGObject)
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
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -v
```

## Limitations

- The popup is positioned by the Wayland compositor, not the application — usually centred on the active monitor.
- Some GTK4 apps don't write to the PRIMARY selection. If selection-via-Super+E doesn't work, try `Ctrl+C` first then: `wl-paste | wl-copy --primary`.
- Selections over 2000 characters are truncated.
