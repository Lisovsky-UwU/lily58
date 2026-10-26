import hid

VID, PID = 0x04D8, 0xEB2D

dev_info = next(d for d in hid.enumerate(VID, PID) if d["usage_page"] == 0xFF60 and d["usage"] == 0x61)
h = hid.device()
h.open_path(dev_info["path"])


def cmd(*payload):
    buf = bytes(payload) + b"\x00" * (32 - len(payload))
    h.write(b"\x00" + buf)
    return bytes(h.read(32, 1000))


# VIA: id_get_protocol_version
print("via protocol:", cmd(0x01).hex())
# Vial: vial_get_keyboard_id -> protocol version (4 bytes LE) + UID (8 bytes)
r = cmd(0xFE, 0x00)
print("vial protocol:", int.from_bytes(r[0:4], "little"))
print("uid:", r[4:12].hex(), "| as C array:", ", ".join(f"0x{b:02X}" for b in r[4:12]))
# Vial: get_size of compressed definition
print("definition size:", int.from_bytes(cmd(0xFE, 0x01)[0:4], "little"))
h.close()
