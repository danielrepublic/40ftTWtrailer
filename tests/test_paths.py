from pathlib import Path
import tempfile
import unittest

from tools.build.paths import remove_matching, reset_directory


class BuildPathTests(unittest.TestCase):
    def test_remove_matching_only_removes_managed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tw40ch_v1.1.scs").write_text("package", encoding="utf-8")
            (root / "keep.txt").write_text("keep", encoding="utf-8")

            removed = remove_matching(root, "tw40*.scs", root)

            self.assertEqual([path.name for path in removed], ["tw40ch_v1.1.scs"])
            self.assertFalse((root / "tw40ch_v1.1.scs").exists())
            self.assertTrue((root / "keep.txt").exists())

    def test_reset_directory_rejects_path_outside_managed_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "managed"
            outside = Path(directory) / "outside"

            with self.assertRaisesRegex(RuntimeError, "outside managed root"):
                reset_directory(outside, root)


if __name__ == "__main__":
    unittest.main()
