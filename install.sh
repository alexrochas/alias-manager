#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.alias-manager"
CONFIG_JSON="$CONFIG_DIR/config.json"
ZSHRC_PATH="$HOME/.zshrc"
DO_APPEND="${1:-}"

mkdir -p "$CONFIG_DIR"

if [[ ! -f "$CONFIG_JSON" ]]; then
  if [[ -f "$SCRIPT_DIR/config.example.json" ]]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_JSON"
    echo "Created: $CONFIG_JSON (from example)"
  else
    echo "No example config found. Create $CONFIG_JSON manually."
  fi
else
  echo "Config exists: $CONFIG_JSON"
fi

chmod +x "$SCRIPT_DIR/alias_manager.py"

if command -v python3 >/dev/null 2>&1; then
  echo "Installing PyYAML (for YAML config support)..."
  python3 -m pip install --break-system-packages --user pyyaml
else
  echo "python3 not found; skipping PyYAML install."
fi

echo ""
echo "Add this to your ~/.zshrc (adjust path if needed):"
HOOK_CONTENT=$(cat <<'ZSH'
# alias-manager
__am_apply_aliases() {
  local am_script="/Users/alex.rocha/Development/alias-manager/alias_manager.py"

  # Clear previously applied aliases.
  if [[ -n "$__AM_ACTIVE_ALIASES" ]]; then
    for a in ${(z)__AM_ACTIVE_ALIASES}; do
      unalias "$a" 2>/dev/null
    done
  fi
  __AM_ACTIVE_ALIASES=""

  # Apply aliases for current folder.
  if [[ -x "$am_script" ]]; then
    local am_output
    am_output="$($am_script --cwd "$PWD" --print)"
    if [[ -n "$am_output" ]]; then
      eval "$am_output"
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd __am_apply_aliases
__am_apply_aliases
ZSH
)
echo "$HOOK_CONTENT"

if [[ "$DO_APPEND" == "--append-zshrc" ]]; then
  echo ""
  echo "Appending hook to $ZSHRC_PATH..."
  {
    echo ""
    echo "$HOOK_CONTENT"
  } >> "$ZSHRC_PATH"
  echo "Done."
  echo "Restart your shell or run: source \"$ZSHRC_PATH\""
fi
