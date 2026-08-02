from pathlib import Path
import tempfile
import unittest

from tools.build.config import load
from tools.build.package import stage

PRESERVED_MODEL_PATHS = (
    "vehicle/trailer_owned/upgrade/rlights/container.pmd",
    "vehicle/trailer_owned/upgrade/r_mudflap/container.pmd",
    "vehicle/trailer_owned/upgrade/r_mudflap/container.pmg",
)
CONVERTED_MODEL_PATHS = (
    "vehicle/trailer_owned/tw40ch/chassis.pmc",
    "vehicle/trailer_owned/tw40ch/chassis.pmd",
    "vehicle/trailer_owned/tw40ch/chassis.pmg",
    "vehicle/trailer_owned/upgrade/reflective/dirt.pmd",
    "vehicle/trailer_owned/upgrade/reflective/dirt.pmg",
    "vehicle/trailer_owned/upgrade/rlights/container.pmg",
    "vehicle/trailer_owned/upgrade/sideskirt/stock.pmd",
    "vehicle/trailer_owned/upgrade/sideskirt/stock.pmg",
    "vehicle/truck/upgrade/r_plate/tplate.pmd",
    "vehicle/truck/upgrade/r_plate/tplate.pmg",
)
SHADOW_PATHS = (
    "vehicle/trailer_owned/tw40ch/shadow.dds",
    "vehicle/trailer_owned/tw40ch/shadow.tobj",
)
CONDITIONAL_PATHS = {
    "dlc_goodyear": (
        "def/vehicle/trailer_wheel/r_tire/t40_gfmx.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_gkmx.sii",
    ),
    "dlc_michelin": (
        "def/vehicle/trailer_wheel/r_tire/t40_mxd.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxd8.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxdp.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxez.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxhd.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxld.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxlz.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxz2.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxz8.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxze.sii",
    ),
    "dlc_rims": (
        "def/vehicle/trailer_wheel/r_disc/t40_d01c.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d01h.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d01p.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d02c.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d02p.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d08h.sii",
        "def/vehicle/trailer_wheel/r_hub/t40_h01p.sii",
        "def/vehicle/trailer_wheel/r_hub/t40_h02p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n02p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n03c.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n03p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n04c.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n04p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n05p.sii",
    ),
}


def write_file(path: Path, content: str = "fixture") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class PackageStageTests(unittest.TestCase):
    def test_stage_preserves_models_and_separates_conditional_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.1\n", encoding="utf-8")
            config = load(root)

            for name in ("manifest.sii", "mod_description.txt", "mod_description.zh_tw.txt"):
                write_file(config.converted_cache / name)
            for files in CONDITIONAL_PATHS.values():
                for relative in files:
                    write_file(config.converted_cache / relative)
            for relative in CONVERTED_MODEL_PATHS + SHADOW_PATHS:
                write_file(config.converted_cache / relative)
            for relative in PRESERVED_MODEL_PATHS:
                write_file(config.base_dir / relative, "preserved")
            write_file(config.base_dir / "mod_icon.jpg")

            stage(config)

            metadata = ("manifest.sii", "mod_description.txt", "mod_description.zh_tw.txt")
            for name in metadata:
                self.assertTrue((config.stage_dir / name).is_file())
                self.assertFalse((config.stage_base_dir / name).exists())
            self.assertTrue((config.stage_dir / "mod_icon.jpg").is_file())
            for section, files in CONDITIONAL_PATHS.items():
                for relative in files:
                    self.assertTrue((config.stage_dir / section / relative).is_file())
                    self.assertFalse((config.stage_base_dir / relative).exists())
            for relative in CONVERTED_MODEL_PATHS + SHADOW_PATHS:
                self.assertTrue((config.stage_base_dir / relative).is_file())
            for relative in PRESERVED_MODEL_PATHS:
                self.assertEqual((config.stage_base_dir / relative).read_text(encoding="utf-8"), "preserved")

            expected_files = {
                *metadata,
                "mod_icon.jpg",
                *(f"{section}/{relative}" for section, files in CONDITIONAL_PATHS.items() for relative in files),
                *(f"base/{relative}" for relative in CONVERTED_MODEL_PATHS + SHADOW_PATHS + PRESERVED_MODEL_PATHS),
            }
            actual_files = {
                path.relative_to(config.stage_dir).as_posix()
                for path in config.stage_dir.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual_files, expected_files)


if __name__ == "__main__":
    unittest.main()
