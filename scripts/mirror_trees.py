"""Mirror Navine package/config changes into Python + Navuryx trees."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


MAIN = Path(r"C:\Users\hitbo\Downloads\Navine AI")
TARGETS = [
    {
        "root": Path(r"C:\Users\hitbo\Downloads\Navine AI - Python"),
        "pkg": "navine",
        "brand": "navine",
    },
    {
        "root": Path(r"C:\Users\hitbo\Downloads\Navuryx AI"),
        "pkg": "navuryx",
        "brand": "navuryx",
    },
    {
        "root": Path(r"C:\Users\hitbo\Downloads\Navuryx AI - Python"),
        "pkg": "navuryx",
        "brand": "navuryx",
    },
]

SKIP_DIR_NAMES = {"__pycache__", ".git", "venv", "checkpoints", "data", "logs", "outputs"}


def brand_text(text: str, brand: str) -> str:
    if brand == "navine":
        return text
    out = text
    repl = [
        ("from navine.", "from navuryx."),
        ("import navine.", "import navuryx."),
        ("import navine\n", "import navuryx\n"),
        ("navine.cli", "navuryx.cli"),
        ("python -m navine", "python -m navuryx"),
        ("Navine AI", "Navuryx AI"),
        ("Navine train", "Navuryx train"),
        ("Navine Neural", "Navuryx Neural"),
        ("NavineDiffusionModel", "NavuryxDiffusionModel"),
        ("NavineTextModel", "NavuryxTextModel"),
        ("NavineTokenizer", "NavuryxTokenizer"),
        ("NavineVideoModel", "NavuryxVideoModel"),
        ("configs/navine.yaml", "configs/navuryx.yaml"),
        ('load_config("navine")', 'load_config("navuryx")'),
        ("load_config('navine')", "load_config('navuryx')"),
        ("_load_Navine_config", "_load_Navuryx_config"),
        ("get_project_root", "get_project_root"),
        ("NAVINE_DEVICE_MODE", "NAVURYX_DEVICE_MODE"),
        ("Navine_DEVICE_MODE", "Navuryx_DEVICE_MODE"),
        ("Navine_PARALLEL_TRAIN", "Navuryx_PARALLEL_TRAIN"),
    ]
    for a, b in repl:
        out = out.replace(a, b)
    out = re.sub(r"\bnavine\b", "navuryx", out)
    out = re.sub(r"\bNavine\b", "Navuryx", out)
    # Repair common over-replacement of class names already handled
    out = out.replace("navuryxDiffusionModel", "NavuryxDiffusionModel")
    out = out.replace("navuryxTextModel", "NavuryxTextModel")
    out = out.replace("navuryxTokenizer", "NavuryxTokenizer")
    out = out.replace("navuryxVideoModel", "NavuryxVideoModel")
    return out


def copy_pkg(src_pkg: Path, dst_pkg: Path, brand: str) -> int:
    count = 0
    if dst_pkg.exists():
        for child in list(dst_pkg.iterdir()):
            if child.name in SKIP_DIR_NAMES:
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                try:
                    child.unlink()
                except OSError:
                    pass
    dst_pkg.mkdir(parents=True, exist_ok=True)
    for path in src_pkg.rglob("*"):
        rel = path.relative_to(src_pkg)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        dest = dst_pkg / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        if path.suffix == ".py" or path.suffix in {".yaml", ".yml", ".md", ".txt"}:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                dest.write_bytes(data)
            else:
                dest.write_text(brand_text(text, brand), encoding="utf-8")
        else:
            dest.write_bytes(data)
        count += 1
    return count


def copy_configs(src_cfg: Path, dst_cfg: Path, brand: str) -> int:
    count = 0
    dst_cfg.mkdir(parents=True, exist_ok=True)
    for path in src_cfg.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(src_cfg)
        name = path.name
        if brand == "navuryx" and name == "navine.yaml":
            dest = dst_cfg / rel.parent / "navuryx.yaml"
        else:
            dest = dst_cfg / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in {".yaml", ".yml", ".txt", ".md", ".json"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            dest.write_text(brand_text(text, brand), encoding="utf-8")
        else:
            shutil.copy2(path, dest)
        count += 1
    return count


def copy_docs(src_docs: Path, dst_docs: Path, brand: str) -> int:
    if not src_docs.exists():
        return 0
    count = 0
    dst_docs.mkdir(parents=True, exist_ok=True)
    for path in src_docs.rglob("*"):
        if not path.is_file():
            continue
        dest = dst_docs / path.relative_to(src_docs)
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8", errors="replace")
        dest.write_text(brand_text(text, brand), encoding="utf-8")
        count += 1
    return count


def main() -> None:
    src_pkg = MAIN / "navine"
    src_cfg = MAIN / "configs"
    src_docs = MAIN / "docs"
    for target in TARGETS:
        root = target["root"]
        if not root.exists():
            print(f"skip missing {root}")
            continue
        pkg_n = copy_pkg(src_pkg, root / target["pkg"], target["brand"])
        cfg_n = copy_configs(src_cfg, root / "configs", target["brand"])
        docs_n = copy_docs(src_docs, root / "docs", target["brand"])
        print(f"{root.name}: pkg={pkg_n} cfg={cfg_n} docs={docs_n}")


if __name__ == "__main__":
    main()
