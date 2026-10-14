from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT))
    from navine.text.arch import apply_size_tier
    from navine.text.model import build_text_model
    from navine.image.model import NavineDiffusionModel
    from navine.video.model import NavineVideoModel
    from navine.voice.neural import NavineVoiceModel
    from navine.deepfake.model import build_deepfake_model, load_deepfake_config
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count

    rows = {}
    text_cfg = apply_size_tier(load_config("text_enterprise"))
    rows["text_enterprise"] = assert_real_param_count(
        build_text_model(text_cfg["model"], int(text_cfg["model"]["vocab_size"])),
        "text_enterprise",
    )
    img = NavineDiffusionModel(**load_config("image_enterprise_v2")["model"])
    rows["image_enterprise_v2"] = assert_real_param_count(img, "image_enterprise_v2")
    vid_cfg = load_config("video_enterprise")["model"]
    rows["video_enterprise"] = assert_real_param_count(
        NavineVideoModel(
            **{
                k: vid_cfg[k]
                for k in ("frame_size", "num_frames", "in_channels", "hidden_dim", "num_layers")
                if k in vid_cfg
            }
        ),
        "video_enterprise",
    )
    voice_cfg = load_config("voice_enterprise")["model"]
    rows["voice"] = assert_real_param_count(
        NavineVoiceModel(
            **{
                k: voice_cfg[k]
                for k in ("vocab_size", "hidden_dim", "num_layers", "mel_bins", "max_seq_len")
                if k in voice_cfg
            }
        ),
        "voice",
    )
    rows["deepfake"] = assert_real_param_count(build_deepfake_model(load_deepfake_config()), "deepfake")
    out = {"models": rows, "total": int(sum(rows.values()))}
    path = ROOT / "logs" / "verify_real_300m.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
