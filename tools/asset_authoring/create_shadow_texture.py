"""Create the transparent black texture used by the v1.1 extended shadow."""

from math import exp
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "40trailer" / "base" / "vehicle" / "trailer_owned" / "tw40ch" / "shadow.dds"
WIDTH = 512
HEIGHT = 2048


def dds_header():
    values = [
        124,
        0x100F,
        HEIGHT,
        WIDTH,
        WIDTH * 4,
        0,
        0,
        *([0] * 11),
        32,
        0x41,
        0,
        32,
        0x00FF0000,
        0x0000FF00,
        0x000000FF,
        0xFF000000,
        0x1000,
        0,
        0,
        0,
        0,
    ]
    return b"DDS " + struct.pack("<31I", *values)


def texture_pixels():
    pixels = bytearray()
    for row in range(HEIGHT):
        y = (row + 0.5) / HEIGHT * 2.0 - 1.0
        for column in range(WIDTH):
            x = (column + 0.5) / WIDTH * 2.0 - 1.0
            edge_fade = min(1.0, max(0.0, (1.0 - abs(x)) * 8.0))
            body = exp(-((x / 0.72) ** 8 + (y / 0.96) ** 8))
            alpha = round(155.0 * body * edge_fade)
            pixels.extend((0, 0, 0, alpha))
    return pixels


OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_bytes(dds_header() + texture_pixels())
print(f"Created {OUTPUT}")
