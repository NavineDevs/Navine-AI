"""Seed SFW people/objects buckets from local image pools (no external models)."""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

from navine.utils.paths import get_project_root

NSFW_HINTS = (
    "hentai",
    "porn",
    "nsfw",
    "nude",
    "naked",
    "xxx",
    "erotic",
    "ecchi",
    "boob",
    "sex",
    "explicit",
)
OBJECT_HINTS = (
    "mug",
    "cup",
    "table",
    "chair",
    "car",
    "bike",
    "book",
    "phone",
    "laptop",
    "bottle",
    "food",
    "flower",
    "tree",
    "building",
    "room",
    "desk",
    "lamp",
    "bag",
    "shoe",
    "clock",
)
PEOPLE_HINTS = (
    "person",
    "people",
    "human",
    "man",
    "woman",
    "girl",
    "boy",
    "portrait",
    "face",
    "selfie",
    "couple",
)


def _is_nsfw_name(path: Path) -> bool:
    text = str(path).lower()
    return any(h in text for h in NSFW_HINTS)


def _sidecar_nsfw(path: Path) -> bool:
    for side in (path.with_suffix(path.suffix + ".json"), path.with_suffix(".json")):
        if not side.exists():
            continue
        try:
            data = json.loads(side.read_text(encoding="utf-8"))
            if data.get("is_nsfw") is True:
                return True
            if data.get("sfw") is True:
                return False
            cap = str(data.get("caption") or "").lower()
            if any(h in cap for h in NSFW_HINTS):
                return True
        except Exception:
            continue
    return False


def _guess_bucket(path: Path) -> str:
    text = str(path).lower()
    if any(h in text for h in OBJECT_HINTS):
        return "objects"
    if any(h in text for h in PEOPLE_HINTS) or "human" in text:
        return "people"
    return "people" if hash(path.name) % 3 else "objects"


def seed_sfw_buckets(people_max: int = 400, objects_max: int = 300) -> dict:
    root = get_project_root()
    sources = [
        root / "data" / "image" / "ingested",
        root / "data" / "image" / "learned",
        root / "data" / "image" / "samples",
        root / "data" / "image" / "human",
        root / "data" / "train" / "human",
    ]
    people_dir = root / "data" / "image" / "sfw" / "people"
    objects_dir = root / "data" / "image" / "sfw" / "objects"
    people_dir.mkdir(parents=True, exist_ok=True)
    objects_dir.mkdir(parents=True, exist_ok=True)

    candidates: list[Path] = []
    for src in sources:
        if not src.exists():
            continue
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            for path in src.rglob(ext):
                if _is_nsfw_name(path) or _sidecar_nsfw(path):
                    continue
                if "nsfw" in str(path).lower() and "sfw" not in str(path).lower():
                    continue
                candidates.append(path)

    rng = random.Random(42)
    rng.shuffle(candidates)
    counts = {"people": 0, "objects": 0}
    for path in candidates:
        bucket = _guess_bucket(path)
        if bucket == "people" and counts["people"] >= people_max:
            bucket = "objects" if counts["objects"] < objects_max else ""
        if bucket == "objects" and counts["objects"] >= objects_max:
            bucket = "people" if counts["people"] < people_max else ""
        if not bucket:
            if counts["people"] >= people_max and counts["objects"] >= objects_max:
                break
            continue
        dest_dir = people_dir if bucket == "people" else objects_dir
        dest = dest_dir / f"sfw_{bucket}_{counts[bucket]:04d}{path.suffix.lower()}"
        if not dest.exists():
            try:
                shutil.copy2(path, dest)
            except OSError:
                continue
        caption = (
            "sfw clothed young adult person portrait, natural light"
            if bucket == "people"
            else "sfw everyday object on a table, clean photo"
        )
        meta = {
            "caption": caption,
            "sfw": True,
            "is_nsfw": False,
            "rating": "sfw",
            "source": str(path),
            "category": "sfw" if bucket == "people" else "object",
        }
        dest.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        counts[bucket] += 1
    print(f"SFW seed complete: people={counts['people']} objects={counts['objects']}")
    return counts


if __name__ == "__main__":
    seed_sfw_buckets()
