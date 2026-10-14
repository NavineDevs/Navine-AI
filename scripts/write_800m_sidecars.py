from __future__ import annotations

import json
from pathlib import Path

from navine.deepfake.model import build_deepfake_model, load_deepfake_config
from navine.image.model import NavineDiffusionModel
from navine.text.arch import apply_size_tier, build_text_model
from navine.utils.config import load_config
from navine.utils.param_verify import assert_real_param_count
from navine.utils.paths import get_checkpoint_dir, get_project_root
from navine.video.model import NavineVideoModel
from navine.voice.neural import NavineVoiceModel


def main() -> None:
    rows = {}
    for name in ("text_enterprise", "text_code"):
        cfg = apply_size_tier(load_config(name), tier="gpt3_800m")
        mcfg = dict(cfg["model"])
        model = build_text_model(mcfg, vocab_size=int(mcfg.get("vocab_size") or 12000))
        rows[name] = assert_real_param_count(model, name, size_tier="gpt3_800m")
        del model

    img_full = load_config("image_enterprise_v2")
    img_cfg = dict(img_full["model"])
    diff = dict(img_full.get("diffusion") or {})
    keys = (
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
    kwargs = {k: img_cfg[k] for k in keys if k in img_cfg}
    kwargs.update({k: diff[k] for k in ("timesteps", "beta_start", "beta_end", "beta_schedule") if k in diff})
    img = NavineDiffusionModel(**kwargs)
    rows["image_enterprise_v2"] = assert_real_param_count(img, "image", size_tier="gpt3_800m")
    del img

    vid_cfg = load_config("video_enterprise")["model"]
    vid = NavineVideoModel(
        **{k: vid_cfg[k] for k in ("frame_size", "num_frames", "in_channels", "hidden_dim", "num_layers") if k in vid_cfg}
    )
    rows["video_enterprise"] = assert_real_param_count(vid, "video", size_tier="gpt3_800m")
    del vid

    voice_cfg = load_config("voice_enterprise")["model"]
    voice = NavineVoiceModel(
        **{k: voice_cfg[k] for k in ("vocab_size", "hidden_dim", "num_layers", "mel_bins", "max_seq_len") if k in voice_cfg}
    )
    rows["voice"] = assert_real_param_count(voice, "voice", size_tier="gpt3_800m")
    del voice

    df = build_deepfake_model(load_deepfake_config())
    rows["deepfake"] = assert_real_param_count(df, "deepfake", size_tier="gpt3_800m")
    del df

    root = get_project_root()
    for name, params in rows.items():
        ckpt = get_checkpoint_dir(name)
        ckpt.mkdir(parents=True, exist_ok=True)
        payload = {
            "parameters": int(params),
            "name": name,
            "size_tier": "gpt3_800m",
            "unique_trainable": True,
        }
        (ckpt / "config.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {ckpt / 'config.json'} {params:,}")

    proof = {
        "tier": "gpt3_800m_plus",
        "target": "800M+ unique trainable params",
        "models": rows,
        "total": int(sum(rows.values())),
    }
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "verify_true_800m.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    cache = logs / "model_stats_cache.json"
    if cache.exists():
        cache.unlink()
        print("cleared model_stats_cache")
    print("ALL", {k: round(v / 1_000_000, 2) for k, v in rows.items()}, "total_B", round(proof["total"] / 1e9, 2))
    print("MIN_OK", min(rows.values()) >= 800_000_000)


if __name__ == "__main__":
    main()
