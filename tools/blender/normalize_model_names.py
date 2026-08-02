"""Normalize the 40ft Blender source without changing SCS locator names.

Run this script inside the canonical Blender 3.6 GUI through Blender MCP.
It creates a timestamped source backup before changing anything and saves only
after the complete migration and scene assertions succeed.
"""

from datetime import datetime
from pathlib import Path
import shutil

import bpy
from mathutils import Vector


SOURCE_NAME = "tw40ch_chassis.blend"
ROOT_OLD_NAME = "chassis"
ROOT_NEW_NAME = "chassis_root"
LOCATOR_COLLECTION = "90_SCS_LOCATORS"
SHADOW_NAMES = ("shadow_x_crn", "shadow_x_ori")
SHADOW_SURFACE_NAME = "shadow_surface"
PARTS = ("defaultpart", "brace_on", "brace_off", "cables_on", "cables_off")

# Model and collision locator names are deliberately absent here. SCS uses
# Model Locator names at runtime, and collision names remain reference-safe.
MESH_RENAMES = {
    "cables_off": "cable_connector_off",
    "cables_on": "cable_connector_on",
    "chassis_cross_beams": "frame_cross_beams",
    "chassis_main_left": "frame_main_left",
    "chassis_main_right": "frame_main_right",
    "hw_container_lock_front_left": "container_lock_front_left",
    "hw_container_lock_front_right": "container_lock_front_right",
    "hw_container_lock_rear_left": "container_lock_rear_left",
    "hw_container_lock_rear_right": "container_lock_rear_right",
    "hw_kingpin_and_base_plate": "kingpin_base_plate",
    "lgear_housing": "landing_gear_housing",
    "lgear_legs_extended": "landing_gear_legs_extended",
    "lgear_legs_folded": "landing_gear_legs_folded",
    "piece_6_running_gear": "running_gear",
}

MESH_DATA_RENAMES = {
    **MESH_RENAMES,
    "leaf_spring_front_left": "leaf_spring_front_left",
    "leaf_spring_front_right": "leaf_spring_front_right",
    "leaf_spring_rear_left": "leaf_spring_rear_left",
    "leaf_spring_rear_right": "leaf_spring_rear_right",
}


def source_path():
    path = Path(bpy.data.filepath).resolve()
    if path.name != SOURCE_NAME:
        raise RuntimeError(f"Expected canonical source {SOURCE_NAME}, got {path.name}")
    if not path.is_file():
        raise RuntimeError(f"Canonical source does not exist: {path}")
    if bpy.data.is_dirty:
        raise RuntimeError("Save the canonical Blender source before migration")
    return path


def create_backup(source):
    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"tw40ch_chassis.pre_v1_1_{stamp}.blend"
    shutil.copy2(source, backup)
    return backup


def validate_name_plan():
    objects = bpy.data.objects
    missing = [name for name in MESH_RENAMES if objects.get(name) is None]
    if missing:
        raise RuntimeError(f"Missing expected Mesh objects: {missing}")

    existing = set(objects.keys())
    conflicts = [new for new in MESH_RENAMES.values() if new in existing]
    if conflicts:
        raise RuntimeError(f"New Mesh names already exist: {conflicts}")
    if objects.get(ROOT_OLD_NAME) is None:
        raise RuntimeError(f"Missing SCS root: {ROOT_OLD_NAME}")
    if objects.get(ROOT_NEW_NAME) is not None:
        raise RuntimeError(f"New SCS root name already exists: {ROOT_NEW_NAME}")
    for name in SHADOW_NAMES:
        obj = objects.get(name)
        if obj is None or obj.type != "EMPTY":
            raise RuntimeError(f"Missing Shadow Model Locator: {name}")


def rename_with_temporary_names():
    objects = bpy.data.objects
    pending = []
    for old, new in MESH_RENAMES.items():
        obj = objects[old]
        temp_object = f"__v11_object_{old}"
        temp_mesh = f"__v11_mesh_{old}"
        obj.name = temp_object
        obj.data.name = temp_mesh
        pending.append((obj, new))

    root = objects[ROOT_OLD_NAME]
    root.name = f"__v11_root_{ROOT_OLD_NAME}"
    if "scs_root" in root:
        root["scs_root"] = ROOT_NEW_NAME

    for obj, new in pending:
        obj.name = new
        obj.data.name = new
    root.name = ROOT_NEW_NAME

    for object_name, data_name in MESH_DATA_RENAMES.items():
        obj = objects[MESH_RENAMES.get(object_name, object_name)]
        if obj.data.name != data_name:
            obj.data.name = f"__v11_mesh_{object_name}"
    for object_name, data_name in MESH_DATA_RENAMES.items():
        obj = objects[MESH_RENAMES.get(object_name, object_name)]
        obj.data.name = data_name


def remove_unowned_mesh_datablocks():
    owned = {obj.data.as_pointer() for obj in bpy.data.objects if obj.type == "MESH"}
    removed = []
    for mesh in list(bpy.data.meshes):
        if mesh.as_pointer() not in owned:
            removed.append(mesh.name)
            bpy.data.meshes.remove(mesh)
    return removed


def shadow_bounds():
    points = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.get("tw40_shadow_surface"):
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise RuntimeError("Cannot build Shadow Locators without static Mesh geometry")
    return (
        min(point.x for point in points),
        min(point.y for point in points),
        min(point.z for point in points),
        max(point.x for point in points),
        max(point.y for point in points),
        max(point.z for point in points),
    )


def rebuild_shadow_locators(root):
    collection = bpy.data.collections.get(LOCATOR_COLLECTION)
    if collection is None:
        raise RuntimeError(f"Missing locator collection: {LOCATOR_COLLECTION}")

    old = [bpy.data.objects[name] for name in SHADOW_NAMES]
    for obj in old:
        bpy.data.objects.remove(obj, do_unlink=True)

    bounds = shadow_bounds()
    min_x, min_y, min_z, max_x, max_y, max_z = bounds
    center_y = (min_y + max_y) / 2.0
    # The 20ft reference uses -0.5m below its ground bound and 0.5331m
    # above its highest static geometry for the shadow origin.
    positions = {
        "shadow_x_crn": (min_x, max_y, min_z - 0.5),
        "shadow_x_ori": (0.0, center_y, max_z + 0.5331),
    }
    for name, location in positions.items():
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = 0.05
        obj.location = location
        obj.parent = root
        collection.objects.link(obj)
        props = obj.scs_props
        props.empty_object_type = "Locator"
        props.locator_type = "Model"
        props.object_identity = name
        props.parent_identity = root.name
        props.scs_part = "defaultpart"
        if name == "shadow_x_ori":
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = (-1.5707963267948966, 0.0, 3.141592653589793)
    return bounds, positions


def assert_scene():
    root = bpy.data.objects.get(ROOT_NEW_NAME)
    if root is None or root.scs_props.empty_object_type != "SCS_Root":
        raise RuntimeError("Migrated SCS root is missing")
    parts = tuple(item.name for item in root.scs_object_part_inventory)
    if parts != PARTS:
        raise RuntimeError(f"Unexpected SCS parts: {parts}")
    for old, new in MESH_DATA_RENAMES.items():
        object_name = MESH_RENAMES.get(old, old)
        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type != "MESH" or obj.data.name != new:
            raise RuntimeError(f"Object/Mesh migration failed: {old} -> {new}")
    for old in MESH_RENAMES:
        if bpy.data.objects.get(old) is not None:
            raise RuntimeError(f"Old Mesh object remains: {old}")
    for name in SHADOW_NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.scs_props.locator_type != "Model":
            raise RuntimeError(f"Shadow Locator migration failed: {name}")
        if obj.scs_props.scs_part != "defaultpart":
            raise RuntimeError(f"Shadow Locator has wrong Part: {name}")
    surface = bpy.data.objects.get(SHADOW_SURFACE_NAME)
    if surface is None or surface.type != "MESH" or surface.scs_props.scs_part != "defaultpart":
        raise RuntimeError("Fakeshadow surface is missing or has the wrong Part")
    if len(bpy.data.objects) != 46:
        raise RuntimeError(f"Unexpected object count after migration: {len(bpy.data.objects)}")


def migrate():
    source = source_path()
    validate_name_plan()
    backup = create_backup(source)
    rename_with_temporary_names()
    root = bpy.data.objects[ROOT_NEW_NAME]
    removed_meshes = remove_unowned_mesh_datablocks()
    bounds, positions = rebuild_shadow_locators(root)
    assert_scene()
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    print("V1_1_MODEL_MIGRATION_COMPLETE")
    print("backup=", backup)
    print("removed_mesh_datablocks=", removed_meshes)
    print("static_bounds=", tuple(round(value, 6) for value in bounds))
    print("shadow_positions=", {name: tuple(round(value, 6) for value in location) for name, location in positions.items()})


if __name__ == "__main__":
    migrate()
