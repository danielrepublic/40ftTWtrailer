"""Reconcile the V2 Blender source with the established SCS part contract."""

from pathlib import Path

import bpy
from io_scs_tools.internals import shader_presets
from io_scs_tools.utils import material as material_utils


ROOT_NAME = "chassis"
LEGACY_ROOT_NAME = "tw40ch_chassis_root"
GUIDE_PREFIX = "GUIDE_"
DEBUG_OBJECT = "__debug_side_rails_v017"
SOURCE_CABLES = Path(__file__).resolve().parents[1] / "reference" / "mod_extractions" / "20ft_tw_container" / "blender" / "tw20ft_full_model.blend"
PARTS = ("defaultpart", "brace_on", "brace_off", "cables_on", "cables_off")


def set_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def find_product_root():
    root = bpy.data.objects.get(LEGACY_ROOT_NAME)
    if root is not None:
        duplicate = bpy.data.objects.get(ROOT_NAME)
        if duplicate is not None and duplicate.parent == root and not duplicate.children:
            bpy.data.objects.remove(duplicate, do_unlink=True)
        root.name = ROOT_NAME
        return root

    root = bpy.data.objects.get(ROOT_NAME)
    if root is None:
        raise RuntimeError(f"Missing SCS root: {ROOT_NAME}")
    return root


def rebuild_part_inventory(root):
    set_active(root)
    root.scs_object_part_inventory.clear()
    root.scs_object_variant_inventory.clear()

    for name in PARTS:
        part = root.scs_object_part_inventory.add()
        part.name = name

    variant = root.scs_object_variant_inventory.add()
    variant.name = "default"
    for name in PARTS:
        entry = variant.parts.add()
        entry.name = name
        entry.include = True


def append_cable_meshes(root):
    if not SOURCE_CABLES.is_file():
        raise RuntimeError(f"Missing authorized cable source: {SOURCE_CABLES}")

    for name in ("cables_on", "cables_off"):
        existing = bpy.data.objects.get(name)
        if existing:
            bpy.data.objects.remove(existing, do_unlink=True)

    with bpy.data.libraries.load(str(SOURCE_CABLES), link=False) as (source, destination):
        destination.objects = [name for name in ("piece_8", "piece_11") if name in source.objects]

    for obj in destination.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)

    imported = {obj.name: obj for obj in destination.objects if obj is not None}
    if set(imported) != {"piece_8", "piece_11"}:
        raise RuntimeError("Authorized cable meshes were not imported")

    # The V2 cable locators are exactly 2.66314 m ahead of the 20 ft source.
    for source_name, target_name, part_name in (
        ("piece_11", "cables_on", "cables_on"),
        ("piece_8", "cables_off", "cables_off"),
    ):
        obj = imported[source_name]
        obj.name = target_name
        obj.location.y += 2.66314
        obj.parent = root
        obj.scs_props.scs_part = part_name


def isolate_guides(root):
    guides = bpy.data.collections.get("Guides")
    if guides is None:
        guides = bpy.data.collections.new("Guides")
        bpy.context.scene.collection.children.link(guides)

    for obj in tuple(bpy.data.objects):
        if obj.name == DEBUG_OBJECT:
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if not obj.name.startswith(GUIDE_PREFIX):
            continue

        obj.parent = None
        if guides not in obj.users_collection:
            guides.objects.link(obj)
        obj.hide_render = True


def normalize_parts(root):
    special_parts = {
        "lgear_legs_extended": "brace_on",
        "lgear_legs_folded": "brace_off",
        "cables_on": "cables_on",
        "cables_off": "cables_off",
    }
    for obj in root.children_recursive:
        obj.scs_props.scs_part = special_parts.get(obj.name, "defaultpart")


def remove_unused_materials():
    for material in tuple(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)


def set_texture_uvs(props, values):
    props.shader_texture_base_uv.clear()
    for value in values:
        uv = props.shader_texture_base_uv.add()
        uv.value = value


def configure_material(material, preset, texture, uvs, diffuse, specular, shininess):
    if not shader_presets.has_preset(preset):
        raise RuntimeError(f"SCS shader preset is unavailable: {preset}")

    section = shader_presets.get_section(preset)
    props = material.scs_props
    props.active_shader_preset_name = preset
    props.mat_effect_name = section.get_prop_value("Effect")
    material_utils.set_shader_data_to_material(material, section)
    props.shader_texture_base = texture
    set_texture_uvs(props, uvs)
    props.shader_attribute_diffuse = diffuse
    props.shader_attribute_specular = specular
    props.shader_attribute_shininess = shininess


def configure_materials():
    leaf_spring_name = "tw40_leaf_spring"
    if bpy.data.materials.get(leaf_spring_name) is None:
        leaf_spring_name = "tw40_leaf_spring_black_scs"

    material_specs = (
        ("tw40_chassis_base", "truckpaint", "//vehicle/trailer_owned/tw_container/plain_grey.tobj", ("UV_0", "UV_1", "UV_2"), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 250.0),
        ("tw40_running_gear", "dif.spec", "//vehicle/trailer_owned/tw_container/plastic_glossy.tobj", ("UVMap",), (0.35, 0.35, 0.35), (0.3, 0.3, 0.3), 50.0),
        ("tw40_landing_gear", "dif.spec", "//vehicle/trailer_owned/tw_container/plastic_glossy.tobj", ("UV_0",), (0.5, 0.5, 0.5), (0.3, 0.3, 0.3), 50.0),
        (leaf_spring_name, "dif.spec", "//vehicle/trailer_owned/tw_container/plastic_glossy.tobj", ("UVMap",), (0.025, 0.025, 0.025), (0.08, 0.08, 0.08), 18.0),
    )

    for name, preset, texture, uvs, diffuse, specular, shininess in material_specs:
        material = bpy.data.materials.get(name)
        if material is None:
            raise RuntimeError(f"Missing required material: {name}")
        configure_material(material, preset, texture, uvs, diffuse, specular, shininess)

    chassis = bpy.data.materials["tw40_chassis_base"]
    # This is a base-game reflection resource. Preserve its engine path rather
    # than copying an official TOBJ into the mod project during export.
    chassis.scs_props.shader_texture_reflection_use_imported = True
    chassis.scs_props.shader_texture_reflection_imported_tobj = "/material/environment/vehicle_reflection"

    leaf_spring = bpy.data.materials[leaf_spring_name]
    leaf_spring.name = "tw40_leaf_spring_black_scs"


def normalize_vertex_colors(root):
    neutral = (0.216, 0.216, 0.216, 1.0)
    for obj in root.children_recursive:
        if obj.type != "MESH":
            continue
        for name in ("Col", "Col_alpha"):
            attribute = obj.data.color_attributes.get(name)
            if attribute is None:
                attribute = obj.data.color_attributes.new(name, "BYTE_COLOR", "CORNER")
            for item in attribute.data:
                item.color = neutral


def ensure_chassis_paint_uvs(root):
    required_layers = ("UV_0", "UV_1", "UV_2")
    for obj in root.children_recursive:
        if obj.type != "MESH" or "tw40_chassis_base" not in {material.name for material in obj.data.materials if material}:
            continue
        source = obj.data.uv_layers.get("UV_0")
        if source is None:
            raise RuntimeError(f"Truckpaint mesh has no UV_0 layer: {obj.name}")
        for name in required_layers:
            if obj.data.uv_layers.get(name) is not None:
                continue
            target = obj.data.uv_layers.new(name=name)
            for source_uv, target_uv in zip(source.data, target.data):
                target_uv.uv = source_uv.uv


def verify(root):
    part_names = {item.name for item in root.scs_object_part_inventory}
    if part_names != set(PARTS):
        raise RuntimeError(f"Unexpected part inventory: {sorted(part_names)}")

    for name in ("cables_on", "cables_off", "lgear_legs_extended", "lgear_legs_folded"):
        if bpy.data.objects.get(name) is None:
            raise RuntimeError(f"Missing required state mesh: {name}")

    for obj in root.children_recursive:
        if obj.name.startswith(GUIDE_PREFIX) or obj.name == DEBUG_OBJECT:
            raise RuntimeError(f"Non-product object remains below SCS root: {obj.name}")
        if obj.type == "MESH" and not obj.data.uv_layers:
            raise RuntimeError(f"Visible export mesh has no UV layer: {obj.name}")
        if obj.type == "MESH" and not obj.data.materials:
            raise RuntimeError(f"Visible export mesh has no material: {obj.name}")


def main():
    root = find_product_root()

    isolate_guides(root)
    append_cable_meshes(root)
    rebuild_part_inventory(root)
    normalize_parts(root)
    configure_materials()
    normalize_vertex_colors(root)
    ensure_chassis_paint_uvs(root)
    remove_unused_materials()
    verify(root)
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)


main()
