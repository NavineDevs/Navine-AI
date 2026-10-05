from __future__ import annotations

import os
import shutil
from pathlib import Path

DOWNLOADS = Path(r"C:\Users\hitbo\Downloads")
SOURCE = DOWNLOADS / "Navine AI"
PROJECTS = [
    DOWNLOADS / "Navine AI - Python",
    DOWNLOADS / "Navuryx AI",
    DOWNLOADS / "Navuryx AI - Python",
    DOWNLOADS / "HitBoyXx23 AI",
    DOWNLOADS / "HitBoyXx23 AI - Python",
]
JUNK_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
HEAVY_DATA = ["nsfw", "image", "video"]


def freed_bytes(path: Path) -> int:
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def remove_path(path: Path) -> int:
    if not path.exists() and not path.is_symlink():
        return 0
    size = freed_bytes(path)
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        print("deleted", path, round(size / (1024 ** 3), 3), "GB")
        return size
    except OSError as exc:
        print("skip", path, exc)
        return 0


def sweep_junk(root: Path) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        current = Path(dirpath)
        if current.name in JUNK_DIRS:
            total += remove_path(current)
            continue
        for name in filenames:
            if name.endswith((".pyc", ".pyo")) or name == "best.pt" or name.endswith(".gguf"):
                total += remove_path(current / name)
    return total


def junction(link: Path, target: Path) -> None:
    if link.exists() or link.is_symlink():
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    os.system('cmd /c mklink /J "' + str(link) + '" "' + str(target) + '"')


def main() -> None:
    before = shutil.disk_usage("C:\\").free
    total = 0
    for archive in [
        SOURCE / "checkpoints" / "text_enterprise" / "archive_34m_8x512",
        SOURCE / "checkpoints" / "video_enterprise" / "archive_11m_384",
    ]:
        total += remove_path(archive)
    for project in [SOURCE, *PROJECTS]:
        if project.exists():
            total += sweep_junk(project)
    src_data = SOURCE / "data"
    for project in PROJECTS:
        if not project.exists():
            continue
        for folder in HEAVY_DATA:
            dest = project / "data" / folder
            src = src_data / folder
            if dest.exists() and not dest.is_symlink() and src.exists():
                total += remove_path(dest)
            if src.exists() and not dest.exists():
                junction(dest, src)
    after = shutil.disk_usage("C:\\").free
    print("removed_gb", round(total / (1024 ** 3), 2))
    print("free_before_gb", round(before / (1024 ** 3), 2))
    print("free_after_gb", round(after / (1024 ** 3), 2))


if __name__ == "__main__":
    main()
