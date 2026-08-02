"""Add the canonical SCS fakeshadow surface to the 40ft chassis source."""

from pathlib import Path

import bpy


SOURCE_NAME = "tw40ch_chassis.blend"
ROOT_NAME = "chassis_root"
CORNER_NAME = "shadow_x_crn"
ORIGIN_NAME = "shadow_x_ori"
SURFACE_NAME = "shadow_surface"
MATERIAL_NAME = "tw40_fakeshadow"


def source_path():
    path = Path(bpy.data.filepath).resolve()
    if path.name != SOURCE_NAME or not path.is_file():
        raise RuntimeError(f"Expected canonical source {SOURCE_NAME}, got {path}")
    if bpy.data.is_dirty:
        raise RuntimeError("Save the canonical Blender source before adding shadow surface")
    return path


def create_backup(source):
    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "tw40ch_chassis.pre_shadow_surface.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(backup), copy=True)
    return backup


def fakeshadow_material():
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material is None:
        template = bpy.data.materials.get("tw40_kingpin_hardware")
        if template is None:
            raise RuntimeError("Missing SCS material template")
        material = template.copy()
        material.name = MATERIAL_NAME
    props = material.scs_props
    props.mat_effect_name = "eut2.fakeshadow"
    props.active_shader_preset_name = "fakeshadow"
    props.shader_attribute_shadow_bias = 0.0
    return material


def create_surface(root):
    if bpy.data.objects.get(SURFACE_NAME) is not None:
        raise RuntimeError(f"Shadow surface already exists: {SURFACE_NAME}")
    corner = bpy.data.objects[CORNER_NAME]
    origin = bpy.data.objects[ORIGIN_NAME]
    half_width = abs(corner.location.x - origin.location.x)
    half_length = abs(corner.location.y - origin.location.y)
    if half_width <= 0.0 or half_length <= 0.0:
        raise RuntimeError("Shadow locators do not define a positive surface")

    mesh = bpy.data.meshes.new(SURFACE_NAME)
    mesh.from_pydata(
        [
            (-half_width, -half_length, 0.0),
            (-half_width, half_length, 0.0),
            (half_width, half_length, 0.0),
            (half_width, -half_length, 0.0),
        ],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    surface = bpy.data.objects.new(SURFACE_NAME, mesh)
    surface.location = tuple(origin.location)
    surface.parent = root
    surface.scs_props.empty_object_type = "None"
    surface.scs_props.scs_part = "defaultpart"
    surface["tw40_shadow_surface"] = True
    surface["tw40_status"] = "static"
    for name in ("Col", "Col_alpha"):
        color_attribute = mesh.color_attributes.new(
            name=name,
            type="BYTE_COLOR",
            domain="CORNER",
        )
        for color in color_attribute.data:
            color.color = (0.214041, 0.214041, 0.214041, 1.0)
    mesh.materials.append(fakeshadow_material())
    collection = root.users_collection[0]
    collection.objects.link(surface)
    return surface


def assert_surface(surface):
    assert len(surface.data.polygons) == 1
    assert surface.data.polygons[0].normal.z < -0.99
    assert surface.scs_props.scs_part == "defaultpart"
    assert surface.data.materials[0].scs_props.mat_effect_name == "eut2.fakeshadow"
    assert {attribute.name for attribute in surface.data.color_attributes} >= {"Col", "Col_alpha"}


def main():
    source = source_path()
    backup = create_backup(source)
    root = bpy.data.objects.get(ROOT_NAME)
    if root is None or root.scs_props.empty_object_type != "SCS_Root":
        raise RuntimeError(f"Missing SCS root: {ROOT_NAME}")
    origin = bpy.data.objects[ORIGIN_NAME]
    origin.rotation_mode = "XYZ"
    origin.rotation_euler = (-1.5707963267948966, 0.0, 3.141592653589793)
    surface = create_surface(root)
    assert_surface(surface)
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    print(f"backup={backup}")
    print(f"surface={surface.name} vertices={len(surface.data.vertices)} normal={tuple(surface.data.polygons[0].normal)}")


if __name__ == "__main__":
    main()
