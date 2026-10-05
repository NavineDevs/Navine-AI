from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_gpt3_760m.log"
PROOF = ROOT / "logs" / "verify_real_gpt3_760m.json"


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def rebuild_text(config_name: str, namespace: str) -> dict:
    import torch
    from navine.text.arch import apply_size_tier, archive_text_checkpoint, build_or_upgrade_text_model
    from navine.text.tokenizer import NavineTokenizer
    from navine.utils.config import load_config
    from navine.utils.param_verify import assert_real_param_count
    from navine.utils.paths import get_checkpoint_dir

    cfg = apply_size_tier(load_config(config_name))
    ckpt_dir = get_checkpoint_dir(namespace)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    archive_text_checkpoint(ckpt_dir, label=f"archive_pre_gpt3_760m_{int(time.time())}")
    tok_path = ckpt_dir / "tokenizer.json"
    if tok_path.exists():
        tokenizer = NavineTokenizer.load(tok_path)
    else:
        tokenizer = NavineTokenizer(int((cfg.get("model") or {}).get("vocab_size") or 12000), use_bpe=True)
        seed_texts = [
            "Hello from Navine AI.",
            "def add(a, b): return a + b",
            "Explain gravity in two sentences.",
        ]
        tokenizer.build(seed_texts, use_bpe=True)
        tokenizer.save(tok_path)
    model, meta = build_or_upgrade_text_model(
        cfg,
        vocab_size=len(tokenizer.token_to_id),
        checkpoint_path=(ckpt_dir / "latest.pt") if (ckpt_dir / "latest.pt").exists() else None,
        device="cpu",
        force_fresh=False,
        max_missing_ratio=0.85,
    )
    params = assert_real_param_count(
        model,
        f"{namespace}:gpt3_760m",
        size_tier=str(cfg.get("size_tier") or "gpt3_760m"),
    )
    arch = model.architecture_config()
    payload = {
        "model_state": model.state_dict(),
        "config": arch,
        "parameters": int(params),
        "size_tier": cfg.get("size_tier"),
        "upgrade_meta": meta,
    }
    torch.save(payload, ckpt_dir / "latest.pt")
    (ckpt_dir / "config.json").write_text(
        json.dumps(
            {
                "size_tier": cfg.get("size_tier"),
                "parameters": int(params),
                "architecture": arch,
                "upgrade": meta,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _log(f"{namespace}: seeded {params:,} real params")
    return {"namespace": namespace, "parameters": int(params), "architecture": arch, "meta": meta}


def main() -> None:
    _log("=== rebuild_gpt3_760m start ===")
    rows = [
        rebuild_text("text_enterprise", "text_enterprise"),
        rebuild_text("text_code", "text_code"),
    ]
    proof = {
        "tier": "gpt3_760m",
        "note": "GPT-3 Medium class (~760M). Full GPT-3 175B is not local-trainable.",
        "models": rows,
        "total_text_params": sum(int(r["parameters"]) for r in rows),
    }
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    _log(f"proof -> {PROOF}")
    _log("=== rebuild_gpt3_760m done ===")


if __name__ == "__main__":
    main()
