#!/usr/bin/env python3
"""Folder-specific aliases for your shell.

Usage:
  alias_manager.py --cwd /path/to/dir

Reads ~/.alias-manager/config.json by default and prints alias definitions
for the given cwd. Output is intended to be eval'd by the shell.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import PurePosixPath
from typing import Dict, Iterable


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
    cwd_path = PurePosixPath(cwd)
    matched: Dict[str, str] = {}
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
            matched.update(aliases)
    return matched


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    config_path = os.path.expanduser(args.config)
    if (
        config_path == DEFAULT_CONFIG
        and not os.path.exists(config_path)
        and os.path.exists(os.path.expanduser("~/.alias-manager/config.yaml"))
    ):
        config_path = os.path.expanduser("~/.alias-manager/config.yaml")
    if (
        config_path == DEFAULT_CONFIG
        and not os.path.exists(config_path)
        and os.path.exists(os.path.expanduser("~/.alias-manager/config.yml"))
    ):
        config_path = os.path.expanduser("~/.alias-manager/config.yml")

    if args.debug:
        print(f"[alias-manager] cwd: {args.cwd}", file=os.sys.stderr)
        print(f"[alias-manager] config: {config_path}", file=os.sys.stderr)

    config = _load_config(config_path, args.debug)
    aliases = _match_patterns(config, args.cwd, args.debug)
    for line in _format_aliases(aliases):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
