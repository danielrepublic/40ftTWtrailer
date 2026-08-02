"""Create the rectified 75-YG plate source texture from the reference photo."""

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference" / "f_24639095_1.jpg"
OUTPUT = ROOT / "40trailer" / "source" / "textures" / "t_plate_75-YG.png"
SIZE = 1024

# Photo coordinates use Blender's bottom-left image origin. The quadrilateral
# follows the outer edge of the small physical plate and excludes its blue mount.
BOTTOM_LEFT = (550.0, 281.0)
BOTTOM_RIGHT = (721.0, 285.0)
TOP_RIGHT = (713.0, 359.0)
TOP_LEFT = (557.0, 362.0)

# Match the existing tplate UV layout used by styles 1 and 2.
TARGET_LEFT = 53
TARGET_RIGHT = 971
TARGET_BOTTOM = 296
TARGET_TOP = 727
CORNER_RADIUS = 28


def bilinear_sample(pixels, width, height, x, y):
    x = min(max(x, 0.0), width - 1.0)
    y = min(max(y, 0.0), height - 1.0)
    x0 = int(x)
    y0 = int(y)
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)
    tx = x - x0
    ty = y - y0

    result = []
    for channel in range(4):
        bottom = pixels[(y0 * width + x0) * 4 + channel] * (1.0 - tx)
        bottom += pixels[(y0 * width + x1) * 4 + channel] * tx
        top = pixels[(y1 * width + x0) * 4 + channel] * (1.0 - tx)
        top += pixels[(y1 * width + x1) * 4 + channel] * tx
        result.append(bottom * (1.0 - ty) + top * ty)
    return result


def inside_rounded_rectangle(x, y):
    nearest_x = min(max(x, TARGET_LEFT + CORNER_RADIUS), TARGET_RIGHT - CORNER_RADIUS)
    nearest_y = min(max(y, TARGET_BOTTOM + CORNER_RADIUS), TARGET_TOP - CORNER_RADIUS)
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= CORNER_RADIUS**2


source = bpy.data.images.load(str(SOURCE), check_existing=False)
width, height = source.size
if (width, height) != (1280, 720):
    raise RuntimeError(f"Unexpected reference size: {width}x{height}")
source_pixels = source.pixels[:]

target_pixels = [0.0] * (SIZE * SIZE * 4)
target_width = TARGET_RIGHT - TARGET_LEFT
target_height = TARGET_TOP - TARGET_BOTTOM
for y in range(TARGET_BOTTOM, TARGET_TOP + 1):
    v = (y - TARGET_BOTTOM) / target_height
    left_x = BOTTOM_LEFT[0] * (1.0 - v) + TOP_LEFT[0] * v
    left_y = BOTTOM_LEFT[1] * (1.0 - v) + TOP_LEFT[1] * v
    right_x = BOTTOM_RIGHT[0] * (1.0 - v) + TOP_RIGHT[0] * v
    right_y = BOTTOM_RIGHT[1] * (1.0 - v) + TOP_RIGHT[1] * v
    for x in range(TARGET_LEFT, TARGET_RIGHT + 1):
        if not inside_rounded_rectangle(x, y):
            continue
        u = (x - TARGET_LEFT) / target_width
        source_x = left_x * (1.0 - u) + right_x * u
        source_y = left_y * (1.0 - u) + right_y * u
        color = bilinear_sample(source_pixels, width, height, source_x, source_y)
        color[3] = 1.0
        offset = (y * SIZE + x) * 4
        target_pixels[offset : offset + 4] = color

output = bpy.data.images.new("t_plate_75-YG", width=SIZE, height=SIZE, alpha=True)
output.pixels = target_pixels
output.file_format = "PNG"
output.filepath_raw = str(OUTPUT)
output.save()
print(f"Created {OUTPUT}")
