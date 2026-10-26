"""Full-body anime girl for a vertical (rotated) 32x128 OLED. Writes girl_v.json + preview PNG."""

import json
import sys

from PIL import Image, ImageDraw

W, H = 32, 128
CX = 15.5


def hair_and_face(d, y, eyes, mouth):
    # long hair behind the body, tapering to points at the waist
    d.polygon([(3, y + 14), (1, y + 50), (3, y + 56), (7, y + 44), (8, y + 26)], fill=1)
    d.polygon([(28, y + 14), (30, y + 50), (28, y + 56), (24, y + 44), (23, y + 26)], fill=1)
    # hair dome
    d.ellipse((2, y, 29, y + 28), fill=1)
    # round face
    d.ellipse((4, y + 8, 27, y + 33), fill=0)
    # bangs: soft locks with rounded tips, parted off-center
    d.polygon([(4, y + 7), (27, y + 7), (27, y + 13), (25, y + 12), (23, y + 14), (21, y + 12),
               (19, y + 10), (17, y + 12), (15, y + 14), (13, y + 12), (11, y + 13), (9, y + 12),
               (7, y + 14), (5, y + 13)], fill=1)
    # thin side locks framing the face
    d.polygon([(4, y + 12), (3, y + 32), (6, y + 26)], fill=1)
    d.polygon([(27, y + 12), (28, y + 32), (25, y + 26)], fill=1)
    # bow
    bx, by = 24, y + 1
    d.rectangle((bx - 6, by - 1, bx + 7, by + 6), fill=0)
    d.polygon([(bx, by + 3), (bx - 5, by), (bx - 5, by + 6)], outline=1, fill=0)
    d.polygon([(bx + 1, by + 3), (bx + 6, by), (bx + 6, by + 6)], outline=1, fill=0)
    d.rectangle((bx, by + 2, bx + 1, by + 4), fill=1)

    ey = y + 17
    for ex in (8, 19):
        if eyes == "open":
            d.line((ex - 1, ey - 1, ex + 4, ey - 1), fill=1)   # lash
            d.rectangle((ex, ey, ex + 3, ey + 6), fill=1)
            d.rectangle((ex + 1, ey + 1, ex + 2, ey + 2), fill=0)  # highlight
            d.point((ex + 2, ey + 5), fill=0)
            d.point((ex, ey + 6), fill=0)
            d.point((ex + 3, ey + 6), fill=0)
        elif eyes == "closed":
            d.line((ex, ey + 4, ex + 3, ey + 4), fill=1)
            d.point((ex - 1, ey + 3), fill=1)
            d.point((ex + 4, ey + 3), fill=1)
        elif eyes == "happy":
            d.line((ex, ey + 4, ex + 1, ey + 2), fill=1)
            d.line((ex + 2, ey + 2, ex + 3, ey + 4), fill=1)
        elif eyes == "focus":
            if ex < CX:
                d.line((ex, ey + 1, ex + 3, ey + 3), fill=1)
                d.line((ex + 3, ey + 3, ex, ey + 5), fill=1)
            else:
                d.line((ex + 3, ey + 1, ex, ey + 3), fill=1)
                d.line((ex, ey + 3, ex + 3, ey + 5), fill=1)
    for bx in (7, 22):
        d.point((bx, y + 26), fill=1)
        d.point((bx + 2, y + 26), fill=1)
    my = y + 28
    if mouth == "smile":
        d.line((14, my, 15, my + 1), fill=1)
        d.line((16, my + 1, 17, my), fill=1)
    elif mouth == "open":
        d.ellipse((14, my - 1, 17, my + 2), fill=1)
    elif mouth == "flat":
        d.line((14, my + 1, 17, my + 1), fill=1)
    elif mouth == "cat":
        d.line((13, my, 14, my + 1), fill=1)
        d.line((14, my + 1, 15, my), fill=1)
        d.line((16, my, 17, my + 1), fill=1)
        d.line((17, my + 1, 18, my), fill=1)


def stroke(d, xy):
    """White line with a black halo, so limbs stay readable in front of the white hair."""
    d.line(xy, fill=0, width=3)
    d.line(xy, fill=1, width=1)


def body(d, y, arms, legs):
    # neck
    d.line((14, y + 34, 14, y + 37), fill=1)
    d.line((17, y + 34, 17, y + 37), fill=1)
    # torso (sailor top), black inside with outline and a black margin against the hair
    d.polygon([(8, y + 37), (23, y + 37), (25, y + 60), (6, y + 60)], fill=0)
    d.polygon([(9, y + 38), (22, y + 38), (23, y + 60), (8, y + 60)], fill=0, outline=1)
    # sailor collar and ribbon
    # sailor collar: one white V with the neckline cut out, ribbon under it
    d.polygon([(9, y + 38), (22, y + 38), (16, y + 47), (15, y + 47)], fill=1)
    d.polygon([(13, y + 38), (18, y + 38), (16, y + 42), (15, y + 42)], fill=0)
    d.polygon([(11, y + 47), (15, y + 48), (11, y + 51)], fill=1)
    d.polygon([(20, y + 47), (16, y + 48), (20, y + 51)], fill=1)
    d.rectangle((15, y + 47, 16, y + 49), fill=1)
    # arms: shoulder -> hand, raised ones end above the shoulders
    for name, sx, down_x, up_x in (("left", 8, 5, 3), ("right", 23, 26, 28)):
        up = arms == "both_up" or arms == f"{name}_up"
        hx, hy = (up_x, y + 27) if up else (down_x, y + 57)
        stroke(d, (sx, y + 40, hx, hy))
        d.ellipse((hx - 2, hy - 1, hx + 2, hy + 3), fill=1)
    # pleated skirt
    d.polygon([(7, y + 60), (24, y + 60), (28, y + 77), (3, y + 77)], fill=0, outline=1)
    for x0, x1 in ((11, 9), (15, 15), (16, 16), (20, 22)):
        d.line((x0, y + 61, x1, y + 76), fill=1)
    d.line((7, y + 61, 24, y + 61), fill=1)
    # legs: outlined thighs, white knee socks, shoes
    for lx, dx in ((10, legs[0]), (18, legs[1])):
        top, sock, foot = y + 78, y + 90, y + 101
        d.line((lx, top, lx + dx, sock), fill=1)
        d.line((lx + 3, top, lx + 3 + dx, sock), fill=1)
        d.rectangle((lx + dx, sock, lx + 3 + dx, foot), fill=1)
        d.line((lx + dx, sock + 1, lx + 3 + dx, sock + 1), fill=0)
        d.ellipse((lx + dx - 1, foot, lx + dx + 5, foot + 4), fill=1)


def deco(d, kind, y):
    if kind == "zz":
        for (x, yy, s) in ((20, y - 4, 3), (25, y - 10, 4)):
            d.line((x, yy, x + s, yy), fill=1)
            d.line((x + s, yy, x, yy + s), fill=1)
            d.line((x, yy + s, x + s, yy + s), fill=1)
    elif kind == "sparkle":
        for (x, yy) in ((3, y - 3), (27, y - 6), (29, y + 70)):
            d.line((x - 2, yy, x + 2, yy), fill=1)
            d.line((x, yy - 2, x, yy + 2), fill=1)
    elif kind == "bang":
        d.rectangle((15, y - 11, 16, y - 5), fill=1)
        d.rectangle((15, y - 3, 16, y - 2), fill=1)
    elif kind == "notes":
        d.ellipse((1, y + 70, 4, y + 72), fill=1)
        d.line((4, y + 64, 4, y + 71), fill=1)
        d.line((4, y + 64, 6, y + 66), fill=1)


def pose(eyes="open", mouth="smile", arms="down", legs=(0, 0), dy=0, dec=None):
    img = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(img)
    y = 13 + dy
    hair_and_face(d, y, eyes, mouth)
    body(d, y, arms, legs)
    if dec:
        deco(d, dec, y)
    d.line((0, H - 4, W - 1, H - 4), fill=1)  # floor
    return img


frames = {
    "idle": [pose(), pose(eyes="closed"), pose(mouth="cat")],
    "type": [pose(eyes="focus", mouth="flat", arms="left_up", legs=(-1, 1), dy=-1, dec="notes"),
             pose(eyes="focus", mouth="flat", arms="right_up", legs=(1, -1), dy=0)],
    "fast": [pose(eyes="happy", mouth="open", arms="both_up", legs=(-2, 2), dy=-3, dec="sparkle"),
             pose(eyes="happy", mouth="open", arms="both_up", legs=(0, 0), dy=0)],
    "sleep": [pose(eyes="closed", mouth="flat", dy=1, dec="zz"), pose(eyes="closed", mouth="flat", dy=1)],
    "jump": [pose(eyes="happy", mouth="open", arms="both_up", legs=(-2, 2), dy=-8)],
    "caps": [pose(eyes="open", mouth="open", dec="bang")],
}


def to_bytes(img):
    # logical layout of a rotated QMK OLED: 16 pages of 32 columns
    px = img.load()
    return [sum(1 << b for b in range(8) if px[x, p * 8 + b]) for p in range(H // 8) for x in range(W)]


json.dump({k: [to_bytes(f) for f in v] for k, v in frames.items()}, open("girl_v.json", "w"))

S = 4
flat = [f for v in frames.values() for f in v]
sheet = Image.new("RGB", (len(flat) * (W * S + 10), H * S), (40, 40, 60))
for i, f in enumerate(flat):
    sheet.paste(f.convert("RGB").resize((W * S, H * S), Image.NEAREST), (i * (W * S + 10), 0))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "girl_v.png")
