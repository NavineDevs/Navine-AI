from __future__ import annotations

import gc
import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_true_1b_modal.log"
PROOF = ROOT / "logs" / "verify_true_1b_modal.json"
CKPT = ROOT / "checkpoints"


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _archive_latest(name: str) -> None:
    import shutil

    src = CKPT / name
    if not src.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = CKPT / f"_archive_pre1b_{name}_{stamp}"
    dst.mkdir(parents=True, exist_ok=True)
    for fname in ("latest.pt", "best.pt", "config.json"):
        path = src / fname
        if path.exists():
            try:
                shutil.move(str(path), str(dst / fname))
            except OSError:
                shutil.copy2(path, dst / fname)
                path.unlink(missing_ok=True)
    _log(f"archived {name} -> {dst.name}")


def main() -> None:
    import torch
    from navine.deepfake.model import build_deepfake_model, load_deepfake_config
    from navine.image.model import NavineDiffusionModel
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count
    from navine.utils.paths import get_checkpoint_dir
    from navine.video.model import NavineVideoModel
    from navine.voice.neural import NavineVoiceModel

    _log("=== rebuild true 1B+ multimodal start ===")
    proof = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tier": "gpt3_1b",
        "target": "1.00B+ unique trainable params",
        "models": {},
    }

    for name in ("image_enterprise_v2", "video_enterprise", "voice", "deepfake"):
        _archive_latest(name)

    img_cfg = dict(load_config("image_enterprise_v2")["model"])
    img_cfg["size_tier"] = "gpt3_1b"
    img = NavineDiffusionModel(
        **{
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
            )
            if k in img_cfg
        }
    )
    params = assert_real_param_count(img, "image_enterprise_v2", size_tier="gpt3_1b")
    img_dir = get_checkpoint_dir("image_enterprise_v2")
    img_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": img.state_dict(),
            "parameters": int(params),
            "config": img_cfg,
            "architecture": img_cfg,
            "size_tier": "gpt3_1b",
        },
        img_dir / "latest.pt",
    )
    proof["models"]["image_enterprise_v2"] = int(params)
    (img_dir / "config.json").write_text(
        json.dumps(
            {"parameters": int(params), "name": "image_enterprise_v2", "size_tier": "gpt3_1b", "unique_trainable": True},
            indent=2,
        ),
        encoding="utf-8",
    )
    _log(f"seeded image_enterprise_v2 {params:,}")
    del img
    gc.collect()

    vid_cfg = dict(load_config("video_enterprise")["model"])
    vid_cfg["size_tier"] = "gpt3_1b"
    vid = NavineVideoModel(
        **{k: vid_cfg[k] for k in ("frame_size", "num_frames", "in_channels", "hidden_dim", "num_layers") if k in vid_cfg}
    )
    params = assert_real_param_count(vid, "video_enterprise", size_tier="gpt3_1b")
    vid_dir = get_checkpoint_dir("video_enterprise")
    vid_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": vid.state_dict(),
            "parameters": int(params),
            "architecture": vid_cfg,
            "size_tier": "gpt3_1b",
        },
        vid_dir / "latest.pt",
    )
    proof["models"]["video_enterprise"] = int(params)
    (vid_dir / "config.json").write_text(
        json.dumps(
            {"parameters": int(params), "name": "video_enterprise", "size_tier": "gpt3_1b", "unique_trainable": True},
            indent=2,
        ),
        encoding="utf-8",
    )
    _log(f"seeded video_enterprise {params:,}")
    del vid
    gc.collect()

    voice_cfg = dict(load_config("voice_enterprise")["model"])
    voice_cfg["size_tier"] = "gpt3_1b"
    voice = NavineVoiceModel(
        **{k: voice_cfg[k] for k in ("vocab_size", "hidden_dim", "num_layers", "mel_bins", "max_seq_len") if k in voice_cfg}
    )
    params = assert_real_param_count(voice, "voice", size_tier="gpt3_1b")
    voice_dir = get_checkpoint_dir("voice")
    voice_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": voice.state_dict(),
            "parameters": int(params),
            "architecture": voice_cfg,
            "size_tier": "gpt3_1b",
        },
        voice_dir / "latest.pt",
    )
    proof["models"]["voice"] = int(params)
    (voice_dir / "config.json").write_text(
        json.dumps(
            {"parameters": int(params), "name": "voice", "size_tier": "gpt3_1b", "unique_trainable": True},
            indent=2,
        ),
        encoding="utf-8",
    )
    _log(f"seeded voice {params:,}")
    del voice
    gc.collect()

    df_cfg = dict(load_deepfake_config())
    df_cfg["size_tier"] = "gpt3_1b"
    deepfake = build_deepfake_model(df_cfg)
    params = assert_real_param_count(deepfake, "deepfake", size_tier="gpt3_1b")
    df_dir = get_checkpoint_dir("deepfake")
    df_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": deepfake.state_dict(),
            "parameters": int(params),
            "architecture": df_cfg,
            "size_tier": "gpt3_1b",
        },
        df_dir / "latest.pt",
    )
    proof["models"]["deepfake"] = int(params)
    (df_dir / "config.json").write_text(
        json.dumps(
            {"parameters": int(params), "name": "deepfake", "size_tier": "gpt3_1b", "unique_trainable": True},
            indent=2,
        ),
        encoding="utf-8",
    )
    _log(f"seeded deepfake {params:,}")
    del deepfake
    gc.collect()

    proof["total"] = int(sum(proof["models"].values()))
    PROOF.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    cache = ROOT / "logs" / "model_stats_cache.json"
    if cache.exists():
        cache.unlink()
        _log("cleared model_stats_cache")
    _log(f"proof written {PROOF} total={proof['total']:,}")
    _log("=== rebuild true 1B+ multimodal done ===")


if __name__ == "__main__":
    main()
