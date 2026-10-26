"""1-bit mage sprite frames (32x88) for the vertical right OLED, adapted from the reference pixel art.

Writes mage.json ({state: [frame bytes, 11 pages x 32 columns]}) and mage.png for a visual check.
"""

import json
import sys

from PIL import Image, ImageDraw

grid = [list(r) for r in json.load(open("cells.json"))]
N = 64
SW, SH = 32, 88
CROP_X = 17          # source column that becomes x = 0
FIG_TOP, FIG_BOTTOM = 2, 60


# 1. remove the original staff: shaft (R/B along the diagonal), head and tassel (top right)
def is_staff(r, c):
    ch = grid[r][c]
    if r <= 11 and c >= 43 and ch in "GRBL":
        return True
    if 11 <= r <= 36 and ch in "RB":
        return True
    if r >= 33 and c <= 14 and ch in "GW":  # staff butt end lower left
        return True
    if 12 <= r <= 16 and c in (47, 48) and ch == "R":
        return True
    return False


body = [[grid[r][c] if not is_staff(r, c) else None for c in range(N)] for r in range(N)]
for r in range(N):
    for c in range(N):
        if body[r][c] is None:
            # staff crossed the dress: patch with the surrounding colour, otherwise background
            around = [grid[r][c + d] for d in (-1, 1) if 0 <= c + d < N and grid[r][c + d] in "WG"]
            body[r][c] = "W" if len(around) == 2 else "."


# 2. pull the twin tails towards the body so everything fits 32 px
def tail_shift(r, c):
    if 10 <= r <= 24 and c <= 23:
        return 2
    if 11 <= r <= 24 and c >= 44:
        return -4
    return 0


def lit(r, c):
    ch = body[r][c]
    if ch in "WB":
        return True  # hair, dress, skin, boots
    if ch == "G":
        return r < 30  # gold on the cape glows, the hem stays a dark band above the legs
    if ch == "D":
        # tights as an outline, so they read apart from the solid boots
        return any(body[r][c + d] not in "D" for d in (-1, 1)) or body[r + 1][c] == "B"
    return False  # hair shading, eyes


def figure_mask(sway=0):
    m = {}
    for r in range(FIG_TOP, FIG_BOTTOM + 1):
        for c in range(N):
            ch = body[r][c]
            if ch == ".":
                continue
            s = tail_shift(r, c)
            dy = sway if s else 0  # tails flutter, the body stays
            x, y = c + s - CROP_X, r + dy
            if 0 <= x < SW:
                m[(x, y)] = lit(r, c)
    return m


def render(sway=0, lift=0, glow=0, effect=None, eyes_closed=False):
    img = Image.new("1", (SW, SH), 0)
    d = ImageDraw.Draw(img)
    oy = SH - 1 - FIG_BOTTOM - lift  # figure bottom sits on the last row
    for (x, y), lit in figure_mask(sway).items():
        if lit:
            img.putpixel((x, y + oy), 1)
    if eyes_closed:
        # the red eyes are dark cells at row 11; close them into a line
        for x in range(36 - CROP_X - 1, 36 - CROP_X + 2):
            img.putpixel((x, 11 + oy), 0)

    # 3. new staff along the original diagonal, held at the chest; dark halo over the white dress
    x0, y0, x1, y1 = 2, 34 + oy, 27, 7 + oy
    d.line((x0, y0, x1, y1), fill=0, width=3)
    d.line((x0, y0, x1, y1), fill=1)
    # staff head: crescent ring with a gem
    hx, hy = 27, 4 + oy
    d.ellipse((hx - 4, hy - 4, hx + 4, hy + 4), fill=0)
    d.arc((hx - 4, hy - 4, hx + 4, hy + 4), 120, 420, fill=1)
    d.rectangle((hx - 1, hy - 1, hx + 1, hy + 1), fill=1)
    if glow:
        for (dx, dy) in ((-7, -3), (2, -8), (5, 5)) if glow == 1 else ((-5, -7), (6, -2), (-2, 7)):
            sx, sy = hx + dx, hy + dy
            if 0 <= sx < SW:
                d.point((sx, sy), fill=1)
                for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= sx + ex < SW:
                        d.point((sx + ex, sy + ey), fill=1)

    if effect == "flowers":
        # little flower field around the boots
        spots = ((3, SH - 4), (24, SH - 6), (28, SH - 3), (7, SH - 9)) if glow == 1 else ((5, SH - 5), (22, SH - 3), (27, SH - 8), (2, SH - 10))
        for fx, fy in spots:
            d.point((fx, fy), fill=0)
            for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d.point((fx + ex, fy + ey), fill=1)
    elif effect in ("zz1", "zz2"):
        for (zx, zy, s) in ((14, oy - 6, 3), (19, oy - 13, 4)) if effect == "zz1" else ((15, oy - 8, 3), (20, oy - 15, 4)):
            d.line((zx, zy, zx + s, zy), fill=1)
            d.line((zx + s, zy, zx, zy + s), fill=1)
            d.line((zx, zy + s, zx + s, zy + s), fill=1)
    elif effect == "bang":
        d.rectangle((15, oy - 14, 16, oy - 8), fill=1)
        d.rectangle((15, oy - 6, 16, oy - 5), fill=1)
    return img


frames = {
    "idle": [render(), render(sway=1), render(glow=1)],
    "cast": [render(glow=1), render(sway=1, glow=2)],
    "fast": [render(glow=1, effect="flowers", lift=2), render(sway=1, glow=2, effect="flowers")],
    "sleep": [render(eyes_closed=True, effect="zz1"), render(eyes_closed=True, sway=1, effect="zz2")],
    "jump": [render(lift=6, sway=1, glow=2)],
    "caps": [render(effect="bang", glow=1)],
}


def to_bytes(img):
    px = img.load()
    return [sum(1 << b for b in range(8) if px[x, p * 8 + b]) for p in range(SH // 8) for x in range(SW)]


json.dump({k: [to_bytes(f) for f in v] for k, v in frames.items()}, open("mage.json", "w"))

S = 5
flat = [f for v in frames.values() for f in v]
sheet = Image.new("RGB", (len(flat) * (SW * S + 10), SH * S), (40, 40, 60))
for i, f in enumerate(flat):
    sheet.paste(f.convert("RGB").resize((SW * S, SH * S), Image.NEAREST), (i * (SW * S + 10), 0))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "mage.png")
print(len(flat), "frames,", len(flat) * SW * SH // 8, "bytes")
