import json
import os
import random
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "image" / "balanced_mix"
EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

CAPS = {
    "sky": (
        "clear blue sky with soft white clouds, wide open atmosphere, natural daylight",
        False,
    ),
    "human": (
        "photorealistic adult photo, natural skin texture, natural lighting, sharp focus",
        True,
    ),
    "hentai": (
        "nude hentai anime girl, detailed face and body, sharp lineart, vibrant colors",
        True,
    ),
    "porn": (
        "photorealistic explicit adult photo, detailed anatomy, pussy boobs ass, natural lighting, sharp focus",
        True,
    ),
}

SOURCES = {
    "sky": [
        ROOT / "data" / "image" / "overfit_sky1",
        ROOT / "data" / "image" / "overfit_sky",
        ROOT / "data" / "image" / "sfw" / "skies",
    ],
    "human": [
        ROOT / "data" / "image" / "overfit_human",
        ROOT / "data" / "nsfw" / "local" / "human",
    ],
    "hentai": [
        ROOT / "data" / "image" / "overfit_hentai",
        ROOT / "data" / "image" / "overfit_hentai8",
        ROOT / "data" / "nsfw" / "local" / "hentai",
    ],
    "porn": [
        ROOT / "data" / "image" / "overfit_porn",
        ROOT / "data" / "nsfw" / "local" / "porn",
    ],
}

LIMITS = {"sky": 20, "human": 14, "hentai": 14, "porn": 14}


def _link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _images(folder: Path):
    if not folder.exists():
        return []
    rows = []
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTS:
            rows.append(path)
    return rows


def _write_sidecar(dst: Path, category: str) -> None:
    caption, is_nsfw = CAPS[category]
    meta = {
        "caption": caption,
        "prompt": caption,
        "media_category": category,
        "is_nsfw": is_nsfw,
        "sfw": not is_nsfw,
        "rating": "explicit" if is_nsfw else "sfw",
    }
    (dst.parent / f"{dst.stem}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def build() -> dict:
    rng = random.Random(23)
    if OUT.exists():
        shutil.rmtree(OUT)
    counts = {}
    for category, folders in SOURCES.items():
        picked = []
        seen = set()
        for folder in folders:
            for path in _images(folder):
                key = str(path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                picked.append(path)
        rng.shuffle(picked)
        limit = LIMITS[category]
        prefer = []
        rest = []
        for path in picked:
            low = str(path).lower()
            if "overfit" in low:
                prefer.append(path)
            else:
                rest.append(path)
        ordered = prefer + rest
        selected = ordered[:limit]
        dest = OUT / category
        dest.mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(selected):
            dst = dest / f"{category}_{i:03d}{src.suffix.lower()}"
            _link_or_copy(src, dst)
            _write_sidecar(dst, category)
        counts[category] = len(selected)
    summary = {"out": str(OUT), "counts": counts, "total": sum(counts.values())}
    (OUT / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
