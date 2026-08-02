"""Blender MCP preflight and export integration."""

from __future__ import annotations

import json
from pathlib import Path
import re
import socket
import time

from .chassis_contract import (
    COLLISION_PART,
    COLLISION_LOCATOR_TYPES,
    MESH_PARTS,
    PARTS,
    ROOT_OBJECT_NAME,
    RUNTIME_MODEL_LOCATORS,
    RUNTIME_MODEL_PART,
    SCENE_OBJECT_COUNT,
    SHADOW_CORNER_Z_OFFSET,
    SHADOW_EFFECT,
    SHADOW_ORIGIN_ROTATION,
    SHADOW_ORIGIN_Z_OFFSET,
    SHADOW_SURFACE_NAME,
    SHADOW_SURFACE_PROPERTY,
    SHADOW_LOCATORS,
)


class BlenderMcp:
    def __init__(self, host: str, port: int, attempts: int = 30):
        self.host = host
        self.port = port
        self.attempts = attempts

    def execute(self, code: str) -> str:
        request = json.dumps({"type": "execute_code", "params": {"code": code}}, separators=(",", ":")).encode()
        last_error = None
        for attempt in range(1, self.attempts + 1):
            try:
                with socket.create_connection((self.host, self.port), timeout=5) as client:
                    client.settimeout(300)
                    client.sendall(request)
                    response = read_response(client)
                    if not response:
                        raise RuntimeError("Blender MCP returned an empty response")
                    error = response_error(response)
                    if error:
                        raise RuntimeError(error)
                    return response
            except (OSError, RuntimeError) as error:
                last_error = error
                if attempt == self.attempts:
                    break
                time.sleep(1)
        raise RuntimeError(f"Blender MCP {self.host}:{self.port} failed after {self.attempts} attempts: {last_error}")


def read_response(client) -> str:
    decoder = json.JSONDecoder()
    response = ""
    while True:
        chunk = client.recv(65536)
        if not chunk:
            return response
        response += chunk.decode("utf-8", errors="replace")
        stripped = response.lstrip()
        offset = len(response) - len(stripped)
        try:
            _, end = decoder.raw_decode(stripped)
        except json.JSONDecodeError:
            continue
        return response[offset : offset + end]


def response_error(response: str) -> str | None:
    try:
        payload = json.loads(response)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and payload.get("status") == "error":
        return str(payload.get("message") or response)
    if re.search(r"traceback|assertionerror|runtimeerror|error executing code|code execution error", response, re.I):
        return response
    return None


def preflight_code(source_blend: Path) -> str:
    expected = repr(str(source_blend.resolve()))
    return f"""
import bpy, bmesh, json
from mathutils import Vector
from math import pi
expected = {expected}
root = bpy.data.objects.get({ROOT_OBJECT_NAME!r})
assert bpy.data.filepath == expected, (bpy.data.filepath, expected)
assert not bpy.data.is_dirty, 'canonical source has unsaved Blender changes'
assert root and root.scs_props.empty_object_type == 'SCS_Root', 'SCS root is missing'
assert tuple(item.name for item in root.scs_object_part_inventory) == {PARTS!r}
assert len(bpy.data.objects) == {SCENE_OBJECT_COUNT}, len(bpy.data.objects)
assert not [o.name for o in bpy.data.objects if o.name.startswith('col_')]
mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH']
assert all(o.data.name == o.name for o in mesh_objects), [(o.name, o.data.name) for o in mesh_objects]
assert not [m.name for m in bpy.data.meshes if not any(o.type == 'MESH' and o.data == m for o in bpy.data.objects)]
runtime_models = {RUNTIME_MODEL_LOCATORS!r}
assert all(bpy.data.objects.get(name) and bpy.data.objects[name].scs_props.locator_type == 'Model' for name in runtime_models)
assert all(bpy.data.objects[name].scs_props.scs_part == {RUNTIME_MODEL_PART!r} for name in runtime_models)
collision = {tuple(name for name, _ in COLLISION_LOCATOR_TYPES)!r}
collision_types = {dict(COLLISION_LOCATOR_TYPES)!r}
assert all(bpy.data.objects.get(name) and bpy.data.objects[name].scs_props.locator_type == 'Collision' for name in collision)
assert all(bpy.data.objects[name].scs_props.locator_collider_type == expected for name, expected in collision_types.items())
assert all(bpy.data.objects[name].scs_props.scs_part == {COLLISION_PART!r} for name in collision)
expected_mesh_parts = {dict(MESH_PARTS)!r}
assert {{obj.name: obj.scs_props.scs_part for obj in mesh_objects}} == expected_mesh_parts
shadow_surface = bpy.data.objects[{SHADOW_SURFACE_NAME!r}]
assert shadow_surface.get({SHADOW_SURFACE_PROPERTY!r}) is True
assert len(shadow_surface.data.polygons) == 1
assert shadow_surface.data.polygons[0].normal.z < -0.99
assert shadow_surface.data.materials[0].scs_props.mat_effect_name == {SHADOW_EFFECT!r}
assert {{attribute.name for attribute in shadow_surface.data.color_attributes}} >= {{'Col', 'Col_alpha'}}
shadow_corner_name, shadow_origin_name = {SHADOW_LOCATORS!r}
shadow_origin = bpy.data.objects[shadow_origin_name]
expected_rotation = {SHADOW_ORIGIN_ROTATION!r}
assert all(abs(shadow_surface.location[i] - shadow_origin.location[i]) < 1e-5 for i in (0, 1, 2))
assert abs(shadow_origin.rotation_euler[0] - expected_rotation[0]) < 1e-4
assert abs(shadow_origin.rotation_euler[1] - expected_rotation[1]) < 1e-4
assert abs(shadow_origin.rotation_euler[2] - expected_rotation[2]) < 1e-4
housing = bpy.data.objects['landing_gear_housing']
housing_bmesh = bmesh.new()
housing_bmesh.from_mesh(housing.data)
assert not [edge for edge in housing_bmesh.edges if len(edge.link_faces) == 1], 'landing_gear_housing has open boundary edges'
assert not [edge for edge in housing_bmesh.edges if len(edge.link_faces) > 2], 'landing_gear_housing has non-manifold edges'
housing_bmesh.free()
points = []
for obj in mesh_objects:
    if obj.get('tw40_shadow_surface'):
        continue
    points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
min_x = min(p.x for p in points); min_y = min(p.y for p in points); min_z = min(p.z for p in points)
max_y = max(p.y for p in points); max_z = max(p.z for p in points)
expected_shadow = {{shadow_corner_name: (min_x, max_y, min_z + {SHADOW_CORNER_Z_OFFSET!r}), shadow_origin_name: (0.0, (min_y + max_y) / 2.0, max_z + {SHADOW_ORIGIN_Z_OFFSET!r})}}
for name, expected_location in expected_shadow.items():
    actual = bpy.data.objects[name].location
    assert all(abs(actual[i] - expected_location[i]) < 1e-4 for i in range(3)), (name, tuple(actual), expected_location)
print(json.dumps({{'source': bpy.data.filepath, 'objects': len(bpy.data.objects), 'mesh_objects': len(mesh_objects), 'runtime_models': runtime_models, 'collision': collision}}))
"""


def export_code(export_script: Path, base_dir: Path, output_dir: Path, log_path: Path) -> str:
    return f"""
import json, runpy
module = runpy.run_path({str(export_script.resolve())!r})
outputs = module['export']({str(base_dir.resolve())!r}, {str(output_dir.resolve())!r}, {str(log_path.resolve())!r})
print(json.dumps({{'outputs': outputs}}))
"""
