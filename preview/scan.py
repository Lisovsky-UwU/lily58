"""Find multi-frame OLED bitmap arrays (PROGMEM x[frames][bytes]) in a QMK tree."""

import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
decl = re.compile(r"PROGMEM\s+(\w+)\s*\[\s*(\w+)\s*\]\s*\[\s*(\w+)\s*\]")
define = re.compile(r"#\s*define\s+(\w+)\s+\(?\s*(\d+)\s*\)?")

for f in sorted(root.glob("keyboards/**/*")):
    if f.suffix not in (".c", ".h") or "/lib/" in str(f):
        continue
    try:
        src = f.read_text(errors="ignore")
    except OSError:
        continue
    if "PROGMEM" not in src:
        continue
    defs = dict(define.findall(src))
    for name, frames, size in decl.findall(src):
        if name == "keymaps":
            continue
        frames = int(defs.get(frames, frames)) if str(defs.get(frames, frames)).isdigit() else frames
        size = int(defs.get(size, size)) if str(defs.get(size, size)).isdigit() else size
        if isinstance(size, int) and size >= 64:
            print(f"{f.relative_to(root)}\t{name}\t{frames}\t{size}")
