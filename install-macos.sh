#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew not found. Install it from https://brew.sh and re-run." >&2
    exit 1
fi

echo "==> Installing dependencies (brew)..."
# python-tk gives Tkinter (used by the popup); pipx for isolated install.
brew install python-tk pipx >/dev/null

# skhd was moved out of homebrew-core into the author's tap.
echo "==> Tapping koekeishiya/formulae (for skhd)..."
brew tap koekeishiya/formulae >/dev/null
echo "==> Installing skhd..."
brew install koekeishiya/formulae/skhd >/dev/null

echo "==> Ensuring pipx PATH..."
pipx ensurepath >/dev/null 2>&1 || true

echo "==> Installing translator (pipx)..."
pipx install --force . >/dev/null

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
    echo "    eval \"\$(pipx environment --path 2>/dev/null)\" || source ~/.zshrc"
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

# ---- skhd hotkey registration ----
#
# skhd matches lines like `cmd + alt - e : <command>`. We tag the lines we
# manage so re-runs are idempotent: any line ending with `# translator` or
# `# translator-image` is replaced rather than duplicated.

SKHD_DIR="$HOME/.config/skhd"
SKHD_RC="$SKHD_DIR/skhdrc"
mkdir -p "$SKHD_DIR"
touch "$SKHD_RC"

echo "==> Registering hotkeys in $SKHD_RC..."
TMP=$(mktemp)
# Drop existing translator-managed lines, keep the rest as-is.
grep -v -E '# (translator|translator-image)$' "$SKHD_RC" > "$TMP" || true
# Trim trailing blank lines so the file doesn't grow.
awk 'BEGIN{blank=0} {if($0==""){blank++} else {for(i=0;i<blank;i++)print ""; blank=0; print}}' "$TMP" > "$SKHD_RC"
rm -f "$TMP"

# Append our bindings.
[ -s "$SKHD_RC" ] && echo "" >> "$SKHD_RC"
echo "cmd + ctrl - e : $TRANSLATOR_BIN # translator" >> "$SKHD_RC"
echo "cmd + ctrl - r : $TRANSLATOR_IMAGE_BIN # translator-image" >> "$SKHD_RC"

echo "==> Starting skhd service..."
# `skhd --start-service` is idempotent — it loads the launchd plist and
# starts it. `--restart-service` reloads config without re-registering.
if skhd --start-service >/dev/null 2>&1; then
    skhd --restart-service >/dev/null 2>&1 || true
else
    # First-time install path on newer skhd: load via brew services.
    brew services start skhd >/dev/null 2>&1 || true
fi

cat <<EOF

Done.

  1. Edit $CONFIG_FILE and paste your MiniMax API key.

  2. Hotkeys (registered via skhd):
       ⌘⌃E  — translate selection
       ⌘⌃R  — interactive screenshot translate

  3. First time you press a hotkey, macOS will prompt for "Accessibility"
     permission for **skhd** (and again for the translator binary itself,
     since it needs to send ⌘C to the focused app). Grant both under
     System Settings → Privacy & Security → Accessibility.

     If a hotkey does nothing: open System Settings → Privacy & Security
     → Accessibility, make sure skhd is listed and enabled.

  Change a binding later? Edit $SKHD_RC and run:  skhd --restart-service
EOF
