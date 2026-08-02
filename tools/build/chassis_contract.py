"""Shared v1.1 runtime invariants for the 40ft chassis."""

from __future__ import annotations

import struct
from typing import Final


ROOT_OBJECT_NAME: Final = "chassis_root"
SCENE_OBJECT_COUNT: Final = 46

PARTS: Final = ("defaultpart", "brace_on", "brace_off", "cables_on", "cables_off")
COLLISION_PART: Final = "cables_on"
RUNTIME_MODEL_PART: Final = "defaultpart"

RUNTIME_MODEL_LOCATORS: Final = (
    "hook",
    "cargo",
    "rlights",
    "r_mudflap",
    "reflective",
    "sideskirt",
    "t_plate",
    "air_cable_r",
    "air_cable_y",
    "ele_cable_b",
    "ele_cable_w",
    "larea_s_0",
    "larea_e_0",
    "wheel_r_0",
    "wheel_r_1",
    "wheel_r_2",
    "wheel_r_3",
    "shadow_x_crn",
    "shadow_x_ori",
)

COLLISION_LOCATOR_TYPES: Final = (
    ("adv_cpling1", "Cylinder"),
    ("cl", "Box"),
    ("cl.001", "Box"),
    ("cl.002", "Box"),
    ("cl.003", "Box"),
    ("cl.004", "Box"),
    ("cl.005", "Box"),
)
COLLISION_LOCATORS: Final = tuple(name for name, _ in COLLISION_LOCATOR_TYPES)
PIC_COLLISION_LOCATOR_NAME: Final = "cl"
PIC_COLLISION_CYLINDER_NAME: Final = "adv_cpling1"
PIC_COLLISION_LOCATOR_COUNT: Final = sum(
    collider_type == "Box" for _, collider_type in COLLISION_LOCATOR_TYPES
)

MESH_PARTS: Final = (
    ("cable_connector_off", "cables_off"),
    ("cable_connector_on", "cables_on"),
    ("container_lock_front_left", "defaultpart"),
    ("container_lock_front_right", "defaultpart"),
    ("container_lock_rear_left", "defaultpart"),
    ("container_lock_rear_right", "defaultpart"),
    ("frame_cross_beams", "defaultpart"),
    ("frame_main_left", "defaultpart"),
    ("frame_main_right", "defaultpart"),
    ("kingpin_base_plate", "defaultpart"),
    ("landing_gear_housing", "defaultpart"),
    ("landing_gear_legs_extended", "brace_on"),
    ("landing_gear_legs_folded", "brace_off"),
    ("leaf_spring_front_left", "defaultpart"),
    ("leaf_spring_front_right", "defaultpart"),
    ("leaf_spring_rear_left", "defaultpart"),
    ("leaf_spring_rear_right", "defaultpart"),
    ("running_gear", "defaultpart"),
    ("shadow_surface", "defaultpart"),
)

SHADOW_LOCATORS: Final = ("shadow_x_crn", "shadow_x_ori")
SHADOW_SURFACE_NAME: Final = "shadow_surface"
SHADOW_SURFACE_PROPERTY: Final = "tw40_shadow_surface"
SHADOW_EFFECT: Final = "eut2.fakeshadow"
SHADOW_ORIGIN_ROTATION: Final = (-1.5707963267948966, 0.0, 3.141592653589793)
SHADOW_CORNER_Z_OFFSET: Final = -0.5
SHADOW_ORIGIN_Z_OFFSET: Final = 0.5331
VEHICLE_REFLECTION_MATERIAL_PATH: Final = "/material/environment/vehicle_reflection"

GUARDRAIL_SLOT_Y: Final = (
    ("slot_0", -1.763325),
    ("slot_1", -1.763325),
    ("slot_2", 2.103217),
    ("slot_3", 2.103217),
    ("slot_4", 0.169946),
    ("slot_5", 0.169946),
)

WHEEL_POSITIONS: Final = (
    ("wheel_r_0", (-0.925, 0.5602, 3.5067687)),
    ("wheel_r_1", (0.925, 0.5602, 3.5067687)),
    ("wheel_r_2", (-0.925, 0.5602, 4.6629722)),
    ("wheel_r_3", (0.925, 0.5602, 4.6629722)),
)
LOADING_AREA_HALF_WIDTH: Final = 1.22
LOADING_AREA_HALF_LENGTH: Final = 6.09


def scs_float_hex(value: float) -> str:
    """Encode a position value in the SCS big-endian float representation."""

    return struct.pack(">f", value).hex()


GUARDRAIL_SLOT_Y_HEX: Final = tuple(
    (name, scs_float_hex(value)) for name, value in GUARDRAIL_SLOT_Y
)
