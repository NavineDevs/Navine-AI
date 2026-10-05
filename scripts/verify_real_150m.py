from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
TARGET_MIN = 140_000_000
TARGET_MAX = 160_000_000


def _unique_param_count(model) -> Tuple[int, int]:
    seen = set()
    unique = 0
    naive = 0
    for p in model.parameters():
        if not p.requires_grad:
            continue
        naive += int(p.numel())
        ptr = int(p.data_ptr()) if hasattr(p, "data_ptr") else id(p)
        if ptr in seen:
            continue
        seen.add(ptr)
        unique += int(p.numel())
    return unique, naive


def _ckpt_unique(path: Path) -> int | None:
    if not path.exists():
        return None
    import torch

    payload = torch.load(str(path), map_location="cpu", weights_only=False)
    state = payload.get("model_state") if isinstance(payload, dict) else None
    if not isinstance(state, dict):
        state = {k: v for k, v in (payload or {}).items() if hasattr(v, "numel")} if isinstance(payload, dict) else {}
    seen = set()
    total = 0
    for value in state.values():
        if not hasattr(value, "numel"):
            continue
        ptr = int(value.data_ptr()) if hasattr(value, "data_ptr") else id(value)
        if ptr in seen:
            continue
        seen.add(ptr)
        total += int(value.numel())
    return total if total > 0 else None


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT))
    from navine.text.model import build_text_model
    from navine.image.model import NavineDiffusionModel
    from navine.video.model import NavineVideoModel
    from navine.voice.neural import NavineVoiceModel
    from navine.utils.config import load_config
    from navine.utils.paths import get_checkpoint_dir

    rows: List[Dict[str, Any]] = []
    ok_all = True

    text_names = [
        "text_enterprise",
        "text_code",
        "hitboyx23_ai",
        "hitboyx23_ai_python",
    ]
    for name in text_names:
        cfg = load_config(name)
        m = dict(cfg.get("model") or {})
        model = build_text_model(m, int(m.get("vocab_size", 12000)))
        unique, naive = _unique_param_count(model)
        ckpt = get_checkpoint_dir(name) / "latest.pt"
        ckpt_n = _ckpt_unique(ckpt)
        real = TARGET_MIN <= unique <= TARGET_MAX
        tied_ok = unique == naive
        row = {
            "name": name,
            "source": "built_from_config",
            "unique_params": unique,
            "naive_params": naive,
            "tied_weights_deduped": unique == model.count_parameters(),
            "count_parameters_api": model.count_parameters(),
            "checkpoint_unique_params": ckpt_n,
            "in_150m_band": real,
            "no_double_count": tied_ok or (unique == model.count_parameters()),
        }
        if not real:
            ok_all = False
        if ckpt_n is not None and abs(ckpt_n - unique) > max(10_000, int(unique * 0.05)):
            row["checkpoint_mismatch"] = True
            ok_all = False
        rows.append(row)

    img = NavineDiffusionModel(**load_config("image_enterprise_v2")["model"])
    u, n = _unique_param_count(img)
    ck = _ckpt_unique(get_checkpoint_dir("image_enterprise_v2") / "latest.pt")
    rows.append(
        {
            "name": "image_enterprise_v2",
            "unique_params": u,
            "naive_params": n,
            "count_parameters_api": img.count_parameters(),
            "checkpoint_unique_params": ck,
            "in_150m_band": TARGET_MIN <= u <= TARGET_MAX,
            "fp32_weight_bytes": u * 4,
        }
    )
    if not (TARGET_MIN <= u <= TARGET_MAX):
        ok_all = False

    vid = NavineVideoModel(**load_config("video_enterprise")["model"])
    u, n = _unique_param_count(vid)
    ck = _ckpt_unique(get_checkpoint_dir("video_enterprise") / "latest.pt")
    rows.append(
        {
            "name": "video_enterprise",
            "unique_params": u,
            "naive_params": n,
            "count_parameters_api": vid.count_parameters(),
            "checkpoint_unique_params": ck,
            "in_150m_band": TARGET_MIN <= u <= TARGET_MAX,
            "fp32_weight_bytes": u * 4,
        }
    )
    if not (TARGET_MIN <= u <= TARGET_MAX):
        ok_all = False

    vc = load_config("voice_enterprise")["model"]
    voice = NavineVoiceModel(
        **{k: vc[k] for k in ("vocab_size", "hidden_dim", "num_layers", "mel_bins", "max_seq_len")}
    )
    u, n = _unique_param_count(voice)
    ck = _ckpt_unique(get_checkpoint_dir("voice") / "latest.pt")
    rows.append(
        {
            "name": "voice_enterprise",
            "unique_params": u,
            "naive_params": n,
            "count_parameters_api": voice.count_parameters(),
            "checkpoint_unique_params": ck,
            "in_150m_band": TARGET_MIN <= u <= TARGET_MAX,
            "fp32_weight_bytes": u * 4,
        }
    )
    if not (TARGET_MIN <= u <= TARGET_MAX):
        ok_all = False

    report = {
        "ok": ok_all,
        "method": "sum(unique Parameter/Tensor storage via data_ptr); not UI labels",
        "band": [TARGET_MIN, TARGET_MAX],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "items": rows,
    }
    out = ROOT / "logs" / "verify_real_150m.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"wrote {out}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
