"""Seed SFW video sequence buckets from local frame pools (no external models)."""

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
    "explicit",
)
OBJECT_HINTS = (
    "mug",
    "cup",
    "table",
    "chair",
    "car",
    "object",
    "bottle",
    "food",
    "flower",
    "building",
    "desk",
    "lamp",
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
)


def _meta_nsfw(seq_dir: Path) -> bool:
    meta = seq_dir / "meta.json"
    if not meta.exists():
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        if data.get("is_nsfw") is True:
            return True
        if data.get("sfw") is True:
            return False
        url = str(data.get("url") or "").lower()
        return any(h in url for h in NSFW_HINTS)
    except Exception:
        return False


def _classify_seq(seq_dir: Path) -> str:
    text = str(seq_dir).lower()
    if any(h in text for h in NSFW_HINTS) or _meta_nsfw(seq_dir):
        return "skip"
    meta = seq_dir / "meta.json"
    cap = ""
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            cap = str(data.get("caption") or data.get("url") or "").lower()
        except Exception:
            pass
    if any(h in cap for h in OBJECT_HINTS):
        return "objects"
    if any(h in cap for h in PEOPLE_HINTS):
        return "people"
    return "people"


def _copy_seq(src: Path, dst_root: Path, name: str, caption: str, sfw: bool = True) -> None:
    frames = sorted(src.glob("frame_*.png"))
    if len(frames) < 8:
        frames = sorted(src.glob("*.png")) + sorted(src.glob("*.jpg"))
    if len(frames) < 8:
        return
    out = dst_root / name
    if out.exists():
        shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    for i, fp in enumerate(frames[:32]):
        shutil.copy2(fp, out / f"frame_{i:04d}.png")
    meta = {"caption": caption, "sfw": sfw, "source": str(src)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main(max_each: int = 40) -> None:
    root = get_project_root()
    people_dst = root / "data" / "video" / "sfw" / "people"
    objects_dst = root / "data" / "video" / "sfw" / "objects"
    people_dst.mkdir(parents=True, exist_ok=True)
    objects_dst.mkdir(parents=True, exist_ok=True)
    sources = [
        root / "data" / "video" / "ingested",
        root / "data" / "video" / "learned",
        root / "data" / "video" / "samples",
        root / "data" / "image" / "sfw" / "people",
        root / "data" / "image" / "sfw" / "objects",
    ]
    candidates: dict[str, list] = {"people": [], "objects": []}
    for src_root in sources:
        if not src_root.exists():
            continue
        seq_dirs = [d for d in src_root.iterdir() if d.is_dir()]
        if seq_dirs:
            for seq in seq_dirs:
                kind = _classify_seq(seq)
                if kind in candidates:
                    candidates[kind].append(seq)
        else:
            imgs = sorted(src_root.glob("*.png")) + sorted(src_root.glob("*.jpg"))
            if len(imgs) >= 16:
                tmp = src_root
                kind = _classify_seq(tmp)
                if kind in candidates:
                    candidates[kind].append(tmp)
    random.seed(42)
    for kind, dst in (("people", people_dst), ("objects", objects_dst)):
        pool = candidates[kind]
        random.shuffle(pool)
        count = 0
        for seq in pool:
            if count >= max_each:
                break
            cap = "sfw clothed person walking, natural motion" if kind == "people" else "sfw object still life, subtle camera motion"
            _copy_seq(seq, dst, f"seq_{count:04d}", cap)
            count += 1
        print(f"Seeded {count} sequences -> {dst}")


if __name__ == "__main__":
    main()
