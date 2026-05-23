<h1 align="center">🌐 super-e-translator</h1>

<p align="center">
  <em>Select text. Hit a hotkey. Get a translation.</em><br/>
  <sub>A no-friction translator for Ubuntu (GNOME/Wayland) and macOS, powered by MiniMax.</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu&logoColor=white" alt="Ubuntu"/>
  <img src="https://img.shields.io/badge/macOS-13%2B-000000?logo=apple&logoColor=white" alt="macOS"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT"/>
</p>

---

## ✨ Why

Most desktop translators are clunky: open the app, paste text, click translate, copy back. This one is one keystroke.

## 🚀 Install

```bash
git clone https://github.com/gaoxiaowei2117/super-e-translator.git
cd super-e-translator
./install.sh
```

`install.sh` auto-detects your OS and dispatches to `install-linux.sh` or `install-macos.sh`.

After install, drop your MiniMax API key into the config:

```bash
$EDITOR ~/.config/translator/config.toml
```

### Ubuntu (GNOME/Wayland)

The Linux installer:

- ✅ installs apt deps (`python3-gi`, `gir1.2-gtk-4.0`, `wl-clipboard`, `libnotify-bin`, `gnome-screenshot`, `pipx`)
- ✅ installs the `translator` command into `~/.local/bin` via `pipx` (with `--system-site-packages` so the venv can use the apt-installed PyGObject)
- ✅ registers <kbd>Super</kbd>+<kbd>E</kbd> (text) and <kbd>Super</kbd>+<kbd>R</kbd> (screenshot) as GNOME custom keybindings via `gsettings`

### macOS

The macOS installer:

- ✅ installs `python-tk` + `pipx` from Homebrew, and `skhd` from the `koekeishiya/formulae` tap (Tkinter for the popup, skhd for global hotkeys — no GTK needed)
- ✅ installs `translator` and `translator-image` into `~/.local/bin` via `pipx`
- ✅ writes <kbd>⌘⌃E</kbd> and <kbd>⌘⌃R</kbd> bindings into `~/.config/skhd/skhdrc` and starts the skhd launchd service

The first time you press a hotkey, macOS prompts for **Accessibility** permission — twice:

1. For **skhd**, so it can listen for the global hotkey.
2. For the **translator** binary, so it can send ⌘C to the focused app to grab your selection.

Grant both under *System Settings → Privacy & Security → Accessibility*. After that, hotkeys work everywhere.

To change a binding later, edit `~/.config/skhd/skhdrc` and run `skhd --restart-service`.

(<kbd>⌘E</kbd> alone is "Use Selection for Find" in most apps and <kbd>⌘⌥E</kbd> clashes with a few pro apps' bindings, so we default to <kbd>⌘⌃E</kbd> — almost nothing uses it.)

## ⌨️ Usage

1. Select English (or Chinese) text **anywhere** — browser, terminal, IDE.
2. Press your hotkey (<kbd>Super</kbd>+<kbd>E</kbd> on Linux / <kbd>⌘⌃E</kbd> on macOS).
3. A small popup appears with the translation.
   - <kbd>Esc</kbd> — close
   - **"复制译文"** — copy result

Direction is auto-detected: ≥30% Chinese characters → translate **to English**; otherwise → translate **to Chinese**.

For a single English word, you get a dictionary entry (IPA + POS-grouped meanings) instead of a sentence translation.

For images: press <kbd>Super</kbd>+<kbd>R</kbd> (Linux) / <kbd>⌘⌃R</kbd> (macOS), drag-select a region, get a translation of the text inside.

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

Tests cover both Linux and macOS backends — the platform-specific bits dispatch via `sys.platform` and each backend is tested independently.

## ⚠️ Limitations

- **Linux**: popup position is controlled by the Wayland compositor — usually centered on the active monitor. A few GTK4 apps don't write to the PRIMARY selection; if selection-via-hotkey doesn't work, try <kbd>Ctrl</kbd>+<kbd>C</kbd> first.
- **macOS**: requires Accessibility permission for the host process (Shortcuts/Terminal/skhd) so the script can dispatch ⌘C to grab your selection. Granted once, persists.
- Selections over 2000 characters are truncated.

## 🗺️ Roadmap

- [ ] Auto-detect more language pairs (es/fr/de/ja → en/zh)
- [ ] Streaming output for long passages
- [ ] X11 fallback on Linux (currently Wayland-only)
- [ ] Windows port
- [ ] Custom popup theme

## 📄 License

MIT
