# Model Naming v1.1

This document is the migration map for the 40ft Blender source. It separates
human-readable source names from SCS runtime names. SCS runtime names are kept
where the game or the reference asset may use the locator name as a contract.

## Naming Rules

- Mesh Object names and their Mesh datablock names are identical.
- Mesh names use lowercase English `snake_case`, with the functional category first.
- `front` means the kingpin/gooseneck end (`Y > 0`); `rear` means the tail end (`Y < 0`).
- `left` means vehicle `X < 0`; `right` means vehicle `X > 0`.
- SCS Part IDs remain `defaultpart`, `brace_on`, `brace_off`, `cables_on`, and `cables_off`.
- Runtime resource paths remain `/vehicle/trailer_owned/tw40ch/chassis.*`.

## Mesh Migration

| Old Object | New Object and Mesh datablock |
|---|---|
| `chassis` (SCS root) | `chassis_root` |
| `chassis_main_left` | `frame_main_left` |
| `chassis_main_right` | `frame_main_right` |
| `chassis_cross_beams` | `frame_cross_beams` |
| `piece_6_running_gear` | `running_gear` |
| `lgear_housing` | `landing_gear_housing` |
| `lgear_legs_extended` | `landing_gear_legs_extended` |
| `lgear_legs_folded` | `landing_gear_legs_folded` |
| `hw_kingpin_and_base_plate` | `kingpin_base_plate` |
| `hw_container_lock_front_left` | `container_lock_front_left` |
| `hw_container_lock_front_right` | `container_lock_front_right` |
| `hw_container_lock_rear_left` | `container_lock_rear_left` |
| `hw_container_lock_rear_right` | `container_lock_rear_right` |
| `cables_on` | `cable_connector_on` |
| `cables_off` | `cable_connector_off` |
| `leaf_spring_front_left` | unchanged; Mesh datablock normalized to the same name |
| `leaf_spring_front_right` | unchanged; Mesh datablock normalized to the same name |
| `leaf_spring_rear_left` | unchanged; Mesh datablock normalized to the same name |
| `leaf_spring_rear_right` | unchanged; Mesh datablock normalized to the same name |
| new shadow surface | `shadow_surface` | closed-range plane using `eut2.fakeshadow` |

## Runtime Locator Semantics

These Object names remain unchanged because SCS Model Locator names are used by
the game and the reference model. The right-hand column is the human-readable
semantic name used in this document and in maintenance discussions only.

| Runtime Object Name | Semantic Name | Type / Part |
|---|---|---|
| `hook` | `loc_hitch_hook` | Model / `defaultpart` |
| `cargo` | `loc_cargo` | Model / `defaultpart` |
| `rlights` | `loc_rear_lights` | Model / `defaultpart` |
| `r_mudflap` | `loc_rear_mudflap` | Model / `defaultpart` |
| `reflective` | `loc_reflective` | Model / `defaultpart` |
| `sideskirt` | `loc_side_skirt` | Model / `defaultpart` |
| `t_plate` | `loc_trailer_license_plate` | Model / `defaultpart` |
| `air_cable_r` | `loc_air_cable_red` | Model / `defaultpart` |
| `air_cable_y` | `loc_air_cable_yellow` | Model / `defaultpart` |
| `ele_cable_b` | `loc_electrical_cable_black` | Model / `defaultpart` |
| `ele_cable_w` | `loc_electrical_cable_white` | Model / `defaultpart` |
| `larea_s_0` | `loc_loading_area_start` | Model / `defaultpart` |
| `larea_e_0` | `loc_loading_area_end` | Model / `defaultpart` |
| `wheel_r_0` | `loc_wheel_front_left` | Model / `defaultpart` |
| `wheel_r_1` | `loc_wheel_front_right` | Model / `defaultpart` |
| `wheel_r_2` | `loc_wheel_rear_left` | Model / `defaultpart` |
| `wheel_r_3` | `loc_wheel_rear_right` | Model / `defaultpart` |
| `shadow_x_crn` | `loc_shadow_corner` | Model / `defaultpart` |
| `shadow_x_ori` | `loc_shadow_origin` | Model / `defaultpart` |

## Collision Locator Semantics

Collision runtime names remain unchanged for SCS safety. The current 40ft
geometry uses one cylinder and six boxes in `cables_on`.

| Runtime Object Name | Semantic Name | Shape |
|---|---|---|
| `adv_cpling1` | `loc_collision_coupling` | Cylinder |
| `cl` | `loc_collision_rear_end` | Box |
| `cl.001` | `loc_collision_main_front` | Box |
| `cl.002` | `loc_collision_main_rear` | Box |
| `cl.003` | `loc_collision_guard` | Box |
| `cl.004` | `loc_collision_cross_front` | Box |
| `cl.005` | `loc_collision_cross_rear` | Box |

## Migration Rules

- The migration script is `tools/blender/normalize_model_names.py`.
- It refuses a dirty source, creates a timestamped backup, and saves only after assertions pass.
- It rebuilds `shadow_x_crn` and `shadow_x_ori` from all static Mesh bounds while preserving their runtime names.
- It keeps `shadow_x_ori` in the standard downward orientation and excludes
  `shadow_surface` from the static bounds calculation.
- It removes Mesh datablocks that have no owning Mesh Object after the migration.
- It must not rename runtime Locators or SCS Part IDs.
