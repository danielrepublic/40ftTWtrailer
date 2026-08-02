from pathlib import Path
import tempfile
import unittest

from tools.build.config import load
from tools.build.package import CONDITIONAL_FILES, stage

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
            for files in CONDITIONAL_FILES.values():
                for relative in files:
                    write_file(config.converted_cache / relative)
            for relative in CONVERTED_MODEL_PATHS + SHADOW_PATHS:
                write_file(config.converted_cache / relative)
            for relative in PRESERVED_MODEL_PATHS:
                write_file(config.base_dir / relative, "preserved")
            write_file(config.base_dir / "mod_icon.jpg")

            stage(config)

            self.assertTrue((config.stage_dir / "manifest.sii").is_file())
            self.assertTrue((config.stage_dir / "mod_icon.jpg").is_file())
            for section, files in CONDITIONAL_FILES.items():
                for relative in files:
                    self.assertTrue((config.stage_dir / section / relative).is_file())
                    self.assertFalse((config.stage_base_dir / relative).exists())
            for relative in CONVERTED_MODEL_PATHS + SHADOW_PATHS:
                self.assertTrue((config.stage_base_dir / relative).is_file())
            for relative in PRESERVED_MODEL_PATHS:
                self.assertEqual((config.stage_base_dir / relative).read_text(encoding="utf-8"), "preserved")


if __name__ == "__main__":
    unittest.main()
