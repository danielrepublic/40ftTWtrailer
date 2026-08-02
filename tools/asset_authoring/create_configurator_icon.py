"""Create the vehicle-configurator DDS icon from the requested reference photo."""

import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference" / "40ft_photos" / "4e06be898a04454ea3f9794eeee0e1fa.jpg"
OUTPUT = (
    ROOT
    / "40trailer"
    / "base"
    / "material"
    / "ui"
    / "accessory"
    / "body"
    / "tw_container"
    / "body.dds"
)
WIDTH = 128
HEIGHT = 64


def bilinear_sample(pixels, width, height, x, y):
    x = min(max(x, 0.0), width - 1.0)
    y = min(max(y, 0.0), height - 1.0)
    x0 = int(x)
    y0 = int(y)
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)
    x_weight = x - x0
    y_weight = y - y0
    result = []
    for channel in range(3):
        bottom = pixels[(y0 * width + x0) * 4 + channel] * (1.0 - x_weight)
        bottom += pixels[(y0 * width + x1) * 4 + channel] * x_weight
        top = pixels[(y1 * width + x0) * 4 + channel] * (1.0 - x_weight)
        top += pixels[(y1 * width + x1) * 4 + channel] * x_weight
        result.append(bottom * (1.0 - y_weight) + top * y_weight)
    return result


def linear_to_srgb(value):
    if value <= 0.0031308:
        return value * 12.92
    return 1.055 * value ** (1.0 / 2.4) - 0.055


source = bpy.data.images.load(str(SOURCE), check_existing=False)
source_width, source_height = source.size
source_pixels = source.pixels[:]

target_ratio = WIDTH / HEIGHT
source_ratio = source_width / source_height
if source_ratio > target_ratio:
    crop_width = source_height * target_ratio
    crop_height = source_height
else:
    crop_width = source_width
    crop_height = source_width / target_ratio
crop_left = (source_width - crop_width) / 2.0
crop_bottom = (source_height - crop_height) / 2.0

pixel_bytes = bytearray()
for row in range(HEIGHT):
    source_y = crop_bottom + (1.0 - row / (HEIGHT - 1)) * (crop_height - 1.0)
    for column in range(WIDTH):
        source_x = crop_left + column / (WIDTH - 1) * (crop_width - 1.0)
        red, green, blue = bilinear_sample(
            source_pixels, source_width, source_height, source_x, source_y
        )
        red, green, blue = (
            round(min(max(linear_to_srgb(value), 0.0), 1.0) * 255)
            for value in (red, green, blue)
        )
        pixel_bytes.extend((blue, green, red, 255))

header_values = [
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
OUTPUT.write_bytes(b"DDS " + struct.pack("<31I", *header_values) + pixel_bytes)
print(f"Created {OUTPUT}")
