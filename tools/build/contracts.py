"""Mid-format contract checks independent of the external converter."""

from __future__ import annotations

from pathlib import Path
import re

from .chassis_contract import (
    COLLISION_LOCATOR_TYPES,
    COLLISION_PART,
    PIC_COLLISION_CYLINDER_NAME,
    PIC_COLLISION_LOCATOR_COUNT,
    PIC_COLLISION_LOCATOR_NAME,
    PARTS,
    RUNTIME_MODEL_LOCATORS,
    VEHICLE_REFLECTION_MATERIAL_PATH,
)
from .contract_queries import locator_blocks, piece_blocks


def _read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing generated file: {path}")
    return path.read_text(encoding="utf-8")


def assert_mid_format(directory: Path) -> None:
    pim = _read(directory / "chassis.pim")
    pit = _read(directory / "chassis.pit")
    pic = _read(directory / "chassis.pic")
    texts = {"PIM": pim, "PIT": pit, "PIC": pic}
    part_count = len(PARTS)
    for label, text in texts.items():
        if not re.search(rf"(?m)^\s*PartCount:\s+{part_count}\s*$", text):
            raise RuntimeError(f"{label} does not declare exactly {part_count} parts")
        for part in PARTS:
            if not re.search(rf'(?s)Part \{{\s+Name: "{re.escape(part)}"', text):
                raise RuntimeError(f"{label} is missing Part {part}")
    if 'Effect: "eut2.default"' in pit or 'Effect: ""' in pit:
        raise RuntimeError("PIT contains an empty/default material effect")
    for effect in ("eut2.truckpaint", "eut2.dif.spec"):
        if f'Effect: "{effect}"' not in pit:
            raise RuntimeError(f"PIT is missing {effect}")
    if f'Value: "{VEHICLE_REFLECTION_MATERIAL_PATH}"' not in pit:
        raise RuntimeError("PIT is missing vehicle_reflection")
    pieces_data = piece_blocks(pim)
    pieces = len(pieces_data)
    positions = len(re.findall(r'Tag: "_POSITION"', pim))
    uv0 = len(re.findall(r'Tag: "_UV0"', pim))
    if pieces == 0 or positions != pieces or uv0 != pieces:
        raise RuntimeError("Every PIM piece must contain POSITION and UV0 streams")
    if "_TEXCOORD-1" in pim or 'Aliases: "_TEXCOORD0"' not in pim:
        raise RuntimeError("PIM UV aliases are invalid")
    fakeshadow_material = re.search(
        r'(?ms)^Material \{\s+Index: (\d+)\s+Alias: "tw40_fakeshadow"\s+Effect: "eut2\.fakeshadow".*?^\}$',
        pim,
    )
    if 'Alias: "tw40_fakeshadow"' not in pit or 'Effect: "eut2.fakeshadow"' not in pit:
        raise RuntimeError("PIT is missing the fakeshadow material")
    if fakeshadow_material is None:
        raise RuntimeError("PIM is missing the fakeshadow material")
    material_index = fakeshadow_material.group(1)
    shadow_pieces = [
        piece
        for piece in pieces_data
        if re.search(rf"(?m)^    Material: {material_index}$", piece)
        and re.search(r"(?m)^    VertexCount: 4$", piece)
        and re.search(r"(?m)^    TriangleCount: 2$", piece)
        and 'Tag: "_NORMAL"' in piece
        and "&bf800000" in piece
    ]
    if len(shadow_pieces) != 1:
        raise RuntimeError("PIM must contain one downward fakeshadow plane")
    expected_collision_types = dict(COLLISION_LOCATOR_TYPES)
    expected_pic_indices = set(range(len(COLLISION_LOCATOR_TYPES)))
    if (
        len(re.findall(r'Type: "Cylinder"', pic))
        != sum(value == "Cylinder" for value in expected_collision_types.values())
        or len(re.findall(r'Type: "Box"', pic))
        != sum(value == "Box" for value in expected_collision_types.values())
    ):
        raise RuntimeError("PIC must contain one Cylinder and six Box locators")
    collision_name_count = len(
        re.findall(rf'Name: "{re.escape(PIC_COLLISION_LOCATOR_NAME)}"', pic)
    )
    if collision_name_count != PIC_COLLISION_LOCATOR_COUNT:
        raise RuntimeError("PIC collision locators do not use the expected SCS name")
    pic_locators = locator_blocks(pic)
    pic_indices = [
        int(match.group(1))
        for block in pic_locators
        if (match := re.search(r"(?m)^    Index: (\d+)$", block))
    ]
    if set(pic_indices) != expected_pic_indices:
        raise RuntimeError("PIC collision Locator indices are not contiguous")
    if not any(
        f'Name: "{PIC_COLLISION_CYLINDER_NAME}"' in block
        and 'Type: "Cylinder"' in block
        and re.search(r"(?m)^    Index: 0$", block)
        for block in pic_locators
    ):
        raise RuntimeError("PIC is missing the named coupling Cylinder")
    box_indices = {
        int(match.group(1))
        for block in pic_locators
        if f'Name: "{PIC_COLLISION_LOCATOR_NAME}"' in block
        and 'Type: "Box"' in block
        if (match := re.search(r"(?m)^    Index: (\d+)$", block))
    }
    if box_indices != set(range(1, PIC_COLLISION_LOCATOR_COUNT + 1)):
        raise RuntimeError("PIC does not contain six named Box locators")
    collision_part = re.search(
        rf'(?ms)^Part \{{\s+Name: "{re.escape(COLLISION_PART)}"'
        rf'\s+PieceCount: 0\s+LocatorCount: {len(COLLISION_LOCATOR_TYPES)}'
        rf'\s+Pieces:\s+Locators:\s+([0-9 ]+)\s+^\}}',
        pic,
    )
    if collision_part is None or set(map(int, collision_part.group(1).split())) != expected_pic_indices:
        raise RuntimeError("PIC collision locators must belong to cables_on")
    for name in RUNTIME_MODEL_LOCATORS:
        if not re.search(rf'(?s)Locator \{{\s+Name: "{re.escape(name)}"', pim):
            raise RuntimeError(f"PIM is missing runtime Locator {name}")
    default_part = re.search(r'(?ms)^Part \{\s+Name: "defaultpart".*?^\}$', pim)
    expected_indices = [str(index) for index in range(len(RUNTIME_MODEL_LOCATORS))]
    locator_count = (
        re.search(r"(?m)^    LocatorCount: (\d+)$", default_part.group(0))
        if default_part
        else None
    )
    locator_list = (
        re.search(r"(?m)^    Locators: ([0-9 ]*)$", default_part.group(0))
        if default_part
        else None
    )
    if (
        default_part is None
        or locator_count is None
        or int(locator_count.group(1)) != len(RUNTIME_MODEL_LOCATORS)
        or locator_list is None
        or locator_list.group(1).split() != expected_indices
    ):
        raise RuntimeError("PIM runtime Locators do not all belong to defaultpart")
    pim_locators = locator_blocks(pim)
    pim_indices = [
        int(match.group(1))
        for block in pim_locators
        if (match := re.search(r"(?m)^    Index: (\d+)$", block))
    ]
    if sorted(pim_indices) != list(range(len(RUNTIME_MODEL_LOCATORS))):
        raise RuntimeError("PIM runtime Locator indices do not match defaultpart")
