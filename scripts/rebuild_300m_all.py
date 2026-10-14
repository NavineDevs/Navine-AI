from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_300m.log"
PY = ROOT / "venv" / "Scripts" / "python.exe"
CKPT = ROOT / "checkpoints"
PROOF = ROOT / "logs" / "verify_real_300m.json"


def _log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def _archive(name: str) -> None:
    src = CKPT / name
    if not src.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = CKPT / f"_archive_pre300m_{name}_{stamp}"
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    for fname in ("latest.pt", "best.pt"):
        p = src / fname
        if p.exists():
            p.unlink()
    _log(f"archived {name} -> {dst.name}")


def _seed_all() -> dict:
    sys.path.insert(0, str(ROOT))
    from navine.text.arch import apply_size_tier
    from navine.text.model import build_text_model
    from navine.image.model import NavineDiffusionModel
    from navine.video.model import NavineVideoModel
    from navine.voice.neural import NavineVoiceModel
    from navine.deepfake.model import build_deepfake_model, load_deepfake_config
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count
    from navine.utils.paths import get_checkpoint_dir
    import torch

    proof: dict = {"created_at": datetime.now(timezone.utc).isoformat(), "models": {}}

    text_cfg = apply_size_tier(load_config("text_enterprise"))
    text_model = build_text_model(text_cfg["model"], int(text_cfg["model"]["vocab_size"]))
    tp = assert_real_param_count(text_model, "text_enterprise")
    text_dir = get_checkpoint_dir("text_enterprise")
    text_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": text_model.state_dict(),
            "parameters": int(tp),
            "architecture": dict(text_cfg["model"]),
            "size_tier": text_cfg.get("size_tier"),
        },
        text_dir / "latest.pt",
    )
    proof["models"]["text_enterprise"] = tp
    _log(f"seeded text_enterprise {tp:,}")

    code_cfg = apply_size_tier(load_config("text_code"))
    code_model = build_text_model(code_cfg["model"], int(code_cfg["model"]["vocab_size"]))
    cp = assert_real_param_count(code_model, "text_code")
    code_dir = get_checkpoint_dir("text_code")
    code_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": code_model.state_dict(),
            "parameters": int(cp),
            "architecture": dict(code_cfg["model"]),
            "size_tier": code_cfg.get("size_tier"),
        },
        code_dir / "latest.pt",
    )
    proof["models"]["text_code"] = cp
    _log(f"seeded text_code {cp:,}")

    img_cfg = load_config("image_enterprise_v2")["model"]
    img = NavineDiffusionModel(**img_cfg)
    ip = assert_real_param_count(img, "image_enterprise_v2")
    img_dir = get_checkpoint_dir("image_enterprise_v2")
    img_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": img.state_dict(), "parameters": int(ip), "architecture": dict(img_cfg)},
        img_dir / "latest.pt",
    )
    proof["models"]["image_enterprise_v2"] = ip
    _log(f"seeded image_enterprise_v2 {ip:,}")

    vid_cfg = load_config("video_enterprise")["model"]
    vid = NavineVideoModel(**{
        k: vid_cfg[k]
        for k in ("frame_size", "num_frames", "in_channels", "hidden_dim", "num_layers")
        if k in vid_cfg
    })
    vp = assert_real_param_count(vid, "video_enterprise")
    vid_dir = get_checkpoint_dir("video_enterprise")
    vid_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": vid.state_dict(), "parameters": int(vp), "architecture": dict(vid_cfg)},
        vid_dir / "latest.pt",
    )
    proof["models"]["video_enterprise"] = vp
    _log(f"seeded video_enterprise {vp:,}")

    voice_cfg = load_config("voice_enterprise")["model"]
    voice = NavineVoiceModel(**{
        k: voice_cfg[k]
        for k in ("vocab_size", "hidden_dim", "num_layers", "mel_bins", "max_seq_len")
        if k in voice_cfg
    })
    vop = assert_real_param_count(voice, "voice")
    voice_dir = get_checkpoint_dir("voice")
    voice_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": voice.state_dict(), "parameters": int(vop), "architecture": dict(voice_cfg)},
        voice_dir / "latest.pt",
    )
    proof["models"]["voice"] = vop
    _log(f"seeded voice {vop:,}")

    df = build_deepfake_model(load_deepfake_config())
    dp = assert_real_param_count(df, "deepfake")
    df.save(get_checkpoint_dir("deepfake") / "latest.pt")
    proof["models"]["deepfake"] = dp
    _log(f"seeded deepfake {dp:,}")

    proof["total"] = int(sum(proof["models"].values()))
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    _log(f"proof written {PROOF} total={proof['total']:,}")
    return proof


def main() -> int:
    _log("=== rebuild_300m_all start ===")
    for name in (
        "text_enterprise",
        "text_code",
        "image_enterprise_v2",
        "video_enterprise",
        "voice",
        "voice_enterprise",
        "deepfake",
    ):
        _archive(name)
    proof = _seed_all()
    _log(
        "DONE "
        + ", ".join(f"{k}={v:,}" for k, v in proof["models"].items())
        + f" total={proof['total']:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
