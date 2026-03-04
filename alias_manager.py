#!/usr/bin/env python3
"""Folder-specific aliases for your shell.

Usage:
  alias_manager.py --cwd /path/to/dir
  alias_manager.py add <name> "<command>"
  alias_manager.py remove <name> | --all
  alias_manager.py list [--sources]
  alias_manager.py open
  alias_manager.py prompt

Reads ~/.alias-manager/config.json by default and prints alias definitions
for the given cwd. Output is intended to be eval'd by the shell.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_CONFIG = os.path.expanduser("~/.alias-manager/config.json")


def _load_config(path: str, debug: bool) -> Dict[str, Dict[str, str]]:
    if not os.path.exists(path):
        if debug:
            print(f"[alias-manager] config not found: {path}", file=os.sys.stderr)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            if path.endswith((".yaml", ".yml")):
                try:
                    import yaml  # type: ignore
                except Exception:
                    if debug:
                        print(
                            "[alias-manager] PyYAML not available; cannot read YAML config",
                            file=os.sys.stderr,
                        )
                    return {}
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        if debug:
            print(f"[alias-manager] failed to parse config: {path}", file=os.sys.stderr)
        return {}
    if not isinstance(data, dict):
        if debug:
            print("[alias-manager] config root is not an object", file=os.sys.stderr)
        return {}

    clean: Dict[str, Dict[str, str]] = {}
    for pattern, aliases in data.items():
        if not isinstance(pattern, str) or not isinstance(aliases, dict):
            continue
        expanded_pattern = os.path.expanduser(pattern)
        clean_aliases: Dict[str, str] = {}
        for name, cmd in aliases.items():
            if isinstance(name, str) and isinstance(cmd, str):
                clean_aliases[name] = cmd
        if clean_aliases:
            clean[expanded_pattern] = clean_aliases
    return clean


def _match_patterns(
    config: Dict[str, Dict[str, str]], cwd: str, debug: bool
) -> Dict[str, str]:
    matched, _sources = _match_patterns_with_sources(config, cwd, debug)
    return matched


def _match_patterns_with_sources(
    config: Dict[str, Dict[str, str]], cwd: str, debug: bool
) -> Tuple[Dict[str, str], List[str]]:
    cwd_path = PurePosixPath(cwd)
    matched: Dict[str, str] = {}
    sources: List[str] = []
    for pattern, aliases in config.items():
        try:
            is_match = cwd_path.match(pattern)
            if not is_match and pattern.endswith("/**"):
                base = pattern[:-3].rstrip("/")
                if base:
                    is_match = cwd_path.match(base) or str(cwd_path) == base
        except Exception:
            is_match = False
        if debug:
            verdict = "matched" if is_match else "no match"
            print(f"[alias-manager] {verdict}: {pattern}", file=os.sys.stderr)
        if is_match:
            sources.append(pattern)
            matched.update(aliases)
    return matched, sources


def _format_aliases(aliases: Dict[str, str]) -> Iterable[str]:
    names: list[str] = []
    for name, cmd in aliases.items():
        if not name:
            continue
        quoted_cmd = shlex.quote(cmd)
        yield f"alias {name}={quoted_cmd}"
        names.append(name)
    if names:
        joined = " ".join(names)
        yield f"__AM_ACTIVE_ALIASES={shlex.quote(joined)}"
    else:
        yield "__AM_ACTIVE_ALIASES="

def _format_pretty(aliases: Dict[str, str], cwd: str) -> Iterable[str]:
    if not aliases:
        return []
    # ANSI colors (inspired by lsd-style vivid output)
    c_reset = "\\033[0m"
    c_header = "\\033[1;36m"  # bold cyan
    c_name = "\\033[1;33m"  # bold yellow
    c_arrow = "\\033[2;37m"  # dim gray
    c_cmd = "\\033[0;32m"  # green

    lines = [f"{c_header}Aliases for {cwd}:{c_reset}"]
    for name, cmd in aliases.items():
        lines.append(f"  {c_name}{name}{c_reset} {c_arrow}->{c_reset} {c_cmd}{cmd}{c_reset}")
    return [f"printf '%b\\n' {shlex.quote(line)}" for line in lines]


def _resolve_config_path(config_arg: str) -> str:
    config_path = os.path.expanduser(config_arg)
    if (
        config_path == DEFAULT_CONFIG
        and not os.path.exists(config_path)
        and os.path.exists(os.path.expanduser("~/.alias-manager/config.yaml"))
    ):
        return os.path.expanduser("~/.alias-manager/config.yaml")
    if (
        config_path == DEFAULT_CONFIG
        and not os.path.exists(config_path)
        and os.path.exists(os.path.expanduser("~/.alias-manager/config.yml"))
    ):
        return os.path.expanduser("~/.alias-manager/config.yml")
    return config_path


def _save_config(path: str, data: Dict[str, Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # type: ignore
        except Exception:
            raise SystemExit("PyYAML not available; cannot write YAML config.")
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")


def _to_config_key(path: str, recursive: bool) -> str:
    abs_path = os.path.abspath(os.path.expanduser(path))
    home = os.path.expanduser("~")
    if abs_path.startswith(home + os.sep):
        key = "~" + abs_path[len(home) :]
    else:
        key = abs_path
    if recursive and not key.endswith("/**"):
        key = key.rstrip("/") + "/**"
    return key


def _confirm(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    reply = input(f"{prompt} [y/N] ").strip().lower()
    return reply in {"y", "yes"}


def _cmd_add(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path, args.debug)

    if args.no_recursive:
        args.recursive = False
    key = _to_config_key(args.cwd, args.recursive)
    aliases = config.get(key, {})

    if args.name in aliases and aliases[args.name] != args.command:
        if not _confirm(
            f"Alias '{args.name}' already exists for {key}. Update?",
            args.yes,
        ):
            print("Cancelled.")
            return 1

    aliases[args.name] = args.command
    config[key] = aliases
    _save_config(config_path, config)
    print(f"Saved alias '{args.name}' for {key}.")
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path, args.debug)

    if args.no_recursive:
        args.recursive = False
    key = _to_config_key(args.cwd, args.recursive)
    aliases = config.get(key, {})
    if args.all_matching:
        matched, sources = _match_patterns_with_sources(config, args.cwd, args.debug)
        if not sources:
            print("No matching patterns for this folder.")
            return 1
        if not _confirm(
            f"Remove ALL aliases from {len(sources)} matching pattern(s)?",
            args.yes,
        ):
            print("Cancelled.")
            return 1
        for pattern in sources:
            config.pop(pattern, None)
        _save_config(config_path, config)
        print(f"Removed all aliases from {len(sources)} pattern(s).")
        return 0
    if args.all:
        if not aliases:
            print(f"No aliases found for {key}.")
            return 1
        if not _confirm(f"Remove ALL aliases for {key}?", args.yes):
            print("Cancelled.")
            return 1
        config.pop(key, None)
        _save_config(config_path, config)
        print(f"Removed all aliases for {key}.")
        return 0
    if not args.name:
        print("Alias name is required unless you use --all or --all-matching.")
        return 1
    if args.name not in aliases:
        print(f"Alias '{args.name}' not found for {key}.")
        return 1

    cmd = aliases[args.name]
    if not _confirm(f"Remove '{args.name}' -> '{cmd}' from {key}?", args.yes):
        print("Cancelled.")
        return 1

    del aliases[args.name]
    if aliases:
        config[key] = aliases
    else:
        config.pop(key, None)
    _save_config(config_path, config)
    print(f"Removed alias '{args.name}' from {key}.")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path, args.debug)
    aliases, sources = _match_patterns_with_sources(config, args.cwd, args.debug)
    if not aliases:
        print("No aliases for this folder.")
        return 0
    for name, cmd in aliases.items():
        print(f"{name} -> {cmd}")
    if args.sources and sources:
        print("")
        print("Matched patterns:")
        for pattern in sources:
            print(f"- {pattern}")
    return 0


def _cmd_open(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    editor = os.environ.get("EDITOR", "vi")
    return subprocess.call([editor, config_path])


def _cmd_prompt(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(args.config)
    config = _load_config(config_path, args.debug)
    aliases = _match_patterns(config, args.cwd, args.debug)
    if aliases:
        print(args.symbol, end="")
    return 0

def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--cwd", default=os.getcwd())
    common.add_argument("--config", default=DEFAULT_CONFIG)
    common.add_argument("--debug", action="store_true")

    parser = argparse.ArgumentParser()
    parser.add_argument("--print", action="store_true")
    for action in common._actions:
        if action.dest not in {"help"}:
            parser._add_action(action)

    subparsers = parser.add_subparsers(dest="command")

    add_p = subparsers.add_parser(
        "add", help="Add or update an alias for this folder", parents=[common]
    )
    add_p.add_argument("name")
    add_p.add_argument("command")
    add_p.add_argument("--yes", action="store_true")
    add_p.add_argument("--no-recursive", action="store_true", help="Use exact folder")
    add_p.set_defaults(recursive=True)
    add_p.set_defaults(func=_cmd_add)

    rm_p = subparsers.add_parser(
        "remove", help="Remove an alias for this folder", parents=[common]
    )
    rm_p.add_argument("name", nargs="?")
    rm_p.add_argument("--yes", action="store_true")
    rm_p.add_argument("--all", action="store_true", help="Remove all aliases for this folder")
    rm_p.add_argument(
        "--all-matching",
        action="store_true",
        help="Remove all aliases from every matching pattern",
    )
    rm_p.add_argument("--no-recursive", action="store_true", help="Use exact folder")
    rm_p.set_defaults(recursive=True)
    rm_p.set_defaults(func=_cmd_remove)

    ls_p = subparsers.add_parser(
        "list", help="List aliases for this folder", parents=[common]
    )
    ls_p.add_argument("--sources", action="store_true", help="Show matched patterns")
    ls_p.set_defaults(func=_cmd_list)

    open_p = subparsers.add_parser(
        "open", help="Open config in $EDITOR", parents=[common]
    )
    open_p.set_defaults(func=_cmd_open)

    prompt_p = subparsers.add_parser(
        "prompt", help="Output a prompt symbol if aliases exist", parents=[common]
    )
    prompt_p.add_argument("--symbol", default="am")
    prompt_p.set_defaults(func=_cmd_prompt)

    args = parser.parse_args()

    if args.command:
        return args.func(args)

    config_path = _resolve_config_path(args.config)

    if args.debug:
        print(f"[alias-manager] cwd: {args.cwd}", file=os.sys.stderr)
        print(f"[alias-manager] config: {config_path}", file=os.sys.stderr)

    config = _load_config(config_path, args.debug)
    aliases = _match_patterns(config, args.cwd, args.debug)
    for line in _format_aliases(aliases):
        print(line)
    if args.print:
        for line in _format_pretty(aliases, args.cwd):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
