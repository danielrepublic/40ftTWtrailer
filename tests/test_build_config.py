import json
from pathlib import Path
import tempfile
import unittest

from tools.build.config import load, read_version


class BuildConfigTests(unittest.TestCase):
    def test_version_uses_major_minor_and_package_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.1\n", encoding="utf-8")
            config = load(root)
            self.assertEqual(config.version, "1.1")
            self.assertEqual(config.package_name, "tw40ch_v1.1.scs")

    def test_config_paths_are_relative_to_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.1\n", encoding="utf-8")
            (root / "build.config.json").write_text(json.dumps({"vendor_root": "local-vendor"}), encoding="utf-8")
            config = load(root)
            self.assertEqual(config.vendor_root, (root / "local-vendor").resolve())

    def test_export_paths_are_separated_from_authored_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.1\n", encoding="utf-8")
            config = load(root)
            self.assertEqual(
                config.mid_format_dir,
                (root / "40trailer" / "build" / "mid-format" / "tw40ch").resolve(),
            )
            self.assertEqual(
                config.blender_export_dir,
                (root / "40trailer" / "base" / ".generated" / "tw40ch").resolve(),
            )
            self.assertEqual(config.tool_cache_dir, (root / "tools" / "vendor" / "tool-cache").resolve())

    def test_relative_config_path_uses_project_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.1\n", encoding="utf-8")
            (root / "custom-build.json").write_text(
                json.dumps({"vendor_root": "root-vendor"}),
                encoding="utf-8",
            )
            config = load(root, Path("custom-build.json"))
            self.assertEqual(config.vendor_root, (root / "root-vendor").resolve())

    def test_invalid_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("1.1.0\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                read_version(root)


if __name__ == "__main__":
    unittest.main()
