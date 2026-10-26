import json
import sys

import hid

VID, PID = 0x04D8, 0xEB2D
ROWS, COLS = 10, 6

dev_info = next(d for d in hid.enumerate(VID, PID) if d["usage_page"] == 0xFF60 and d["usage"] == 0x61)
h = hid.device()
h.open_path(dev_info["path"])


def cmd(*payload):
    buf = bytes(payload) + b"\x00" * (32 - len(payload))
    h.write(b"\x00" + buf)
    return bytes(h.read(32, 1000))


layers = cmd(0x11)[1]
total = layers * ROWS * COLS * 2
raw = b""
for off in range(0, total, 28):
    size = min(28, total - off)
    raw += cmd(0x12, off >> 8, off & 0xFF, size)[4 : 4 + size]

keymap = []
for layer in range(layers):
    rows = []
    for r in range(ROWS):
        base = (layer * ROWS * COLS + r * COLS) * 2
        rows.append([int.from_bytes(raw[base + c * 2 : base + c * 2 + 2], "big") for c in range(COLS)])
    keymap.append(rows)

# Vial dynamic entries: counts of tap dance / combo / key override
counts = cmd(0xFE, 0x0D, 0x00)
td_count = counts[0]
tap_dances = []
for i in range(td_count):
    r = cmd(0xFE, 0x0D, 0x01, i)
    if r[0] != 0:
        tap_dances.append({"idx": i, "error": r[0]})
        continue
    vals = [int.from_bytes(r[1 + j * 2 : 3 + j * 2], "little") for j in range(5)]
    tap_dances.append(dict(zip(["idx", "on_tap", "on_hold", "on_double_tap", "on_tap_hold", "tapping_term"], [i, *vals])))

# VIA macros buffer
macro_count = cmd(0x0C)[1]
msize = int.from_bytes(cmd(0x0D)[1:3], "big")
mraw = b""
for off in range(0, msize, 28):
    size = min(28, msize - off)
    mraw += cmd(0x0E, off >> 8, off & 0xFF, size)[4 : 4 + size]

h.close()
out = {
    "layers": layers,
    "keymap_hex": [[[f"0x{k:04X}" for k in row] for row in layer] for layer in keymap],
    "tap_dance_count": td_count,
    "tap_dances": [{k: (f"0x{v:04X}" if k.startswith("on_") else v) for k, v in td.items()} for td in tap_dances],
    "macro_count": macro_count,
    "macro_buffer_nonzero_bytes": sum(1 for b in mraw if b),
    "macro_buffer_hex": mraw.rstrip(b"\x00").hex(),
}
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "keymap_hex"}, indent=1))
for i, layer in enumerate(out["keymap_hex"]):
    print(f"layer {i}:")
    for row in layer:
        print("  ", " ".join(row))
