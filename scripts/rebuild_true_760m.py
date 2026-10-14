from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_true_760m.log"
PROOF = ROOT / "logs" / "verify_true_760m.json"
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
    dst = CKPT / f"_archive_true760m_{name}_{stamp}"
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
    from navine.text.arch import apply_size_tier, build_or_upgrade_text_model
    from navine.text.tokenizer import NavineTokenizer
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count
    from navine.utils.paths import get_checkpoint_dir
    from navine.video.model import NavineVideoModel
    from navine.voice.neural import NavineVoiceModel

    _log("=== rebuild true ~760M start ===")
    proof = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tier": "gpt3_760m",
        "target": "740M-780M unique trainable params",
        "models": {},
    }

    for namespace, cfg_name in (
        ("text_enterprise", "text_enterprise"),
        ("text_code", "text_code"),
    ):
        _archive_latest(namespace)
        cfg = apply_size_tier(load_config(cfg_name))
        ckpt_dir = get_checkpoint_dir(namespace)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        tok_path = ckpt_dir / "tokenizer.json"
        if tok_path.exists():
            tokenizer = NavineTokenizer.load(tok_path)
        else:
            tokenizer = NavineTokenizer(12000, use_bpe=True)
            tokenizer.build(
                [
                    "Hello from Navine AI.",
                    "def add(a, b): return a + b",
                    "Explain gravity briefly.",
                ],
                use_bpe=True,
            )
            tokenizer.save(tok_path)
        archived = list((CKPT.glob(f"_archive_true760m_{namespace}_*/latest.pt")))
        source = archived[-1] if archived else None
        model, meta = build_or_upgrade_text_model(
            cfg,
            vocab_size=len(tokenizer.token_to_id),
            checkpoint_path=source,
            device="cpu",
            force_fresh=False,
            max_missing_ratio=0.9,
        )
        params = assert_real_param_count(model, namespace, size_tier="gpt3_760m")
        torch.save(
            {
                "model_state": model.state_dict(),
                "config": model.architecture_config(),
                "parameters": int(params),
                "size_tier": "gpt3_760m",
                "upgrade_meta": meta,
            },
            ckpt_dir / "latest.pt",
        )
        proof["models"][namespace] = int(params)
        _log(f"seeded {namespace} {params:,}")
        del model

    for name in ("image_enterprise_v2", "video_enterprise", "voice", "deepfake"):
        _archive_latest(name)

    img_cfg = load_config("image_enterprise_v2")["model"]
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
                "min_snr_gamma",
                "arch_version",
            )
            if k in img_cfg
        }
    )
    ip = assert_real_param_count(img, "image_enterprise_v2", size_tier="gpt3_760m")
    img_dir = get_checkpoint_dir("image_enterprise_v2")
    img_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": img.state_dict(), "parameters": int(ip), "architecture": dict(img_cfg), "size_tier": "gpt3_760m"},
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
        {"model": vid.state_dict(), "parameters": int(vp), "architecture": dict(vid_cfg), "size_tier": "gpt3_760m"},
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
        {"model": voice.state_dict(), "parameters": int(vop), "architecture": dict(voice_cfg), "size_tier": "gpt3_760m"},
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

    proof["total"] = int(sum(proof["models"].values()))
    PROOF.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    _log(f"proof -> {PROOF} total={proof['total']:,}")
    _log("=== rebuild true ~760M done ===")


if __name__ == "__main__":
    main()
