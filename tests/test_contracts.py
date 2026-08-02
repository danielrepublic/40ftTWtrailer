from pathlib import Path
import tempfile
import unittest

from tools.build.chassis_contract import RUNTIME_MODEL_LOCATORS
from tools.build.contracts import assert_mid_format


FIXTURE_PARTS = ("defaultpart", "brace_on", "brace_off", "cables_on", "cables_off")


def part_block(name: str, *, collision: bool = False) -> str:
    lines = ["Part {", f'    Name: "{name}"']
    if name == "defaultpart":
        lines.extend(
            [
                f"    LocatorCount: {len(RUNTIME_MODEL_LOCATORS)}",
                "    Locators: " + " ".join(str(index) for index, _ in enumerate(RUNTIME_MODEL_LOCATORS)),
            ]
        )
    if collision:
        lines.extend(["    PieceCount: 0", "    LocatorCount: 7", "    Pieces:", "    Locators: 0 1 2 3 4 5 6"])
    lines.append("}")
    return "\n".join(lines)


def pim_text(parts=FIXTURE_PARTS) -> str:
    piece = "\n".join(
        [
            "Piece {",
            "    Material: 0",
            "    VertexCount: 4",
            "    TriangleCount: 2",
            '    Tag: "_POSITION"',
            '    Tag: "_UV0"',
            '    Aliases: "_TEXCOORD0"',
            '    Tag: "_NORMAL"',
            "    Normal: &bf800000",
            "}",
        ]
    )
    material = '\n'.join(["Material {", "    Index: 0", '    Alias: "tw40_fakeshadow"', '    Effect: "eut2.fakeshadow"', "}"])
    locators = "\n".join(
        f'Locator {{\n    Name: "{name}"\n    Index: {index}\n}}'
        for index, name in enumerate(RUNTIME_MODEL_LOCATORS)
    )
    return "\n".join(["PartCount: 5", *(part_block(part) for part in parts), piece, material, locators])


def pit_text(parts=FIXTURE_PARTS) -> str:
    return "\n".join(
        [
            "PartCount: 5",
            *(part_block(part) for part in parts),
            'Effect: "eut2.truckpaint"',
            'Effect: "eut2.dif.spec"',
            'Value: "/material/environment/vehicle_reflection"',
            'Alias: "tw40_fakeshadow"',
            'Effect: "eut2.fakeshadow"',
        ]
    )


def pic_text(parts=FIXTURE_PARTS) -> str:
    collisions = [
        'Locator {\n    Name: "adv_cpling1"\n    Index: 0\n    Type: "Cylinder"\n}',
        *(
            f'Locator {{\n    Name: "cl"\n    Index: {index}\n    Type: "Box"\n}}'
            for index in range(1, 7)
        ),
    ]
    return "\n".join(
        [
            "PartCount: 5",
            *(part_block(part, collision=part == "cables_on") for part in parts),
            *collisions,
        ]
    )


def write_fixture(root: Path, *, parts=FIXTURE_PARTS) -> None:
    (root / "chassis.pim").write_text(pim_text(parts), encoding="utf-8")
    (root / "chassis.pit").write_text(pit_text(parts), encoding="utf-8")
    (root / "chassis.pic").write_text(pic_text(parts), encoding="utf-8")


class MidFormatContractTests(unittest.TestCase):
    def test_missing_generated_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "Missing generated file"):
                assert_mid_format(Path(directory))

    def test_valid_generated_asset_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)

            assert_mid_format(root)

    def test_missing_runtime_part_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, parts=FIXTURE_PARTS[:-1])

            with self.assertRaisesRegex(RuntimeError, "PIM is missing Part cables_off"):
                assert_mid_format(root)


if __name__ == "__main__":
    unittest.main()
