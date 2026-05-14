<h1 align="center">🌐 super-e-translator</h1>

<p align="center">
  <em>Select text. Hit <kbd>Super</kbd>+<kbd>E</kbd>. Get a translation.</em><br/>
  <sub>A no-friction translator for Ubuntu 24.04 (GNOME/Wayland), powered by MiniMax.</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu&logoColor=white" alt="Ubuntu"/>
  <img src="https://img.shields.io/badge/GTK-4-4A90D9?logo=gnome&logoColor=white" alt="GTK4"/>
  <img src="https://img.shields.io/badge/Wayland-supported-success" alt="Wayland"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT"/>
</p>

<p align="center">
  <!-- TODO: drop a demo gif here, e.g.: docs/demo.gif -->
  <img src="docs/demo.gif" alt="demo" width="640" onerror="this.style.display='none'"/>
</p>

---

## ✨ Why

Most desktop translators on Linux are clunky: open the app, paste text, click translate, copy back. This one is one keystroke.

## 🚀 Install

```bash
git clone https://github.com/gaoxiaowei2117/super-e-translator.git
cd super-e-translator
./install.sh
```

The installer:

- ✅ installs apt deps (`python3-gi`, `gir1.2-gtk-4.0`, `wl-clipboard`, `libnotify-bin`, `pipx`)
- ✅ installs the `translator` command into `~/.local/bin` via `pipx` (with `--system-site-packages` so the venv can use the apt-installed PyGObject)
- ✅ writes a default `~/.config/translator/config.toml` (mode 600)
- ✅ registers <kbd>Super</kbd>+<kbd>E</kbd> as a GNOME custom keybinding

After install, drop your MiniMax API key into the config:

```bash
$EDITOR ~/.config/translator/config.toml
```

## ⌨️ Usage

1. Select English (or Chinese) text **anywhere** — browser, terminal, IDE.
2. Press <kbd>Super</kbd> + <kbd>E</kbd>.
3. A small popup appears with the translation.
   - <kbd>Esc</kbd> — close
   - **"复制译文"** — copy result

Direction is auto-detected: ≥30% Chinese characters → translate **to English**; otherwise → translate **to Chinese**.

## ⚙️ Configuration

`~/.config/translator/config.toml`:

```toml
api_key  = "your-minimax-key"
model    = "MiniMax-M2.5-highspeed"
endpoint = "https://api.minimaxi.com/anthropic/v1/messages"
```

`model` and `endpoint` are optional; defaults shown. Other supported models:

| Model                       | Notes                |
|-----------------------------|----------------------|
| `MiniMax-M2.7`              | latest, most capable |
| `MiniMax-M2.7-highspeed`    | latest, faster       |
| `MiniMax-M2.5` *(default)*  | balanced             |
| `MiniMax-M2.5-highspeed`    | balanced, faster     |
| `MiniMax-M2.1`              | older                |
| `MiniMax-M2.1-highspeed`    | older, faster        |
| `MiniMax-M2`                | original             |

All go through the same Anthropic-style endpoint.

## 🧑‍💻 Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -v
```

## ⚠️ Limitations

- Popup position is controlled by the Wayland compositor — usually centered on the active monitor.
- A few GTK4 apps don't write to the PRIMARY selection. If selection-via-<kbd>Super</kbd>+<kbd>E</kbd> doesn't work, try <kbd>Ctrl</kbd>+<kbd>C</kbd> first, then `wl-paste | wl-copy --primary`.
- Selections over 2000 characters are truncated.

## 🗺️ Roadmap

- [ ] Auto-detect more language pairs (es/fr/de/ja → en/zh)
- [ ] Streaming output for long passages
- [ ] X11 fallback (currently Wayland-only)
- [ ] Custom popup theme

## 📄 License

MIT
