#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

case "$(uname -s)" in
    Linux*)   exec ./install-linux.sh "$@" ;;
    Darwin*)  exec ./install-macos.sh "$@" ;;
    *)
        echo "Unsupported OS: $(uname -s). Supported: Linux, macOS." >&2
        exit 1
        ;;
esac
