#!/usr/bin/env python3
"""
Generate a lightweight terminal-style demo GIF for the README.

Usage:
  python3 assets/generate-demo.py

Requires ImageMagick (magick) to be available in PATH.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


ASSETS_DIR = Path(__file__).resolve().parent
OUTPUT_GIF = ASSETS_DIR / "demo.gif"
TMP_DIR = ASSETS_DIR / ".frames"

WIDTH = 980
HEIGHT = 580
FONT = "Courier"
POINTSIZE = 18

COLORS = {
    "bg": "#0B1B26",
    "fg": "#EAF7FF",
    "dim": "#8CB7C8",
    "green": "#31D0AA",
    "yellow": "#F2C94C",
    "cyan": "#5AE0FF",
    "gray": "#7A8A99",
}


@dataclass
class Line:
    text: str
    color: str = "fg"


@dataclass
class Frame:
    lines: List[Line]
    delay_s: float


class DemoBuilder:
    def __init__(self) -> None:
        self._lines: List[Line] = []
        self._frames: List[Frame] = []

    def add_line(self, text: str, pause_s: float, color: str = "fg") -> None:
        """Append a line and capture a frame with a pause in seconds."""
        self._lines.append(Line(text=text, color=color))
        self._frames.append(Frame(lines=list(self._lines), delay_s=pause_s))

    @property
    def frames(self) -> List[Frame]:
        return self._frames


def _require_magick() -> str:
    magick = shutil.which("magick")
    if not magick:
        raise SystemExit("ImageMagick not found. Install and ensure `magick` is in PATH.")
    return magick


def _render_frame(magick: str, frame: Frame, out_path: Path) -> None:
    args = [
        magick,
        "-size",
        f"{WIDTH}x{HEIGHT}",
        f"xc:{COLORS['bg']}",
        "-font",
        FONT,
        "-pointsize",
        str(POINTSIZE),
    ]

    y = 40
    line_height = 32
    for line in frame.lines:
        color = COLORS.get(line.color, COLORS["fg"])
        args += ["-fill", color, "-draw", f"text 24,{y} '{line.text}'"]
        y += line_height

    args.append(str(out_path))
    subprocess.check_call(args)


def _build_gif(magick: str, frames: List[Frame], output: Path) -> None:
    if not frames:
        raise SystemExit("No frames to render.")

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    frame_paths: List[Path] = []
    for idx, frame in enumerate(frames, start=1):
        frame_path = TMP_DIR / f"frame{idx:02d}.png"
        _render_frame(magick, frame, frame_path)
        frame_paths.append(frame_path)

    cmd = [magick, "-loop", "0"]
    for frame, path in zip(frames, frame_paths):
        delay_cs = max(1, int(frame.delay_s * 100))
        cmd += ["-delay", str(delay_cs), str(path)]
    cmd.append(str(output))

    subprocess.check_call(cmd)


def main() -> int:
    magick = _require_magick()

    demo = DemoBuilder()
    demo.add_line("alex@terminal$ ~/Projects", 0, "dim")
    demo.add_line("->  ls", 1, "fg")
    demo.add_line("web-app  api-service  other", 2, "gray")
    demo.add_line("alex@terminal$ ~/Projects", 0, "dim")
    demo.add_line("->  cd web-app", 2, "fg")
    demo.add_line("alex@terminal$ ~/Projects/web-app", 0, "dim")
    demo.add_line("Aliases for /Users/alex/Projects/web-app:", 0, "cyan")
    demo.add_line("  start -> npm run dev", 0, "green")
    demo.add_line("  test  -> npm test", 3, "green")
    demo.add_line("alex@terminal$ ~/Projects/web-app", 0, "dim")
    demo.add_line("->  start", 1, "fg")
    demo.add_line("...dev server starting...", 2, "gray")
    demo.add_line("alex@terminal$ ~/Projects/web-app", 0, "dim")
    demo.add_line("->  cd ../other", 2, "fg")
    demo.add_line("alex@terminal$ ~/Projects/other", 0, "dim")
    demo.add_line("(no aliases here)", 2.2, "gray")

    _build_gif(magick, demo.frames, OUTPUT_GIF)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
