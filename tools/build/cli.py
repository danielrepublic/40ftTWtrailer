"""Command-line orchestration for the tw40ch build."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import sys

from .blender import BlenderMcp, export_code, preflight_code
from .config import BuildConfig, load
from .contracts import assert_mid_format
from .conversion import convert, ensure_effect_resources, migrate_tool_cache, prepare_mount, remove_effect_definition_mount
from .package import create_archive, deploy, stage
from .paths import remove_directory, remove_matching, reset_directory
from .reporting import Reporter


REVERSE_VERIFY_ALLOWED_WARNINGS = (
    "vehicle_reflection.tobj: Unable to mstat file!",
    "vehicle_reflection.tobj: Unable to load!",
    "ccc532965e6efbaa.mat: Error in material!",
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Build the tw40ch ETS2 trailer mod")
    result.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    result.add_argument("--config", type=Path)
    result.add_argument("--clean", action="store_true")
    result.add_argument("--ets2-path", type=Path)
    result.add_argument("--mod-directory", type=Path)
    result.add_argument("--game-log", type=Path)
    return result


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def assert_source_versions(config: BuildConfig) -> None:
    manifest = (config.base_dir / "manifest.sii").read_text(encoding="utf-8")
    for path in (config.base_dir / "mod_description.txt", config.base_dir / "mod_description.zh_tw.txt"):
        text = path.read_text(encoding="utf-8")
        if f"[orange]版本：[normal]{config.version}" not in text:
            raise RuntimeError(f"{path} does not use VERSION {config.version}")
    if f'package_version: "{config.version}"' not in manifest:
        raise RuntimeError(f"manifest.sii does not use VERSION {config.version}")


def write_input_manifest(config: BuildConfig, source_digest: str) -> None:
    lines = [f"blend\t{source_digest}", f"version\t{config.version}"]
    for path in sorted(config.base_dir.rglob("*")):
        if not path.is_file() or ".generated" in path.parts:
            continue
        lines.append(f"base/{path.relative_to(config.base_dir).as_posix()}\t{source_hash(path)}")
    target = config.build_dir / "last_package_input_manifest.tsv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")


def clean(config: BuildConfig) -> None:
    migrate_tool_cache(config)
    reset_directory(config.build_dir, config.project_dir)
    reset_directory(config.mid_format_dir, config.build_dir)
    remove_effect_definition_mount(config)
    remove_directory(config.legacy_mid_format_dir, config.base_dir)
    if config.conversion_tools.is_dir():
        reset_directory(config.conversion_mount, config.conversion_tools)
        reset_directory(config.conversion_output, config.conversion_tools)
    remove_matching(config.dist_dir, "tw40*.scs", config.dist_dir)
    remove_matching(config.mod_directory, "tw40*.scs", config.mod_directory)
    print(f"Cleaned managed outputs for {config.package_name}")


def collect_blender_export(config: BuildConfig) -> None:
    reset_directory(config.mid_format_dir, config.build_dir)
    for extension in ("pim", "pit", "pic"):
        source = config.legacy_mid_format_dir / f"chassis.{extension}"
        if not source.is_file():
            raise RuntimeError(f"Blender export output is missing: {source}")
        shutil.copy2(source, config.mid_format_dir / source.name)
    remove_directory(config.legacy_mid_format_dir, config.base_dir)


def assert_export_log_is_clean(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    unexpected = [
        line
        for line in text.splitlines()
        if re.search(r"\b(error|warning)\b", line, re.I)
        and "draw window and swap" not in line.lower()
    ]
    if unexpected:
        raise RuntimeError(f"Blender export emitted an error or warning; see {path}")
    if "Export successfully completed" not in text:
        raise RuntimeError(f"Blender export did not report success; see {path}")


def validate_reverse_verify(result, reporter: Reporter) -> None:
    text = result.stdout + result.stderr
    warning_lines = [
        line.strip()
        for line in text.splitlines()
        if "<warning>" in line.lower()
    ]
    unexpected = [
        line
        for line in warning_lines
        if not any(marker.lower() in line.lower() for marker in REVERSE_VERIFY_ALLOWED_WARNINGS)
    ]
    fatal = re.search(r"\*\*\*\s*ERROR\s*\*\*\*|<error>", text, re.I)
    if result.returncode != 0 or fatal or unexpected:
        reporter.stage("reverse_verify", "failed", unexpected_warnings=unexpected)
        raise RuntimeError("reverse_verify failed or emitted an unapproved warning")
    if warning_lines:
        reporter.stage("reverse_verify", "passed", accepted_warnings=warning_lines)


def validate_external_inputs(config: BuildConfig) -> None:
    required = (config.source_blend, config.export_script, config.contract_validator, config.resconvert, config.converter_pix)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Missing build inputs:\n" + "\n".join(missing))


def build(config: BuildConfig) -> Path:
    config.build_dir.mkdir(parents=True, exist_ok=True)
    migrate_tool_cache(config)
    reset_directory(config.logs_dir, config.build_dir)
    for path in (config.report_json, config.report_text, config.build_dir / "last_package_input_manifest.tsv"):
        if path.is_file():
            path.unlink()
    remove_directory(config.stage_dir, config.project_dir)
    remove_directory(config.mid_format_dir, config.build_dir)
    remove_directory(config.reverse_verify_dir, config.build_dir)
    remove_directory(config.build_dir / "base-extract", config.build_dir)
    remove_directory(config.build_dir / "staging-alpha", config.build_dir)
    remove_directory(config.build_dir / "tool-cache", config.build_dir)
    reporter = Reporter(config.logs_dir, config.report_json, config.report_text, config.version, config.package_name)
    reporter.start()
    try:
        reporter.stage("prepare_workspace", "running")
        removed_dist = remove_matching(config.dist_dir, "tw40*.scs", config.dist_dir)
        removed_mod = remove_matching(config.mod_directory, "tw40*.scs", config.mod_directory)
        remove_directory(config.legacy_mid_format_dir, config.base_dir)
        reset_directory(config.stage_dir, config.project_dir)
        reset_directory(config.mid_format_dir, config.build_dir)
        reset_directory(config.legacy_mid_format_dir, config.base_dir)
        reset_directory(config.reverse_verify_dir, config.build_dir)
        reporter.stage(
            "prepare_workspace",
            "passed",
            removed_dist_packages=len(removed_dist),
            removed_mod_packages=len(removed_mod),
        )
        reporter.stage("source_versions", "running")
        assert_source_versions(config)
        reporter.stage("source_versions", "passed")
        reporter.stage("external_inputs", "running")
        validate_external_inputs(config)
        reporter.stage("external_inputs", "passed")

        digest = source_hash(config.source_blend)
        write_input_manifest(config, digest)
        mcp = BlenderMcp(config.blender_host, config.blender_port)
        reporter.stage("blender_preflight", "running")
        mcp.execute(preflight_code(config.source_blend))
        reporter.stage("blender_preflight", "passed")
        export_log = config.logs_dir / "blender_export.log"
        reporter.stage("blender_export", "running")
        mcp.execute(export_code(config.export_script, config.base_dir, config.legacy_mid_format_dir, export_log))
        if not export_log.is_file():
            raise RuntimeError(f"Blender export log is missing: {export_log}")
        assert_export_log_is_clean(export_log)
        collect_blender_export(config)
        reporter.stage("blender_export", "passed")
        reporter.stage("mid_format_contract", "running")
        assert_mid_format(config.mid_format_dir)
        reporter.stage("mid_format_contract", "passed")
        reporter.stage("effect_resources", "running")
        ensure_effect_resources(config, reporter)
        reporter.stage("effect_resources", "passed")
        reporter.stage("prepare_mount", "running")
        prepare_mount(config)
        reporter.stage("prepare_mount", "passed")
        convert(config, reporter)
        reporter.stage("package_stage", "running")
        stage(config)
        reporter.stage("package_stage", "passed")
        reverse_result = reporter.command(
            "reverse_verify",
            [str(config.converter_pix), "-b", str(config.stage_base_dir), "-e", str(config.reverse_verify_dir), "-m", "/vehicle/trailer_owned/tw40ch/chassis"],
            config.root,
            check=False,
        )
        validate_reverse_verify(reverse_result, reporter)
        reporter.command(
            "source_contract",
            [
                sys.executable,
                str(config.contract_validator),
                digest,
                "--generated-dir",
                str(config.mid_format_dir),
                "--conversion-mount",
                str(config.conversion_mount),
            ],
            config.root,
        )
        reporter.stage("archive", "running")
        create_archive(config)
        reporter.stage("archive", "passed", package_path=str(config.package_path))
        if config.game_log is not None:
            reporter.stage("game_log", "running")
            if not config.game_log.is_file():
                raise RuntimeError(f"Game log does not exist: {config.game_log}")
            errors = [line for line in config.game_log.read_text(encoding="utf-8", errors="replace").splitlines() if "<ERROR>" in line and re.search(r"tw40ch|tw40ft", line, re.I)]
            if errors:
                raise RuntimeError(f"Game log contains {len(errors)} tw40-related errors")
            reporter.stage("game_log", "passed", path=str(config.game_log))
        reporter.stage("deploy", "running")
        deployed = deploy(config)
        reporter.stage("deploy", "passed", deployed_path=str(deployed))
        reporter.finish("success", source_hash=digest, package_path=str(config.package_path), deployed_path=str(deployed))
        print(config.package_path)
        return config.package_path
    except Exception as error:
        try:
            remove_matching(config.dist_dir, "tw40*.scs", config.dist_dir)
            remove_matching(config.mod_directory, "tw40*.scs", config.mod_directory)
        except OSError:
            pass
        reporter.finish("failed", error=str(error))
        raise


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    config = load(root, args.config, {"ets2_path": str(args.ets2_path) if args.ets2_path else None, "mod_directory": str(args.mod_directory) if args.mod_directory else None, "game_log": str(args.game_log) if args.game_log else None})
    if args.clean:
        clean(config)
        return 0
    build(config)
    return 0
