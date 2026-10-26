"""Pack frames + firmware font into the vertical preview page (replaces /*DATA*/null in template_v.html)."""

import base64
import json
import re

pick = json.load(open("pick.json"))
girl = json.load(open("../sprites/girl/girl_v.json"))
mage = json.load(open("../sprites/mage/mage.json"))
font_src = open("glcdfont_lily.c").read()


def b64(frames):
    return [base64.b64encode(bytes(f)).decode() for f in frames]


def get(src_part, name):
    return next(v["frames"] for k, v in pick.items() if src_part in k and k.endswith("::" + name))


lines = font_src.splitlines()[40:135]  # glyphs 32..126, one glyph per line
font = [int(x, 16) for line in lines for x in re.findall(r"0x[0-9A-Fa-f]{2}", line)]
assert len(font) == 95 * 6

data = {
    "font": base64.b64encode(bytes(font)).decode(),
    "luna": {n: b64(get("ellora65", n)) for n in ("sit", "walk", "run", "bark", "sneak")},
    "mage": {k: b64(v) for k, v in mage.items()},
    "girl": {k: b64(v) for k, v in girl.items()},
    "duck": {"idle": b64(get("duckboard_r2", "idle_frames"))},
}

page = open("template_v.html", encoding="utf-8").read().replace("/*DATA*/null", json.dumps(data))
open("lily58-oled.html", "w", encoding="utf-8").write(page)
print("bytes:", len(page))
