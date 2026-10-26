# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "hidapi",
#     "pycaw",
#     "winrt-runtime",
#     "winrt-Windows.Foundation",
#     "winrt-Windows.Media.Control",
# ]
# ///
"""Feeds the Lily58 right screen (media mode) with system volume and the current track.

Run:  uv run host/oled_feed.py                 (sends every second, reconnects if the keyboard is unplugged)
      uv run host/oled_feed.py --dry-run       (prints what would be sent, no keyboard needed)
      uvw run host/oled_feed.py --log FILE     (no console window; errors go to FILE)

Protocol (32-byte raw HID packets, same interface as Vial; see raw_hid_receive_kb in keymap/keymap.c):
  0x40 0x01 volume flags text_len      flags: 0x01 playing, 0x02 muted
  0x40 0x02 offset count chars[count]  text = title, 0x1F, artist (the artist part may be absent)
"""

import asyncio
import sys
import time
import unicodedata

import hid
from pycaw.pycaw import AudioUtilities
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

VID, PID = 0x04D8, 0xEB2D
USAGE_PAGE, USAGE = 0xFF60, 0x61  # raw HID interface of QMK/Vial
CMD, HEADER, TITLE = 0x40, 0x01, 0x02
TITLE_LEN = 64
ARTIST_LEN = 24
SEPARATOR = "\x1f"
CHUNK = 28
PLAYING_STATUS = 4  # GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING

# the screen font is ASCII only
RU = dict(zip("абвгдеёзийклмнопрстуфхцы", "abvgdeezijklmnoprstufhcy"))
RU.update({"ж": "zh", "ч": "ch", "ш": "sh", "щ": "sch", "ю": "yu", "я": "ya", "э": "e", "ъ": "", "ь": ""})


def to_ascii(text: str) -> str:
    out = []
    for ch in text:
        low = ch.lower()
        if low in RU:
            lat = RU[low]
            out.append(lat.capitalize() if ch != low else lat)
        elif ord(ch) < 128:
            out.append(ch)
        else:
            plain = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
            out.append(plain or "?")
    return "".join(out)


def read_volume():
    speakers = AudioUtilities.GetSpeakers()
    endpoint = speakers.EndpointVolume  # pycaw >= 2024
    return round(endpoint.GetMasterVolumeLevelScalar() * 100), bool(endpoint.GetMute())


async def read_track():
    manager = await MediaManager.request_async()
    session = manager.get_current_session()
    if session is None:
        return "", "", False
    props = await session.try_get_media_properties_async()
    playing = session.get_playback_info().playback_status == PLAYING_STATUS
    return props.title or "", props.artist or "", playing


def media_text(title: str, artist: str) -> str:
    artist = to_ascii(artist)[:ARTIST_LEN]
    title = to_ascii(title).replace(SEPARATOR, " ")
    if not artist:
        return title[:TITLE_LEN]
    return title[: TITLE_LEN - len(artist) - 1] + SEPARATOR + artist


def packets(volume: int, muted: bool, playing: bool, text: str):
    data = text.encode("ascii")
    flags = (0x01 if playing else 0) | (0x02 if muted else 0)
    yield bytes([CMD, HEADER, volume, flags, len(data)])
    for off in range(0, len(data), CHUNK):
        part = data[off : off + CHUNK]
        yield bytes([CMD, TITLE, off, len(part)]) + part


def open_keyboard():
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] == USAGE_PAGE and d["usage"] == USAGE:
            dev = hid.device()
            dev.open_path(d["path"])
            return dev
    return None


def send(dev, packet: bytes):
    dev.write(b"\x00" + packet.ljust(32, b"\x00"))
    reply = dev.read(32, 500)  # the firmware echoes every packet; drain it
    if reply and reply[0] == 0xFF:
        raise RuntimeError("firmware does not know command 0x40 (old firmware?)")


def log(message: str):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}", file=sys.stderr, flush=True)


async def main(dry_run: bool):
    dev = None
    while True:
        try:
            volume, muted = read_volume()
            title, artist, playing = await read_track()
        except OSError as e:  # audio device or media session briefly unavailable
            log(f"read failed: {e}")
            await asyncio.sleep(1)
            continue
        text = media_text(title, artist)
        if dry_run:
            print(f"vol={volume} muted={muted} playing={playing} text={text!r}")
        else:
            try:
                dev = dev or open_keyboard()
                if dev:
                    for p in packets(volume, muted, playing, text):
                        send(dev, p)
            except (OSError, RuntimeError) as e:
                log(str(e))
                if dev:
                    dev.close()
                dev = None
        await asyncio.sleep(1)


if __name__ == "__main__":
    if "--log" in sys.argv:
        # started without a console (uvw): keep errors in a file
        sys.stderr = open(sys.argv[sys.argv.index("--log") + 1], "a", encoding="utf-8")
    log("started")
    asyncio.run(main("--dry-run" in sys.argv))
