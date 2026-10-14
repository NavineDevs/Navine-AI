from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_gpt3_760m_modalities.log"
PROOF = ROOT / "logs" / "verify_real_gpt3_760m_all.json"
CKPT = ROOT / "checkpoints"


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _archive(name: str) -> None:
    src = CKPT / name
    if not src.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = CKPT / f"_archive_pre760m_{name}_{stamp}"
    dst.mkdir(parents=True, exist_ok=True)
    moved = 0
    for fname in ("latest.pt", "best.pt", "config.json", "tokenizer.json", "train_report.json"):
        path = src / fname
        if not path.exists():
            continue
        target = dst / fname
        try:
            shutil.move(str(path), str(target))
            moved += 1
        except OSError:
            try:
                shutil.copy2(path, target)
                path.unlink()
                moved += 1
            except OSError as exc:
                _log(f"archive skip {name}/{fname}: {exc}")
    _log(f"archived {name} ({moved} files) -> {dst.name}")


def main() -> None:
    import torch
    from navine.deepfake.model import build_deepfake_model, load_deepfake_config
    from navine.image.model import NavineDiffusionModel
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count
    from navine.utils.paths import get_checkpoint_dir
    from navine.video.model import NavineVideoModel
    from navine.voice.neural import NavineVoiceModel

    _log("=== rebuild multimodal gpt3_760m start ===")
    for name in ("image_enterprise_v2", "video_enterprise", "voice", "deepfake"):
        _archive(name)

    proof = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tier": "gpt3_760m",
        "note": (
            "All modalities ~760M GPT-3 Medium class. "
            "Detective/think/OSINT/analyze use text_enterprise (~701M)."
        ),
        "models": {},
    }

    img_cfg = load_config("image_enterprise_v2")["model"]
    img_kwargs = {
        k: img_cfg[k]
        for k in (
            "image_size",
            "in_channels",
            "base_channels",
            "channel_mults",
            "num_res_blocks",
            "time_emb_dim",
            "text_emb_dim",
            "attn_resolutions",
            "text_max_len",
            "text_layers",
            "text_heads",
            "min_snr_gamma",
            "arch_version",
        )
        if k in img_cfg
    }
    img = NavineDiffusionModel(**img_kwargs)
    ip = assert_real_param_count(img, "image_enterprise_v2", size_tier="gpt3_760m")
    img_dir = get_checkpoint_dir("image_enterprise_v2")
    img_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": img.state_dict(),
            "parameters": int(ip),
            "architecture": dict(img_cfg),
            "size_tier": "gpt3_760m",
        },
        img_dir / "latest.pt",
    )
    proof["models"]["image_enterprise_v2"] = int(ip)
    _log(f"seeded image_enterprise_v2 {ip:,}")
    del img

    vid_cfg = load_config("video_enterprise")["model"]
    vid = NavineVideoModel(
        **{
            k: vid_cfg[k]
            for k in ("frame_size", "num_frames", "in_channels", "hidden_dim", "num_layers")
            if k in vid_cfg
        }
    )
    vp = assert_real_param_count(vid, "video_enterprise", size_tier="gpt3_760m")
    vid_dir = get_checkpoint_dir("video_enterprise")
    vid_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": vid.state_dict(),
            "parameters": int(vp),
            "architecture": dict(vid_cfg),
            "size_tier": "gpt3_760m",
        },
        vid_dir / "latest.pt",
    )
    proof["models"]["video_enterprise"] = int(vp)
    _log(f"seeded video_enterprise {vp:,}")
    del vid

    voice_cfg = load_config("voice_enterprise")["model"]
    voice = NavineVoiceModel(
        **{
            k: voice_cfg[k]
            for k in ("vocab_size", "hidden_dim", "num_layers", "mel_bins", "max_seq_len")
            if k in voice_cfg
        }
    )
    vop = assert_real_param_count(voice, "voice", size_tier="gpt3_760m")
    voice_dir = get_checkpoint_dir("voice")
    voice_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": voice.state_dict(),
            "parameters": int(vop),
            "architecture": dict(voice_cfg),
            "size_tier": "gpt3_760m",
        },
        voice_dir / "latest.pt",
    )
    proof["models"]["voice"] = int(vop)
    _log(f"seeded voice {vop:,}")
    del voice

    df = build_deepfake_model(load_deepfake_config())
    dp = assert_real_param_count(df, "deepfake", size_tier="gpt3_760m")
    df.save(get_checkpoint_dir("deepfake") / "latest.pt")
    proof["models"]["deepfake"] = int(dp)
    _log(f"seeded deepfake {dp:,}")
    del df

    for name in ("text_enterprise", "text_code"):
        latest = CKPT / name / "latest.pt"
        if not latest.exists():
            continue
        try:
            payload = torch.load(str(latest), map_location="cpu", weights_only=False)
            params = int(payload.get("parameters") or 0)
            if params <= 0 and isinstance(payload.get("model_state"), dict):
                params = sum(int(v.numel()) for v in payload["model_state"].values() if hasattr(v, "numel"))
            if params > 0:
                proof["models"][name] = params
                _log(f"kept {name} {params:,}")
        except Exception as exc:
            _log(f"skip {name}: {exc}")

    proof["total"] = int(sum(proof["models"].values()))
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    _log(f"proof -> {PROOF} total={proof['total']:,}")
    _log("=== rebuild multimodal gpt3_760m done ===")


if __name__ == "__main__":
    main()
