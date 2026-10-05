from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_ROOT = Path(r"C:\Users\hitbo\Downloads\ai output")

EXPORTS = [
    ("text_enterprise", "text"),
    ("text_code", "text"),
    ("hitboyx23_ai", "text"),
    ("hitboyx23_ai_python", "text"),
    ("image_enterprise_v2", "image"),
    ("video_enterprise", "video"),
]

SITES = [
    {"name": "Navine AI", "port": 8765, "text": "text_enterprise"},
    {"name": "Navine AI - Python", "port": 8766, "text": "text_code"},
    {"name": "Navuryx AI", "port": 8767, "text": "text_enterprise"},
    {"name": "Navuryx AI - Python", "port": 8768, "text": "text_code"},
    {"name": "HitBoyXx23 AI", "port": 8769, "text": "hitboyx23_ai"},
    {"name": "HitBoyXx23 AI - Python", "port": 8770, "text": "hitboyx23_ai_python"},
]

IMAGE_KEY = "image_enterprise_v2"
VIDEO_KEY = "video_enterprise"

SITE_LABELS = {
    "Navine AI": "Navine AI",
    "Navine AI - Python": "Navine AI Python coding mode",
    "Navuryx AI": "Navuryx AI",
    "Navuryx AI - Python": "Navuryx AI Python coding mode",
    "HitBoyXx23 AI": "HitBoyXx23 AI",
    "HitBoyXx23 AI - Python": "HitBoyXx23 AI Python coding mode",
}


def _write_import_help() -> None:
    text = """Navine AI model export
=====================

TEXT (Ollama / LM Studio / llama.cpp)
  Import ONLY text.gguf from each site folder.

  Ollama:
    cd "C:\\Users\\hitbo\\Downloads\\ai output\\Navine AI"
    ollama create navine-ai -f Modelfile
    ollama run navine-ai

  LM Studio:
    1. Open LM Studio
    2. My Models -> Import -> select text.gguf
    3. Chat template is embedded (### User: / ### Assistant: format)
    4. Or drag text.gguf into LM Studio window

  Or double-click import_ollama.bat in a site folder.

IMAGE / VIDEO (Navine sites only)
  image.gguf and video.gguf are Navine-native weight bundles.
  Ollama and LM Studio cannot run them (not language models).
  Use your local Navine site instead:
    Image: http://127.0.0.1:8765  (Image tab)
    Video: http://127.0.0.1:8765  (Video tab)

  Native checkpoints are in _checkpoints\\ if you need .pt files.

Re-export after training:
  cd "C:\\Users\\hitbo\\Downloads\\Navine AI"
  .\\venv\\Scripts\\python.exe scripts\\export_ai_output_gguf.py
"""
    (OUT_ROOT / "HOW_TO_IMPORT.txt").write_text(text, encoding="utf-8")


def _write_import_bat(folder: Path, model_tag: str) -> None:
    body = f"""@echo off
cd /d "%~dp0"
where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama is not installed. Get it from https://ollama.com
  pause
  exit /b 1
)
if not exist "text.gguf" (
  echo Missing text.gguf in this folder.
  pause
  exit /b 1
)
if not exist "Modelfile" (
  echo Missing Modelfile in this folder.
  pause
  exit /b 1
)
ollama create {model_tag} -f Modelfile
if errorlevel 1 (
  echo Import failed. See HOW_TO_IMPORT.txt in the parent folder.
  pause
  exit /b 1
)
echo Imported as {model_tag}
echo Run: ollama run {model_tag}
pause
"""
    (folder / "import_ollama.bat").write_text(body, encoding="utf-8")


def _export_one(name: str, modality: str, dest: Path) -> dict:
    from navine.gguf_export import export_modality_gguf, export_text_gguf

    dest.parent.mkdir(parents=True, exist_ok=True)
    if modality == "text":
        path = export_text_gguf(name, out_path=dest)
    else:
        path = export_modality_gguf(name, modality, out_path=dest)
    return {"name": name, "ok": True, "path": str(path), "bytes": path.stat().st_size}


def _hardlink_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        import os

        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> int:
    from navine.gguf_export import write_modelfile_at

    export_dir = OUT_ROOT / "_exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, modality in EXPORTS:
        dest = export_dir / f"{name}.gguf"
        print(f"export {name} -> {dest}", flush=True)
        try:
            rows.append(_export_one(name, modality, dest))
            if modality == "text":
                write_modelfile_at(export_dir / f"{name}.Modelfile", name, f"{name}.gguf")
        except Exception as exc:
            rows.append({"name": name, "ok": False, "error": str(exc)})
            print(f"FAIL {name}: {exc}", flush=True)

    site_rows = []
    for site in SITES:
        folder = OUT_ROOT / site["name"]
        folder.mkdir(parents=True, exist_ok=True)
        bundle = {"site": site["name"], "port": site["port"], "files": []}
        mapping = [
            ("text.gguf", site["text"]),
            ("image.gguf", IMAGE_KEY),
            ("video.gguf", VIDEO_KEY),
        ]
        for out_name, key in mapping:
            src = export_dir / f"{key}.gguf"
            dst = folder / out_name
            if not src.exists():
                bundle["files"].append({"file": out_name, "ok": False, "error": f"missing export {key}"})
                continue
            _hardlink_or_copy(src, dst)
            bundle["files"].append({"file": out_name, "source": key, "bytes": dst.stat().st_size})
            if out_name == "text.gguf":
                write_modelfile_at(
                    folder / "Modelfile",
                    key,
                    "text.gguf",
                    system_label=SITE_LABELS.get(site["name"]),
                )
        tag = site["name"].lower().replace(" ", "-").replace("--", "-")
        _write_import_bat(folder, tag)
        site_rows.append(bundle)

    _write_import_help()

    ckpt_dir = OUT_ROOT / "_checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    for name in ("text_enterprise", "text_code", "image_enterprise_v2", "video_enterprise"):
        src = ROOT / "checkpoints" / name / "latest.pt"
        if src.exists():
            dst = ckpt_dir / f"{name}.pt"
            if dst.exists():
                dst.unlink()
            try:
                import os
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)

    manifest = {
        "output_root": str(OUT_ROOT),
        "exports": rows,
        "sites": site_rows,
    }
    (OUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (export_dir / "index.json").write_text(json.dumps({"format": "gguf", "models": rows}, indent=2), encoding="utf-8")
    ok = sum(1 for r in rows if r.get("ok")) 
    print(json.dumps(manifest, indent=2))
    return 0 if ok == len(EXPORTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
