"""Extract OLED frame arrays from QMK sources into JSON: {id: {src, name, frames: [[bytes]]}}."""

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
scan = Path(sys.argv[2])
out = Path(sys.argv[3])

num = re.compile(r"0[xX][0-9a-fA-F]+|\b\d+\b")


def block_after(src, start):
    """Return text of the balanced {...} block starting at the first '{' after start."""
    i = src.index("{", start)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i + 1 : j]
    raise ValueError("unbalanced")


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


result = {}
for line in scan.read_text().splitlines():
    path, name, frames, size = line.split("\t")
    src = strip_comments((root / path).read_text(errors="ignore"))
    m = re.search(r"PROGMEM\s+" + name + r"\s*\[", src)
    body = block_after(src, m.end())
    frame_bodies = re.findall(r"\{([^{}]*)\}", body)
    data = [[int(x, 0) & 0xFF for x in num.findall(fb)] for fb in frame_bodies]
    result[f"{path}::{name}"] = {"src": path, "name": name, "size": int(size), "frames": data}
    print(path, name, [len(d) for d in data])

out.write_text(json.dumps(result))
