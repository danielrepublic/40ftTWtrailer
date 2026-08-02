"""Export the canonical v1.1 chassis source to SCS mid-format assets."""

import re
import shutil
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import bpy
from io_scs_tools.utils import get_scs_globals


def normalize_uv_aliases(pim_path):
    """Repair invalid UV aliases emitted by the current SCS Blender exporter."""
    pim_path = Path(pim_path)
    text = pim_path.read_text(encoding="utf-8")
    uv_streams = 0

    def normalize(match):
        nonlocal uv_streams
        stream = match.group(0)
        tag = re.search(r'^        Tag: "_UV(\d+)"$', stream, re.MULTILINE)
        if tag is None:
            return stream
        uv_streams += 1
        alias = f'_TEXCOORD{tag.group(1)}'
        stream = re.sub(r"(?m)^        AliasCount: \d+$", "        AliasCount: 1", stream)
        stream = re.sub(r'(?m)^        Aliases:.*$', f'        Aliases: "{alias}"', stream)
        return stream

    text = re.sub(r"(?ms)^    Stream \{\n.*?^    \}$", normalize, text)
    if uv_streams == 0:
        raise RuntimeError(f"No UV streams found in exported PIM: {pim_path}")
    if "_TEXCOORD-1" in text:
        raise RuntimeError(f"Invalid UV aliases remain in exported PIM: {pim_path}")
    pim_path.write_text(text, encoding="utf-8")
    return uv_streams


def export(base_dir, output_dir, log_path):
    """Export without saving or otherwise mutating the loaded blend file."""
    base_dir = Path(base_dir).resolve()
    output_dir = Path(output_dir).resolve()
    log_path = Path(log_path).resolve()
    root = bpy.data.objects.get("chassis_root")
    if root is None or root.scs_props.empty_object_type != "SCS_Root":
        raise RuntimeError("Canonical SCS root 'chassis_root' is missing")

    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("*.pim"):
        path.unlink()
    for path in output_dir.glob("*.pit"):
        path.unlink()
    for path in output_dir.glob("*.pic"):
        path.unlink()

    globals_ = get_scs_globals()
    previous_project_path = globals_.scs_project_path
    previous_scope = globals_.export_scope
    previous_active = bpy.context.view_layer.objects.active
    previously_selected = tuple(obj for obj in bpy.context.selected_objects)
    export_log = StringIO()
    try:
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        globals_.scs_project_path = str(base_dir)
        globals_.export_scope = "selection"

        with redirect_stdout(export_log):
            result = bpy.ops.scs_tools.export_pim(filepath=str(output_dir / "chassis.pim"))
    finally:
        globals_.scs_project_path = previous_project_path
        globals_.export_scope = previous_scope
        bpy.ops.object.select_all(action="DESELECT")
        for obj in previously_selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = previous_active
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(export_log.getvalue(), encoding="utf-8")
    if result != {"FINISHED"}:
        raise RuntimeError(f"SCS export failed: {result}")

    required = tuple(output_dir / f"chassis.{extension}" for extension in ("pim", "pit", "pic"))
    for extension, target in zip(("pim", "pit", "pic"), required):
        root_named = output_dir / f"{root.name}.{extension}"
        if not target.is_file() and root_named.is_file():
            shutil.move(root_named, target)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"SCS export did not produce: {', '.join(missing)}")
    normalize_uv_aliases(required[0])

    return [str(path) for path in required]


def argument(name):
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    try:
        return args[args.index(name) + 1]
    except (ValueError, IndexError) as error:
        raise RuntimeError(f"Missing Blender export argument: {name}") from error


if __name__ == "__main__":
    outputs = export(argument("--base-dir"), argument("--output-dir"), argument("--log"))
    print("SCS export completed:")
    for output in outputs:
        print(output)
