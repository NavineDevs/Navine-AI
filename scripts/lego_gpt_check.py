"""Smoke-check that gpt3_1b LEGO pieces and param count are valid."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from navine.text.arch import apply_size_tier
    from navine.text.model import build_text_model
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count, range_for_tier

    cfg = apply_size_tier(load_config("text_enterprise"))
    model_cfg = dict(cfg["model"])
    tier = str(cfg.get("size_tier") or "gpt3_1b")
    model = build_text_model(model_cfg, int(model_cfg["vocab_size"]))
    params = int(model.count_parameters())
    lo, hi = range_for_tier(tier)
    arch = model.architecture_config()
    print(f"tier={tier}")
    print(
        "lego="
        f"embed+tie={arch.get('tie_embeddings')} "
        f"rope={arch.get('use_rope')} "
        f"swiglu={arch.get('use_swiglu')} "
        f"rms={arch.get('use_rms_norm')} "
        f"layers={arch.get('n_layers')} "
        f"d={arch.get('d_model')} "
        f"heads={arch.get('n_heads')} "
        f"ff={arch.get('d_ff')}"
    )
    print(f"params={params:,}")
    print(f"range={lo:,}..{hi:,}")
    assert_real_param_count(model, f"lego:{tier}", size_tier=tier)
    if params < 1_000_000_000:
        print("FAIL: params below true 1B")
        return 1
    print("OK: LEGO check passed (>=1B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
