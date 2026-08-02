"""Validate the source and generated asset contract for tw40ch 1.1."""

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build.chassis_contract import (
    GUARDRAIL_SLOT_Y,
    LOADING_AREA_HALF_LENGTH,
    LOADING_AREA_HALF_WIDTH,
    WHEEL_POSITIONS,
)
from tools.build.config import load
from tools.build.contract_queries import locator_position, locator_y, piece_blocks


TARGET_GRAY = 105 / 255
LEAF_SPRING_COLOR = (98 / 255, 91 / 255, 87 / 255)
PLATE_SOURCE_SHA256 = "E75495242718E5F0AA5906788D4E0DDC75DC0DAC95E32120F9B6F097CE78EC49"
PLATE_DDS_SHA256 = "4EB3717215D5162C49003AFF92F87E6BFB6DA3A9A0F148B8ACF95C1C3354D81C"
CONFIGURATOR_REFERENCE_SHA256 = "4F616044F7788F12FC437313A1B47E65CEC508DDAF93271394999210855CB1CE"
CONFIGURATOR_ICON_DDS_SHA256 = "D58557EC3BABF2D6390E56B0E4E0478ED03777086D065B17248BEEBE5D878154"


def read(path):
    return path.read_text(encoding="utf-8")


def floats(value):
    return tuple(float(item) for item in value.split())


def material(text, alias):
    match = re.search(
        rf'(?ms)^    Material \{{\s+Alias: "{re.escape(alias)}".*?^    \}}$',
        text,
    )
    if match is None:
        raise AssertionError(f"missing material {alias}")
    return match.group(0)


def attribute(block, tag):
    match = re.search(
        rf'(?ms)        Attribute \{{.*?Tag: "{re.escape(tag)}"\s+Value: \( ([^)]+) \).*?        \}}',
        block,
    )
    if match is None:
        raise AssertionError(f"missing {tag} attribute")
    return floats(match.group(1))


def close(actual, expected, tolerance=1e-5):
    return len(actual) == len(expected) and all(
        abs(left - right) <= tolerance for left, right in zip(actual, expected)
    )


def main(expected_source_hash=None, generated=None, conversion_mount=None):
    config = load(ROOT)
    project = config.project_dir
    base = config.base_dir
    generated = generated or config.mid_format_dir
    conversion_mount = conversion_mount or config.conversion_mount
    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)

    manifest = read(base / "manifest.sii")
    body = read(
        base
        / "def"
        / "vehicle"
        / "trailer_owned"
        / "tw40ch.container40"
        / "body"
        / "cont_40.sii"
    )
    trailer_data = read(
        base / "def" / "vehicle" / "trailer_owned" / "tw40ch.container40" / "data.sii"
    )
    plate_dir = (
        base
        / "def"
        / "vehicle"
        / "trailer_owned"
        / "tw40ch.container40"
        / "accessory"
        / "t_plate"
    )
    plate_1 = read(plate_dir / "1.sii")
    plate_2 = read(plate_dir / "2.sii")
    desktop = read(base / "def" / "vehicle" / "trailer_desktop" / "tw40ch_40.sii")
    dealer = read(
        base / "def" / "vehicle" / "trailer_dealer" / "tw40ch" / "tw40ch_40.sii"
    )
    trailer_type_icon = read(
        base
        / "material"
        / "ui"
        / "accessory"
        / "trailer_types"
        / "tw40ch_container40.mat"
    )
    chassis = read(
        base
        / "def"
        / "vehicle"
        / "trailer_owned"
        / "tw40ch.container40"
        / "chassis"
        / "ch_40.sii"
    )
    shadow_tobj_path = base / "vehicle" / "trailer_owned" / "tw40ch" / "shadow.tobj"
    shadow_dds_path = base / "vehicle" / "trailer_owned" / "tw40ch" / "shadow.dds"
    shadow_tobj = read(shadow_tobj_path) if shadow_tobj_path.is_file() else ""
    shadow_dds = shadow_dds_path.read_bytes() if shadow_dds_path.is_file() else b""
    holder_root = conversion_mount
    holder = read(
        holder_root
        / "vehicle"
        / "trailer_owned"
        / "upgrade"
        / "sideskirt"
        / "stock.pim"
    )
    pit = read(generated / "chassis.pit")
    pim = read(generated / "chassis.pim")

    version = config.version
    check(f'package_version: "{version}"' in manifest, f"manifest version is not {version}")
    check('shadow_texture: "/vehicle/trailer_owned/tw40ch/shadow.tobj"' in chassis, "chassis does not configure the chassis shadow texture")
    check('extended_shadow_texture: "/vehicle/trailer_owned/tw40ch/shadow.tobj"' in chassis, "chassis does not configure the extended shadow texture")
    check(
        'ui_shadow: "/vehicle/trailer_owned/scs_gooseneck/chassis/shadow_40ft.pmd"' in chassis,
        "chassis does not configure the 40ft dealer UI shadow model",
    )
    check((base / "vehicle" / "trailer_owned" / "tw40ch" / "shadow.dds").is_file(), "extended shadow DDS is missing")
    check((base / "vehicle" / "trailer_owned" / "tw40ch" / "shadow.tobj").is_file(), "extended shadow TOBJ is missing")
    check("map\t2d\tshadow.dds" in shadow_tobj, "shadow TOBJ does not target shadow.dds")
    check("color_space\tlinear" in shadow_tobj, "shadow TOBJ is not linear color space")
    if shadow_dds:
        check(shadow_dds[:4] == b"DDS ", "shadow texture is not a DDS")
        if len(shadow_dds) >= 128:
            height, width = struct.unpack("<II", shadow_dds[12:20])
            check((width, height) == (512, 2048), "shadow DDS is not 512x2048")
            check(struct.unpack("<I", shadow_dds[88:92])[0] == 32, "shadow DDS is not 32-bit RGBA")
            check(any(shadow_dds[131::4]), "shadow DDS alpha channel is empty")
    check(
        "cargo_regular_width: 2.5" in body,
        "owned 40 ft body does not declare cargo_regular_width 2.5",
    )
    check(
        "cargo_loading_methods[]: area_cont_40ft" in body,
        "owned body does not use area_cont_40ft",
    )
    check(
        'name: "88-XD"' in plate_1
        and "look: 1" in plate_1
        and 'icon: "plate_number"' in plate_1,
        "plate 1 is not the 88-XD plate accessory",
    )
    check(
        'name: "75-YG"' in plate_2
        and "look: 2" in plate_2
        and 'icon: "plate_number"' in plate_2,
        "plate 2 is not the 75-YG plate accessory",
    )
    check('fallback[]: "t_plate|2.sii"' in trailer_data, "75-YG is not the fallback plate")
    for label, definition in (("desktop", desktop), ("dealer", dealer)):
        check(
            'data_path: "/def/vehicle/trailer_owned/tw40ch.container40/accessory/t_plate/2.sii"'
            in definition,
            f"{label} does not default to 75-YG",
        )
    check(
        'source : "/material/ui/cargo.tobj"' in trailer_type_icon,
        "job trailer type does not use the original cargo icon",
    )
    check(
        not (
            base
            / "material"
            / "ui"
            / "accessory"
            / "trailer_types"
            / "tw40ch_container40.dds"
        ).exists(),
        "obsolete custom job-menu DDS still exists",
    )
    check(
        'icon: "body/tw_container/body"' in chassis,
        "vehicle configurator chassis does not use the reference-photo icon",
    )
    configurator_reference = (
        ROOT / "reference" / "40ft_photos" / "4e06be898a04454ea3f9794eeee0e1fa.jpg"
    )
    configurator_icon = (
        base
        / "material"
        / "ui"
        / "accessory"
        / "body"
        / "tw_container"
        / "body.dds"
    )
    check(configurator_reference.is_file(), "configurator reference photo is missing")
    check(configurator_icon.is_file(), "configurator reference-photo DDS is missing")
    if configurator_reference.is_file():
        check(
            hashlib.sha256(configurator_reference.read_bytes()).hexdigest().upper()
            == CONFIGURATOR_REFERENCE_SHA256,
            "configurator reference photo changed without updating the icon contract",
        )
    if configurator_icon.is_file():
        icon_bytes = configurator_icon.read_bytes()
        check(
            hashlib.sha256(icon_bytes).hexdigest().upper()
            == CONFIGURATOR_ICON_DDS_SHA256,
            "configurator DDS changed without updating the icon contract",
        )
        check(icon_bytes[:4] == b"DDS ", "configurator icon is not a DDS")
        if len(icon_bytes) >= 128:
            height, width = struct.unpack("<II", icon_bytes[12:20])
            check((width, height) == (128, 64), "configurator DDS is not 128x64")
            check(
                struct.unpack("<I", icon_bytes[88:92])[0] == 32,
                "configurator DDS is not a 32-bit texture",
            )
    plate_texture = base / "vehicle" / "truck" / "upgrade" / "r_plate" / "2.dds"
    plate_source = project / "source" / "textures" / "t_plate_75-YG.png"
    check(plate_texture.is_file(), "75-YG DDS is missing")
    check(plate_source.is_file(), "75-YG source PNG is missing")
    if plate_source.is_file():
        source_bytes = plate_source.read_bytes()
        check(
            hashlib.sha256(source_bytes).hexdigest().upper() == PLATE_SOURCE_SHA256,
            "75-YG source PNG changed without updating the texture contract",
        )
        check(source_bytes[:8] == b"\x89PNG\r\n\x1a\n", "75-YG source is not a PNG")
        if len(source_bytes) >= 24:
            check(
                struct.unpack(">II", source_bytes[16:24]) == (1024, 1024),
                "75-YG source PNG is not 1024x1024",
            )
    if plate_texture.is_file():
        dds_bytes = plate_texture.read_bytes()
        check(
            hashlib.sha256(dds_bytes).hexdigest().upper() == PLATE_DDS_SHA256,
            "75-YG DDS changed without updating the texture contract",
        )
        check(dds_bytes[:4] == b"DDS ", "75-YG texture is not a DDS")
        if len(dds_bytes) >= 88:
            height, width = struct.unpack("<II", dds_bytes[12:20])
            check((width, height) == (1024, 1024), "75-YG DDS is not 1024x1024")
            check(dds_bytes[84:88] == b"DXT5", "75-YG DDS is not DXT5")

    for name, expected in GUARDRAIL_SLOT_Y:
        actual = locator_y(holder, name)
        check(abs(actual - expected) <= 0.001, f"{name} Y is {actual:.6f}, expected {expected:.6f}")

    for alias in ("tw40_running_gear", "tw40_landing_gear"):
        block = material(pit, alias)
        check(
            close(attribute(block, "diffuse"), (TARGET_GRAY,) * 3),
            f"{alias} diffuse is not #696969",
        )
        check(
            close(attribute(block, "specular"), (0.1,) * 3),
            f"{alias} specular is not 0.10",
        )
        check(
            close(attribute(block, "shininess"), (10.0,)),
            f"{alias} shininess is not 10",
        )

    leaf_spring = material(pit, "tw40_leaf_spring_iron_gray_scs")
    check(
        close(attribute(leaf_spring, "diffuse"), LEAF_SPRING_COLOR),
        "leaf spring diffuse is not #625B57",
    )
    check(
        close(attribute(leaf_spring, "specular"), (0.1,) * 3),
        "leaf spring specular is not 0.10",
    )
    check(
        close(attribute(leaf_spring, "shininess"), (10.0,)),
        "leaf spring shininess is not 10",
    )

    kingpin = material(pit, "tw40_kingpin_hardware")
    check(
        close(attribute(kingpin, "diffuse"), (0.5, 0.5, 0.5)),
        "kingpin/base plate original gray changed",
    )

    pieces = piece_blocks(pim)
    check(bool(pieces), "generated chassis contains no pieces")
    for index, piece in enumerate(pieces):
        uv = re.search(r'(?ms)^    Stream \{.*?Tag: "_UV0".*?^    \}$', piece)
        check(uv is not None, f"piece {index} has no UV0 stream")
        if uv is not None:
            check(
                'Aliases: "_TEXCOORD0"' in uv.group(0),
                f"piece {index} UV0 is not aliased to TEXCOORD0",
            )
    check("_TEXCOORD-1" not in pim, "generated chassis contains invalid UV aliases")

    cargo = locator_position(pim, "cargo")
    area_start = locator_position(pim, "larea_s_0")
    area_end = locator_position(pim, "larea_e_0")
    check(
        close(
            area_start,
            (
                cargo[0] - LOADING_AREA_HALF_WIDTH,
                cargo[1],
                cargo[2] - LOADING_AREA_HALF_LENGTH,
            ),
            tolerance=0.002,
        ),
        "larea_s_0 does not bound the 40 ft cargo area",
    )
    check(
        close(
            area_end,
            (
                cargo[0] + LOADING_AREA_HALF_WIDTH,
                cargo[1],
                cargo[2] + LOADING_AREA_HALF_LENGTH,
            ),
            tolerance=0.002,
        ),
        "larea_e_0 does not bound the 40 ft cargo area",
    )
    for name, expected_position in WHEEL_POSITIONS:
        actual_position = locator_position(pim, name)
        check(
            close(actual_position, expected_position, tolerance=0.001),
            f"{name} is {actual_position}, expected {expected_position}",
        )

    input_manifest = project / "build" / "last_package_input_manifest.tsv"
    source_blend = config.source_blend
    if expected_source_hash is not None:
        current_hash = hashlib.sha256(source_blend.read_bytes()).hexdigest().upper()
        check(
            current_hash == expected_source_hash.upper(),
            "canonical Blender source changed during the build",
        )
    elif input_manifest.is_file():
        match = re.search(r"(?m)^blend\t([0-9A-F]+)$", read(input_manifest))
        current_hash = hashlib.sha256(source_blend.read_bytes()).hexdigest().upper()
        check(match is not None, "build input manifest has no Blender source hash")
        if match is not None:
            check(
                match.group(1) == current_hash,
                "generated assets are stale relative to the canonical Blender source",
            )
    else:
        check(False, "build input manifest is missing; generated asset freshness is unknown")

    if failures:
        print("Source contract failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Source contract passed.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate the tw40ch source and generated asset contract")
    parser.add_argument("expected_source_hash", nargs="?")
    parser.add_argument("--generated-dir", type=Path)
    parser.add_argument("--conversion-mount", type=Path)
    args = parser.parse_args()
    sys.exit(main(args.expected_source_hash, args.generated_dir, args.conversion_mount))
