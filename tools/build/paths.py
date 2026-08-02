"""Safe filesystem operations for managed build paths."""

from __future__ import annotations

from pathlib import Path
import shutil


def assert_inside(path: Path, root: Path) -> None:
    path = path.resolve()
    root = root.resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise RuntimeError(f"Refusing to modify path outside managed root: {path}") from error


def reset_directory(path: Path, root: Path) -> None:
    assert_inside(path, root)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def remove_directory(path: Path, root: Path) -> None:
    assert_inside(path, root)
    if path.exists():
        shutil.rmtree(path)


def remove_matching(directory: Path, pattern: str, root: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    removed = []
    for path in directory.glob(pattern):
        assert_inside(path, root)
        if path.is_file() or path.is_symlink():
            path.unlink()
            removed.append(path)
    return removed
