import unittest

from tools.build.chassis_contract import (
    COLLISION_LOCATOR_TYPES,
    GUARDRAIL_SLOT_Y,
    GUARDRAIL_SLOT_Y_HEX,
    PIC_COLLISION_CYLINDER_NAME,
    PIC_COLLISION_LOCATOR_NAME,
    PIC_COLLISION_LOCATOR_COUNT,
    PARTS,
    RUNTIME_MODEL_LOCATORS,
    WHEEL_POSITIONS,
)


class ChassisContractTests(unittest.TestCase):
    def test_parts_and_runtime_locators_are_unique(self):
        self.assertEqual(len(PARTS), 5)
        self.assertEqual(len(PARTS), len(set(PARTS)))
        self.assertEqual(len(RUNTIME_MODEL_LOCATORS), len(set(RUNTIME_MODEL_LOCATORS)))

    def test_collision_contract_has_one_cylinder_and_six_boxes(self):
        types = [collider_type for _, collider_type in COLLISION_LOCATOR_TYPES]
        self.assertEqual(types.count("Cylinder"), 1)
        self.assertEqual(types.count("Box"), 6)
        self.assertEqual(PIC_COLLISION_LOCATOR_NAME, "cl")
        self.assertEqual(PIC_COLLISION_CYLINDER_NAME, "adv_cpling1")
        self.assertEqual(PIC_COLLISION_LOCATOR_COUNT, 6)

    def test_positions_are_the_v11_layout(self):
        self.assertEqual(len(WHEEL_POSITIONS), 4)
        self.assertEqual(dict(GUARDRAIL_SLOT_Y_HEX)["slot_0"], "bfe1b4a2")
        self.assertEqual(dict(GUARDRAIL_SLOT_Y_HEX)["slot_2"], "40069b1b")
        self.assertEqual(dict(GUARDRAIL_SLOT_Y_HEX)["slot_4"], "3e2e0653")


if __name__ == "__main__":
    unittest.main()
