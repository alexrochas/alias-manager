#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.alias-manager"
CONFIG_JSON="$CONFIG_DIR/config.json"
INSTALL_BIN="$CONFIG_DIR/bin"
ZSHRC_PATH="$HOME/.zshrc"
DO_APPEND=""

for arg in "$@"; do
  case "$arg" in
    --append-zshrc) DO_APPEND="1" ;;
  esac
done

mkdir -p "$CONFIG_DIR"
mkdir -p "$INSTALL_BIN"

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

chmod 600 "$CONFIG_JSON" 2>/dev/null || true

cp "$SCRIPT_DIR/alias_manager.py" "$INSTALL_BIN/alias_manager.py"
cp "$SCRIPT_DIR/bin/am" "$INSTALL_BIN/am"
chmod +x "$INSTALL_BIN/alias_manager.py" "$INSTALL_BIN/am"

echo ""
echo "Add this to your ~/.zshrc (adjust path if needed):"
HOOK_CONTENT=$(cat <<'ZSH'
# alias-manager
export PATH="$HOME/.alias-manager/bin:$PATH"

__am_apply_aliases() {
  # Clear previously applied aliases.
  if [[ -n "$__AM_ACTIVE_ALIASES" ]]; then
    for a in ${(z)__AM_ACTIVE_ALIASES}; do
      unalias "$a" 2>/dev/null
    done
  fi
  __AM_ACTIVE_ALIASES=""

  # Apply aliases for current folder.
  if command -v am >/dev/null 2>&1; then
    local am_output
    am_output="$(am --cwd "$PWD" --print)"
    if [[ -n "$am_output" ]]; then
      eval "$am_output"
    fi
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd __am_apply_aliases
__am_apply_aliases

# Optional: show a prompt marker when aliases exist in the current folder.
# Enable by adding: RPROMPT='$(am_prompt)'
am_prompt() {
  local out
  out="$(am prompt --cwd "$PWD" --symbol "⚙")"
  if [[ -n "$out" ]]; then
    echo "%F{cyan}${out}%f"
  fi
}
ZSH
)
echo "$HOOK_CONTENT"

if [[ -n "$DO_APPEND" ]]; then
  echo ""
  echo "Appending hook to $ZSHRC_PATH..."
  {
    echo ""
    echo "$HOOK_CONTENT"
  } >> "$ZSHRC_PATH"
  echo "Done."
  echo "Restart your shell or run: source \"$ZSHRC_PATH\""
fi
