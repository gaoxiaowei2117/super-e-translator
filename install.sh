#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Installing system dependencies (apt)..."
sudo apt install -y \
    python3-gi gir1.2-gtk-4.0 \
    wl-clipboard libnotify-bin \
    flameshot \
    pipx

echo "==> Ensuring pipx PATH..."
pipx ensurepath >/dev/null 2>&1 || true

echo "==> Installing translator (pipx with system-site-packages for gi)..."
# --system-site-packages lets the isolated venv import the apt-installed `gi`.
# --force makes re-runs idempotent.
pipx install --system-site-packages --force .

TRANSLATOR_BIN="$HOME/.local/bin/translator"
TRANSLATOR_IMAGE_BIN="$HOME/.local/bin/translator-image"
for bin in "$TRANSLATOR_BIN" "$TRANSLATOR_IMAGE_BIN"; do
    if [ ! -x "$bin" ]; then
        echo "ERROR: $bin not found after install" >&2
        exit 1
    fi
done

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

# ---- GNOME custom-keybinding registration ----

SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
KB_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"

# Register a single binding by name. Reuses existing slot with the same name,
# else picks the first free customN. Updates the parent custom-keybindings list.
# Args: $1=name  $2=command  $3=binding (e.g. '<Super>e')
register_binding() {
    local name="$1" command="$2" binding="$3"
    local existing slot_path path i found
    existing=$(gsettings get $SCHEMA custom-keybindings)

    slot_path=""
    i=0
    while true; do
        path="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${i}/"
        if echo "$existing" | grep -q "$path"; then
            found=$(gsettings get "${KB_SCHEMA}:${path}" name 2>/dev/null || echo "''")
            if [ "$found" = "'$name'" ]; then
                slot_path="$path"
                echo "    [$name] reusing custom${i}"
                break
            fi
            i=$((i+1))
        else
            slot_path="$path"
            echo "    [$name] using new slot custom${i}"
            break
        fi
    done

    if ! echo "$existing" | grep -q "$slot_path"; then
        local new_list
        if [ "$existing" = "@as []" ]; then
            new_list="['$slot_path']"
        else
            new_list=$(echo "$existing" | sed "s|]|, '$slot_path']|")
        fi
        gsettings set $SCHEMA custom-keybindings "$new_list"
    fi

    gsettings set "${KB_SCHEMA}:${slot_path}" name "$name"
    gsettings set "${KB_SCHEMA}:${slot_path}" command "$command"
    gsettings set "${KB_SCHEMA}:${slot_path}" binding "$binding"
}

echo "==> Registering hotkeys..."
register_binding 'Translator' "$TRANSLATOR_BIN" '<Super>e'
register_binding 'Translator-Image' "$TRANSLATOR_IMAGE_BIN" '<Super>r'

echo
echo "Done."
echo "  1. Edit $CONFIG_FILE and paste your MiniMax API key (if not already set)."
echo "  2. Select text and press Super+E       — translate selection."
echo "  3. Press Super+R                       — interactive screenshot translate."
