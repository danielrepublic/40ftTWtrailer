"""Build configuration, versioning, and managed paths."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any


VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")
MOD_ID = "tw40ch"


def read_version(root: Path) -> str:
    version_path = root / "VERSION"
    if not version_path.is_file():
        raise RuntimeError(f"Missing version source: {version_path}")
    version = version_path.read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise RuntimeError(f"VERSION must use major.minor format, got {version!r}")
    return version


def _path(root: Path, value: str | None, default: Path) -> Path:
    if not value:
        return default
    candidate = Path(os.path.expandvars(value)).expanduser()
    return candidate if candidate.is_absolute() else (root / candidate).resolve()


@dataclass(frozen=True)
class BuildConfig:
    root: Path
    version: str
    ets2_path: Path | None
    mod_directory: Path
    game_log: Path | None
    blender_host: str
    blender_port: int
    vendor_root: Path
    conversion_tools: Path
    extractor: Path
    converter_pix: Path
    resconvert: Path

    @property
    def project_dir(self) -> Path:
        return self.root / "40trailer"

    @property
    def base_dir(self) -> Path:
        return self.project_dir / "base"

    @property
    def build_dir(self) -> Path:
        return self.project_dir / "build"

    @property
    def stage_dir(self) -> Path:
        return self.build_dir / "staging"

    @property
    def stage_base_dir(self) -> Path:
        return self.stage_dir / "base"

    @property
    def mid_format_dir(self) -> Path:
        return self.build_dir / "mid-format" / MOD_ID

    @property
    def blender_export_dir(self) -> Path:
        return self.base_dir / ".generated" / MOD_ID

    @property
    def tool_cache_dir(self) -> Path:
        return self.vendor_root / "tool-cache"

    @property
    def reverse_verify_dir(self) -> Path:
        return self.build_dir / "reverse-verify"

    @property
    def dist_dir(self) -> Path:
        return self.project_dir / "dist"

    @property
    def source_blend(self) -> Path:
        return self.project_dir / "source" / "blender" / "tw40ch_chassis.blend"

    @property
    def export_script(self) -> Path:
        return self.root / "tools" / "blender" / "export_chassis.py"

    @property
    def contract_validator(self) -> Path:
        return self.root / "tools" / "maintenance" / "validate_contract.py"

    @property
    def package_name(self) -> str:
        return f"{MOD_ID}_v{self.version}.scs"

    @property
    def package_path(self) -> Path:
        return self.dist_dir / self.package_name

    @property
    def conversion_mount(self) -> Path:
        return self.conversion_tools / MOD_ID

    @property
    def conversion_output(self) -> Path:
        return self.conversion_tools / "rsrc" / MOD_ID

    @property
    def converted_cache(self) -> Path:
        return self.conversion_output / "@cache"

    @property
    def report_json(self) -> Path:
        return self.build_dir / "build-report.json"

    @property
    def report_text(self) -> Path:
        return self.build_dir / "build-report.txt"

    @property
    def logs_dir(self) -> Path:
        return self.build_dir / "logs"


def load(root: Path, config_path: Path | None = None, overrides: dict[str, Any] | None = None) -> BuildConfig:
    root = root.resolve()
    config_path = config_path or (root / "build.config.json")
    if not config_path.is_absolute():
        config_path = root / config_path
    raw: dict[str, Any] = {}
    if config_path.is_file():
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    raw.update({key: value for key, value in (overrides or {}).items() if value is not None})

    vendor_root = _path(root, raw.get("vendor_root"), root / "tools" / "vendor")
    conversion_tools = _path(root, raw.get("conversion_tools"), vendor_root / "conversion_tools")
    extractor = _path(root, raw.get("extractor"), vendor_root / "scs_extractor" / "scs_extractor.exe")
    converter_pix = _path(root, raw.get("converter_pix"), vendor_root / "converter_pix.exe")
    resconvert = _path(root, raw.get("resconvert"), conversion_tools / "bin" / "win_x64" / "tools" / "resconvert.exe")
    ets2_value = raw.get("ets2_path")
    ets2_path = _path(root, ets2_value, Path(r"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2")) if ets2_value or Path(r"C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2").is_dir() else None
    default_mod = Path.home() / "Documents" / "Euro Truck Simulator 2" / "mod"
    mod_directory = _path(root, raw.get("mod_directory"), default_mod)
    game_log_value = raw.get("game_log")
    game_log = _path(root, game_log_value, Path()) if game_log_value else None
    return BuildConfig(
        root=root,
        version=read_version(root),
        ets2_path=ets2_path,
        mod_directory=mod_directory,
        game_log=game_log,
        blender_host=str(raw.get("blender_host", "127.0.0.1")),
        blender_port=int(raw.get("blender_port", 9876)),
        vendor_root=vendor_root,
        conversion_tools=conversion_tools,
        extractor=extractor,
        converter_pix=converter_pix,
        resconvert=resconvert,
    )
