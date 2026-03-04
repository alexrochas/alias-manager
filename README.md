# alias-manager

Folder-specific aliases for your shell.

## How it works
- You define aliases in `~/.alias-manager/config.json` (or `config.yaml`/`config.yml`) using glob patterns.
- A zsh hook runs when you `cd`, clears previous folder aliases, and applies the ones that match the new folder.

## Example config
Create `~/.alias-manager/config.json` (or `config.yaml` / `config.yml`):

```json
{
  "/Users/alex/Projects/on-frontend/**": {
    "start": "npx yarn on-shop dev:safe",
    "test": "npx yarn test"
  },
  "/Users/alex/Projects/on-backend": {
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

## Zsh setup
Add this to your `~/.zshrc` (adjust the script path if needed):

```zsh
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
    am_output="$($am_script --cwd "$PWD")"
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
```

## Permissions
Make the script executable:

```bash
chmod +x /Users/alex.rocha/Development/alias-manager/alias_manager.py
```

## Install helper
Run the installer (creates config, installs PyYAML, prints the hook):

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
