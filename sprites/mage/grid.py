"""Sample the 64x64 pixel-art grid of the reference into classes. Writes cells.json + an enlarged check PNG."""

import json
from collections import Counter

import numpy as np
from PIL import Image

SRC = "reference.jpg"
PITCH, OFF, N = 11.5, 5.25, 64

im = np.array(Image.open(SRC).convert("RGB")).astype(int)
cells = np.zeros((N, N, 3), int)
for r in range(N):
    for c in range(N):
        y, x = int(OFF + r * PITCH), int(OFF + c * PITCH)
        cells[r, c] = np.median(im[max(0, y - 2) : y + 3, max(0, x - 2) : x + 3].reshape(-1, 3), axis=0)


def classify(rgb):
    r, g, b = rgb
    if b > 190 and b - r > 60 and g > 160:
        return "."  # background blue
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    if lum > 205:
        return "W"  # white: hair, dress
    if r - b > 70 and r > 130 and g < 110:
        return "R"  # red: staff shaft, gem, eyes
    if r - b > 50 and lum > 140:
        return "G"  # gold trims, staff head
    if lum > 170:
        return "L"  # light gray shading of white
    if r - b > 25:
        return "B"  # brown boots
    return "D"  # dark: tights, belt


grid = ["".join(classify(cells[r, c]) for c in range(N)) for r in range(N)]
json.dump(grid, open("cells.json", "w"))
print(Counter("".join(grid)))
for r, row in enumerate(grid):
    if row.strip("."):
        print(f"{r:2d} {row}")

pal = {".": (110, 190, 230), "W": (255, 255, 255), "L": (190, 190, 205), "R": (180, 30, 30),
       "G": (210, 180, 110), "B": (130, 95, 70), "D": (50, 55, 70)}
S = 8
out = Image.new("RGB", (N * S, N * S))
for r, row in enumerate(grid):
    for c, ch in enumerate(row):
        out.paste(pal[ch], (c * S, r * S, c * S + S, r * S + S))
out.save("cells.png")
