"""Turn the Vial keymap dump into LAYOUT(...) blocks with QMK keycode names."""

import json
import re
import sys

qmk, dump_path = sys.argv[1], sys.argv[2]
src = open(f"{qmk}/quantum/keycodes.h").read()

enum = {m[0]: int(m[1], 16) for m in re.findall(r"^\s+(\w+) = (0x[0-9A-Fa-f]+),", src, re.M)}
names = {v: k for k, v in enum.items()}
# prefer short aliases: KC_ESC over KC_ESCAPE, MS_WHLU over QK_MOUSE_WHEEL_UP
for alias, target in re.findall(r"^\s+(\w+)\s+= (\w+),", src, re.M):
    if target in enum and (len(alias) < len(names[enum[target]])):
        names[enum[target]] = alias
names[0x0000], names[0x0001] = "XXXXXXX", "_______"

# shifted symbols from keymap_us.h: KC_LPRN = S(KC_9)
shifted = {}
us = open(f"{qmk}/quantum/keymap_extras/keymap_us.h").read()
for alias, base in re.findall(r"^#define (KC_\w{4}) S\((\w+)\)", us, re.M):
    base_kc = enum.get(base)
    if base_kc is not None:
        shifted.setdefault(base_kc, alias)


def name(kc):
    if 0x5220 <= kc <= 0x523F:
        return f"MO({kc & 0x1F})"
    if 0x0200 <= kc <= 0x02FF:
        base = kc & 0xFF
        return shifted.get(base, f"S({names.get(base, hex(base))})")
    return names.get(kc, f"0x{kc:04X}")


layout = json.load(open(f"{qmk}/keyboards/lily58/rev1/keyboard.json"))["layouts"]["LAYOUT"]["layout"]
dump = json.load(open(dump_path))
# rows of the LAYOUT macro as the default keymap formats them: 12, 12, 12, 14, 8
row_sizes = [12, 12, 12, 14, 8]

for li, layer in enumerate(dump["keymap_hex"]):
    keys = [name(int(layer[k["matrix"][0]][k["matrix"][1]], 16)) for k in layout]
    # layout order in keyboard.json is left half row, then right half row
    print(f"[{li}] = LAYOUT(")
    i = 0
    lines = []
    for n in row_sizes:
        lines.append("  " + ", ".join(f"{k:<8}" for k in keys[i : i + n]).rstrip())
        i += n
    print(",\n".join(lines))
    print("),")
