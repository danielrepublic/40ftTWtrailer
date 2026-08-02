from pathlib import Path
import tempfile
import unittest

from tools.build.config import load
from tools.build.package import CONDITIONAL_FILES, EXPECTED_MODELS, EXPECTED_SHADOW_FILES, stage
from tools.build.conversion import PRESERVED_RUNTIME_MODELS


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
            for relative in EXPECTED_MODELS + EXPECTED_SHADOW_FILES:
                write_file(config.converted_cache / relative)
            for relative in PRESERVED_RUNTIME_MODELS:
                write_file(config.base_dir / relative)
            write_file(config.base_dir / "mod_icon.jpg")

            stage(config)

            self.assertTrue((config.stage_dir / "manifest.sii").is_file())
            self.assertTrue((config.stage_dir / "mod_icon.jpg").is_file())
            for section, files in CONDITIONAL_FILES.items():
                for relative in files:
                    self.assertTrue((config.stage_dir / section / relative).is_file())
                    self.assertFalse((config.stage_base_dir / relative).exists())
            for relative in EXPECTED_MODELS + EXPECTED_SHADOW_FILES:
                self.assertTrue((config.stage_base_dir / relative).is_file())


if __name__ == "__main__":
    unittest.main()
