from pathlib import Path
import tempfile
import unittest

from tools.build.contracts import assert_mid_format


class MidFormatContractTests(unittest.TestCase):
    def test_missing_generated_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "Missing generated file"):
                assert_mid_format(Path(directory))

    def test_missing_runtime_part_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("chassis.pim", "chassis.pit", "chassis.pic"):
                (root / name).write_text("PartCount: 5\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "PIM is missing Part defaultpart"):
                assert_mid_format(root)


if __name__ == "__main__":
    unittest.main()
