"""Prepare and convert the SCS mid-format asset tree."""

from __future__ import annotations

import re
from pathlib import Path
import shutil
import subprocess

from .config import MOD_ID, BuildConfig
from .chassis_contract import GUARDRAIL_SLOT_Y_HEX
from .paths import assert_inside, reset_directory
from .reporting import Reporter


SKIP_EXTENSIONS = {".blend", ".blend1", ".blend2", ".psd", ".kra", ".xcf", ".tmp", ".bak", ".log", ".md", ".ps1", ".py"}
SKIP_MODEL_INPUTS = {"vehicle/trailer_owned/upgrade/rlights/container1.pim"}
PRESERVED_RUNTIME_MODELS = (
    "vehicle/trailer_owned/upgrade/rlights/container.pmd",
    "vehicle/trailer_owned/upgrade/r_mudflap/container.pmd",
    "vehicle/trailer_owned/upgrade/r_mudflap/container.pmg",
)


def copy_tree(source: Path, destination: Path, *, exclude_model_assets: bool = False) -> None:
    for source_file in source.rglob("*"):
        if not source_file.is_file():
            continue
        relative = source_file.relative_to(source)
        extension = source_file.suffix.lower()
        if source_file.name.startswith(".") or extension in SKIP_EXTENSIONS:
            continue
        if relative.as_posix().startswith(".generated/"):
            continue
        if exclude_model_assets and extension in {".pmd", ".pmg", ".pmc"}:
            continue
        if exclude_model_assets and relative.as_posix() in SKIP_MODEL_INPUTS:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)


def _run_tool(reporter: Reporter, name: str, command: list[str], cwd: Path) -> None:
    result = reporter.run_stage(name, command, cwd, check=False, reject_pattern=r"\b(error|warning)\b")
    if result.returncode != 0 or re.search(r"\b(error|warning)\b", result.stdout + result.stderr, re.I):
        raise RuntimeError(f"{name} failed or emitted a warning; see {reporter.logs_dir / (name + '.log')}")


def remove_effect_definition_mount(config: BuildConfig) -> None:
    mount = config.conversion_tools / "base" / "effect" / "def"
    is_junction = getattr(mount, "is_junction", lambda: False)()
    if mount.is_symlink() or is_junction or mount.is_file():
        mount.unlink()
    elif mount.exists():
        shutil.rmtree(mount)


def migrate_tool_cache(config: BuildConfig) -> None:
    relative = Path("ets2-1.60.1.7") / "effect-def"
    legacy = config.build_dir / "tool-cache" / relative
    target = config.tool_cache_dir / relative
    if target.is_dir() or not legacy.is_dir():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(legacy, target)


def ensure_effect_resources(config: BuildConfig, reporter: Reporter) -> None:
    if config.ets2_path is None:
        raise RuntimeError("ETS2 path is required for effect resource preparation")
    if not config.ets2_path.is_dir():
        raise RuntimeError(f"ETS2 installation was not found: {config.ets2_path}")
    if not config.extractor.is_file():
        raise RuntimeError(f"SCS extractor is missing: {config.extractor}")
    tool_base = config.conversion_tools / "base"
    remove_effect_definition_mount(config)
    interfaces = tool_base / "effect" / "def" / "eut2_interfaces.sui"
    if not interfaces.is_file():
        _run_tool(reporter, "extract_effect", [str(config.extractor), str(config.ets2_path / "effect.scs"), str(tool_base)], config.root)

    cache_dir = config.tool_cache_dir / "ets2-1.60.1.7" / "effect-def"
    required = (
        "effect_family.sii",
        "eut2_heightmap_transition_config.sui",
        "eut2_interfaces.sui",
        "flavors.sui",
        "inputs.sui",
        "samplers.sui",
        "uniforms.sui",
        "vas.sui",
        "eut2/eut2_aurora.sui",
    )
    if not all((cache_dir / name).is_file() for name in required):
        temp = config.build_dir / "base-extract"
        reset_directory(temp, config.build_dir)
        _run_tool(reporter, "extract_base", [str(config.extractor), str(config.ets2_path / "base.scs"), str(temp)], config.root)
        source = temp / "effect" / "def"
        if not source.is_dir():
            raise RuntimeError("base.scs did not contain effect/def")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        shutil.copytree(source, cache_dir)
        shutil.rmtree(temp)
    mount = tool_base / "effect" / "def"
    mount.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(mount), str(cache_dir)], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create effect definition junction: {result.stdout}{result.stderr}")


def set_guardrail_slot_positions(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    values = dict(GUARDRAIL_SLOT_Y_HEX)
    for name, value in values.items():
        pattern = rf'(?ms)(Locator \{{\s+Name: "{re.escape(name)}".*?Position: \(\s+&[0-9a-f]+\s+&[0-9a-f]+\s+&)[0-9a-f]+(\s+\))'
        matches = list(re.finditer(pattern, text))
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one {name} locator in {path}")
        text = re.sub(pattern, lambda match: match.group(1) + value + match.group(2), text, count=1)
    path.write_text(text, encoding="utf-8")


def prepare_mount(config: BuildConfig) -> None:
    reset_directory(config.stage_dir, config.project_dir)
    reset_directory(config.reverse_verify_dir, config.build_dir)
    reset_directory(config.conversion_mount, config.conversion_tools)
    reset_directory(config.conversion_output, config.conversion_tools)
    copy_tree(config.base_dir, config.conversion_mount, exclude_model_assets=True)

    stale_trailer_definitions = config.conversion_mount / "def" / "vehicle" / "trailer"
    if stale_trailer_definitions.exists():
        shutil.rmtree(stale_trailer_definitions)
    stale_chassis_model = config.conversion_mount / "vehicle" / "trailer_owned" / "upgrade" / "sideskirt" / "chassis"
    for extension in ("pim", "pit", "pic"):
        path = stale_chassis_model.with_suffix(f".{extension}")
        if path.exists():
            path.unlink()
    guardrail_holder = config.conversion_mount / "vehicle" / "trailer_owned" / "upgrade" / "sideskirt" / "stock.pim"
    if not guardrail_holder.is_file():
        raise RuntimeError(f"Missing guardrail holder: {guardrail_holder}")
    set_guardrail_slot_positions(guardrail_holder)

    target = config.conversion_mount / "vehicle" / "trailer_owned" / MOD_ID / "chassis"
    target.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("pim", "pit", "pic"):
        shutil.copy2(config.mid_format_dir / f"chassis.{extension}", target.with_suffix(f".{extension}"))


def convert(config: BuildConfig, reporter: Reporter) -> None:
    if not config.resconvert.is_file():
        raise RuntimeError(f"resconvert is missing: {config.resconvert}")
    _run_tool(reporter, "conversion", [str(config.resconvert), "-update", "-root", MOD_ID], config.resconvert.parent)
    if not config.converted_cache.is_dir():
        raise RuntimeError(f"Conversion cache was not created: {config.converted_cache}")
