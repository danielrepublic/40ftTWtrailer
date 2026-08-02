"""Stage converted assets and create/deploy the versioned SCS package."""

from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

from .config import BuildConfig
from .conversion import PRESERVED_RUNTIME_MODELS, copy_tree
from .paths import remove_matching


CONDITIONAL_FILES = {
    "dlc_goodyear": (
        "def/vehicle/trailer_wheel/r_tire/t40_gfmx.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_gkmx.sii",
    ),
    "dlc_michelin": (
        "def/vehicle/trailer_wheel/r_tire/t40_mxd.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxd8.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxdp.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxez.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxhd.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxld.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxlz.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxz2.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxz8.sii",
        "def/vehicle/trailer_wheel/r_tire/t40_mxze.sii",
    ),
    "dlc_rims": (
        "def/vehicle/trailer_wheel/r_disc/t40_d01c.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d01h.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d01p.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d02c.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d02p.sii",
        "def/vehicle/trailer_wheel/r_disc/t40_d08h.sii",
        "def/vehicle/trailer_wheel/r_hub/t40_h01p.sii",
        "def/vehicle/trailer_wheel/r_hub/t40_h02p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n02p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n03c.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n03p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n04c.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n04p.sii",
        "def/vehicle/trailer_wheel/r_nuts/t40_n05p.sii",
    ),
}

EXPECTED_MODELS = (
    "vehicle/trailer_owned/tw40ch/chassis.pmc",
    "vehicle/trailer_owned/tw40ch/chassis.pmd",
    "vehicle/trailer_owned/tw40ch/chassis.pmg",
    "vehicle/trailer_owned/upgrade/reflective/dirt.pmd",
    "vehicle/trailer_owned/upgrade/reflective/dirt.pmg",
    "vehicle/trailer_owned/upgrade/rlights/container.pmd",
    "vehicle/trailer_owned/upgrade/rlights/container.pmg",
    "vehicle/trailer_owned/upgrade/r_mudflap/container.pmd",
    "vehicle/trailer_owned/upgrade/r_mudflap/container.pmg",
    "vehicle/trailer_owned/upgrade/sideskirt/stock.pmd",
    "vehicle/trailer_owned/upgrade/sideskirt/stock.pmg",
    "vehicle/truck/upgrade/r_plate/tplate.pmd",
    "vehicle/truck/upgrade/r_plate/tplate.pmg",
)

EXPECTED_SHADOW_FILES = (
    "vehicle/trailer_owned/tw40ch/shadow.dds",
    "vehicle/trailer_owned/tw40ch/shadow.tobj",
)


def stage(config: BuildConfig) -> None:
    copy_tree(config.converted_cache, config.stage_base_dir)
    for relative in PRESERVED_RUNTIME_MODELS:
        source = config.base_dir / relative
        target = config.stage_base_dir / relative
        if not source.is_file():
            raise RuntimeError(f"Missing legacy runtime model: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    for name in ("manifest.sii", "mod_description.txt", "mod_description.zh_tw.txt"):
        source = config.stage_base_dir / name
        if not source.is_file():
            raise RuntimeError(f"Missing package metadata: {source}")
        shutil.move(source, config.stage_dir / name)

    for section, files in CONDITIONAL_FILES.items():
        for relative in files:
            source = config.stage_base_dir / relative
            target = config.stage_dir / section / relative
            if not source.is_file():
                raise RuntimeError(f"Missing conditional package source: {source}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source, target)

    icon = config.base_dir / "mod_icon.jpg"
    if not icon.is_file():
        raise RuntimeError(f"Missing mod icon: {icon}")
    shutil.copy2(icon, config.stage_dir / icon.name)
    for relative in EXPECTED_MODELS:
        if not (config.stage_base_dir / relative).is_file():
            raise RuntimeError(f"Missing packaged model: {relative}")
    for relative in EXPECTED_SHADOW_FILES:
        if not (config.stage_base_dir / relative).is_file():
            raise RuntimeError(f"Missing packaged shadow resource: {relative}")


def create_archive(config: BuildConfig) -> None:
    config.dist_dir.mkdir(parents=True, exist_ok=True)
    remove_matching(config.dist_dir, "tw40*.scs", config.dist_dir)
    with zipfile.ZipFile(config.package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(config.stage_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(config.stage_dir).as_posix())
    with zipfile.ZipFile(config.package_path) as archive:
        names = set(archive.namelist())
        required_entries = (
            "base/",
            "base/vehicle/trailer_owned/tw40ch/chassis.pmd",
            "base/vehicle/trailer_owned/tw40ch/chassis.pmg",
            "base/vehicle/trailer_owned/tw40ch/chassis.pmc",
            *(f"base/{relative}" for relative in EXPECTED_SHADOW_FILES),
        )
        for required in required_entries:
            if required not in names and required != "base/":
                raise RuntimeError(f"Package is missing required entry: {required}")


def deploy(config: BuildConfig) -> Path:
    config.mod_directory.mkdir(parents=True, exist_ok=True)
    remove_matching(config.mod_directory, "tw40*.scs", config.mod_directory)
    target = config.mod_directory / config.package_name
    shutil.copy2(config.package_path, target)
    return target
