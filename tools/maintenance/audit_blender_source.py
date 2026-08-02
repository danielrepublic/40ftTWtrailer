"""Print the canonical Blender source structure for final cleanup planning."""

import json

import bpy


root = bpy.data.objects.get("chassis_root")
report = {
    "filepath": bpy.data.filepath,
    "dirty": bpy.data.is_dirty,
    "scenes": [scene.name for scene in bpy.data.scenes],
    "collections": [collection.name for collection in bpy.data.collections],
    "root": {
        "name": root.name if root else None,
        "children": sorted(child.name for child in root.children) if root else [],
        "parts": [item.name for item in root.scs_object_part_inventory] if root else [],
    },
    "objects": [
        {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "collections": sorted(collection.name for collection in obj.users_collection),
            "part": getattr(obj.scs_props, "scs_part", None),
            "empty_type": getattr(obj.scs_props, "empty_object_type", None),
            "status": obj.get("tw40_status"),
            "hidden": obj.hide_viewport,
            "render_hidden": obj.hide_render,
            "export_excluded": obj.get("scs_export_exclude"),
            "materials": sorted(
                material.name for material in obj.data.materials if material
            )
            if obj.type == "MESH"
            else [],
        }
        for obj in sorted(bpy.data.objects, key=lambda item: item.name)
    ],
    "materials": sorted(material.name for material in bpy.data.materials),
    "images": sorted(image.name for image in bpy.data.images),
    "meshes": sorted(mesh.name for mesh in bpy.data.meshes),
    "orphan_counts": {
        "collections": sum(collection.users == 0 for collection in bpy.data.collections),
        "meshes": sum(mesh.users == 0 for mesh in bpy.data.meshes),
        "materials": sum(material.users == 0 for material in bpy.data.materials),
        "images": sum(image.users == 0 for image in bpy.data.images),
    },
}
print("TW40_BLENDER_AUDIT=" + json.dumps(report, ensure_ascii=True))
