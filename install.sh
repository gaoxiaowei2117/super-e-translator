#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Installing system dependencies (apt)..."
sudo apt install -y \
    python3-gi gir1.2-gtk-4.0 \
    wl-clipboard libnotify-bin \
    pipx

echo "==> Ensuring pipx PATH..."
pipx ensurepath >/dev/null 2>&1 || true

echo "==> Installing translator (pipx with system-site-packages for gi)..."
# --system-site-packages lets the isolated venv import the apt-installed `gi`
# (PyGObject is not pip-installable on Ubuntu 24.04 without GTK build deps).
# --force makes re-runs idempotent.
pipx install --system-site-packages --force .

TRANSLATOR_BIN="$HOME/.local/bin/translator"
if [ ! -x "$TRANSLATOR_BIN" ]; then
    echo "ERROR: $TRANSLATOR_BIN not found after install" >&2
    exit 1
fi

if ! echo ":$PATH:" | grep -q ":$HOME/.local/bin:"; then
    echo "NOTE: $HOME/.local/bin is not on PATH yet. Open a new shell or run:"
    echo "    source ~/.bashrc"
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
