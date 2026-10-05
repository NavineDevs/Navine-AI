"""Rebuild text models only to fixed gpt3_800m (even head_dim)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import torch
    from navine.text.arch import apply_size_tier, build_or_upgrade_text_model
    from navine.text.tokenizer import NavineTokenizer
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count
    from navine.utils.paths import get_checkpoint_dir

    proof_path = ROOT / "logs" / "verify_true_800m.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8")) if proof_path.exists() else {
        "tier": "gpt3_800m",
        "target": "780M-820M unique trainable params",
        "models": {},
    }
    proof["created_at"] = datetime.now(timezone.utc).isoformat()
    proof["text_fix"] = "d_model=1632 head_dim=102 even for RoPE"

    for namespace, cfg_name in (("text_enterprise", "text_enterprise"), ("text_code", "text_code")):
        cfg = apply_size_tier(load_config(cfg_name), tier="gpt3_800m")
        model_cfg = cfg["model"]
        assert int(model_cfg["d_model"]) % int(model_cfg["n_heads"]) == 0
        head = int(model_cfg["d_model"]) // int(model_cfg["n_heads"])
        assert head % 2 == 0, f"odd head_dim {head}"
        ckpt_dir = get_checkpoint_dir(namespace)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        tok_path = ckpt_dir / "tokenizer.json"
        tokenizer = NavineTokenizer.load(tok_path) if tok_path.exists() else NavineTokenizer(12000, use_bpe=True)
        if not tok_path.exists():
            tokenizer.build(["Hello from Navine AI.", "def add(a, b): return a + b"], use_bpe=True)
            tokenizer.save(tok_path)
        source = ckpt_dir / "latest.pt"
        model, meta = build_or_upgrade_text_model(
            cfg,
            vocab_size=len(tokenizer.token_to_id),
            checkpoint_path=source if source.exists() else None,
            device="cpu",
            force_fresh=False,
            max_missing_ratio=0.95,
        )
        params = assert_real_param_count(model, namespace, size_tier="gpt3_800m")
        torch.save(
            {
                "model_state": model.state_dict(),
                "config": model.architecture_config(),
                "parameters": int(params),
                "size_tier": "gpt3_800m",
                "upgrade_meta": meta,
            },
            ckpt_dir / "latest.pt",
        )
        proof["models"][namespace] = int(params)
        print(f"{namespace}: {params:,} head_dim={head} meta={meta.get('note')}", flush=True)
        del model

    proof["total"] = int(sum(int(v) for v in proof["models"].values()))
    proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
