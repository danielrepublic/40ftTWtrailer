import unittest

from tools.build.contract_queries import locator_blocks, locator_position, locator_y, piece_blocks


SAMPLE = """Piece {
    Index: 0
}
Piece {
    Index: 1
}
Locator {
    Name: "cargo"
    Position: ( &3f800000 &40000000 &40400000 )
}
Locator {
    Name: "wheel_r_0"
    Position: ( &bf800000 &00000000 &3f000000 )
}
"""


class ContractQueryTests(unittest.TestCase):
    def test_extracts_mid_format_blocks(self):
        self.assertEqual(len(piece_blocks(SAMPLE)), 2)
        self.assertEqual(len(locator_blocks(SAMPLE)), 2)

    def test_decodes_locator_position_and_y(self):
        self.assertEqual(locator_position(SAMPLE, "cargo"), (1.0, 2.0, 3.0))
        self.assertEqual(locator_y(SAMPLE, "wheel_r_0"), 0.5)

    def test_missing_locator_is_rejected(self):
        with self.assertRaises(AssertionError):
            locator_position(SAMPLE, "missing")


if __name__ == "__main__":
    unittest.main()
