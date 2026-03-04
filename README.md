# alias-manager

![alias-manager logo](logo.svg)

Folder-specific aliases for your shell.

## How it works
- You define aliases in `~/.alias-manager/config.json` (or `config.yaml`/`config.yml`) using glob patterns.
- A zsh hook runs when you `cd`, clears previous folder aliases, and applies the ones that match the new folder.

## Quick start
1. Run the installer:

```bash
/Users/alex.rocha/Development/alias-manager/install.sh --append-zshrc
```

2. Edit your config:

```json
{
  "/Users/alex/Projects/web-app/**": {
    "start": "npm run dev",
    "test": "npm test"
  },
  "/Users/alex/Projects/api-service": {
    "start": "npm run dev",
    "test": "npm test"
  }
}
```

3. Restart your shell or run `source ~/.zshrc`.
4. `cd` into a matching folder and use your aliases.

## CLI (am)
`am` edits the config for the current folder so you don't have to touch JSON manually.

```bash
am add start "npm run dev"
am remove start
am list
am open
am --help
```

Notes:
- Use `--yes` to skip confirmation prompts.
- `am add` is recursive by default (stores `/path/**`).
- Use `--no-recursive` to store the exact folder.
- Use `am list --sources` to show which patterns matched.
- Use `am remove --all` to remove all aliases for the current folder.
- Use `am remove --all-matching` to remove aliases for all matching patterns.
- Config security checks are enabled by default; use `--allow-insecure-config` to bypass.

## Example config
Create `~/.alias-manager/config.json` (or `config.yaml` / `config.yml`):

```json
{
  "/Users/alex/Projects/web-app/**": {
    "start": "npm run dev",
    "test": "npm test"
  },
  "/Users/alex/Projects/api-service": {
    "start": "npm run dev",
    "test": "npm test"
  }
}
```

Notes:
- `*` matches a single path segment.
- `**` matches any number of segments (subfolders).
- Exact paths (no glob) only match that exact folder.
- `~` is supported in patterns and the config path.
  - `/**` also matches the base folder itself (e.g. `/path/**` matches `/path`).

## Example session
```bash
cd ~/Projects/web-app
# Printed automatically on entry (with color):
# Aliases for /Users/alex/Projects/web-app:
#   start -> npm run dev
#   test  -> npm test
```

Move to another folder:

```bash
cd ~/Projects/other
# No aliases are printed, and any previously applied aliases are cleared.
```

## Demo
![alias-manager demo](assets/demo.gif)

## Prompt indicator (oh-my-zsh)
If you want a subtle marker in your prompt when a folder has aliases, add:

```zsh
# Add to ~/.zshrc after alias-manager setup
am_prompt() {
  local out
  out="$(am prompt --cwd "$PWD" --symbol "⚙")"
  if [[ -n "$out" ]]; then
    echo "%F{cyan}${out}%f"
  fi
}

# Example: show it on the right side
RPROMPT='$(am_prompt)'
```

## Zsh setup
Add this to your `~/.zshrc`:

```zsh
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

# Run after each directory change.
autoload -Uz add-zsh-hook
add-zsh-hook chpwd __am_apply_aliases

# Run once for the initial shell.
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
```

## Permissions
Make the script executable:

```bash
chmod +x /Users/alex.rocha/Development/alias-manager/alias_manager.py
```

## Install helper
Run the installer (creates config, installs the CLI into `~/.alias-manager/bin`, prints the hook):

```bash
/Users/alex.rocha/Development/alias-manager/install.sh
```

Append the hook automatically:

```bash
/Users/alex.rocha/Development/alias-manager/install.sh --append-zshrc
```


## Troubleshooting
- If nothing happens, ensure the config file exists and is valid JSON (or YAML).
- If aliases don't update, make sure the hook is in your `~/.zshrc` and restart the shell.
- For YAML config, install PyYAML: `pip install pyyaml`
- To see which patterns matched, run the script with `--debug`:
  - Example: `/Users/alex.rocha/Development/alias-manager/alias_manager.py --cwd "$PWD" --debug`
- To print a list of aliases when you enter a folder, use `--print` in the hook.
  - Output is colorized by default.

## Security notes
- Config files are rejected if they are symlinks, not owned by you, or group/world writable.
- Alias names must be safe identifiers (`letters`, `numbers`, `_`, `-`).
- Use `--allow-insecure-config` only if you understand the risks.
- To fix permissions: `chmod 600 ~/.alias-manager/config.json`

## License
PolyForm Noncommercial 1.0.0 — forking/cloning/modifying is allowed, but commercial use is not.
