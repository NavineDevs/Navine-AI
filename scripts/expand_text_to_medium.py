from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

from navine.text.arch import (
    apply_size_tier,
    archive_text_checkpoint,
    architectures_match,
    build_or_upgrade_text_model,
)
from navine.text.tokenizer import NavineTokenizer
from navine.utils.config import load_config
from navine.utils.paths import get_checkpoint_dir


TEXT_TARGETS: List[Tuple[str, str]] = [
    ("text_enterprise", "text_enterprise"),
    ("text_code", "text_enterprise"),
    ("hitboyx23_ai", "hitboyx23_ai"),
    ("hitboyx23_ai_python", "hitboyx23_ai_python"),
]


def _write_config_json(ckpt_dir: Path, arch: dict, params: int, size_tier: str, meta: dict) -> None:
    payload = {
        "size_tier": size_tier,
        "parameters": params,
        "architecture": arch,
        "upgrade": {
            "transferred": meta.get("transferred"),
            "skipped": meta.get("skipped"),
            "fresh": meta.get("fresh"),
            "upgraded": meta.get("upgraded"),
            "note": meta.get("note"),
        },
    }
    (ckpt_dir / "config.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def expand_one(namespace: str, config_name: str) -> dict:
    config = apply_size_tier(load_config(config_name))
    ckpt_dir = get_checkpoint_dir(namespace)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    latest = ckpt_dir / "latest.pt"
    tok_path = ckpt_dir / "tokenizer.json"
    if not tok_path.exists():
        raise FileNotFoundError(f"Missing tokenizer for {namespace}: {tok_path}")

    source = latest if latest.exists() else None
    if source is not None:
        import torch

        payload = torch.load(str(source), map_location="cpu", weights_only=False)
        saved = dict((payload or {}).get("config") or {})
        if architectures_match(saved, config.get("model") or {}):
            model_probe = None
            from navine.text.model import NavineTextModel

            model_probe, _ = NavineTextModel.load_checkpoint(source, "cpu")
            params = model_probe.count_parameters()
            arch = model_probe.architecture_config()
            _write_config_json(ckpt_dir, arch, params, str(config.get("size_tier", "medium")), {"note": "already medium"})
            print(f"{namespace}: already medium ({params:,} params)")
            return {"namespace": namespace, "params": params, "status": "already_medium"}

        archive = archive_text_checkpoint(ckpt_dir, label="archive_small_58m")
        if archive and (archive / "latest.pt").exists():
            source = archive / "latest.pt"
            print(f"{namespace}: archived small checkpoint -> {archive}")

    tokenizer = NavineTokenizer.load(tok_path)
    model, meta = build_or_upgrade_text_model(
        config,
        vocab_size=len(tokenizer.token_to_id),
        checkpoint_path=source,
        device="cpu",
        force_fresh=False,
    )
    params = model.count_parameters()
    arch = model.architecture_config()
    model.save_checkpoint(
        latest,
        extra={
            "size_tier": config.get("size_tier", "medium"),
            "upgrade": meta,
        },
    )
    _write_config_json(ckpt_dir, arch, params, str(config.get("size_tier", "medium")), meta)
    print(
        f"{namespace}: expanded to {params:,} params "
        f"(transferred={meta.get('transferred')} skipped={meta.get('skipped')} "
        f"fresh={meta.get('fresh')}) -> {latest}"
    )
    return {"namespace": namespace, "params": params, "status": "expanded", "meta": meta}


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand local text checkpoints to medium architecture")
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Optional subset of namespaces",
    )
    parser.add_argument("--train-steps", type=int, default=0, help="Optional post-expand instruct SFT steps")
    args = parser.parse_args()

    selected = set(args.models) if args.models else None
    results = []
    for namespace, config_name in TEXT_TARGETS:
        if selected is not None and namespace not in selected:
            continue
        results.append(expand_one(namespace, config_name))

    if args.train_steps > 0:
        import sys

        root = Path(__file__).resolve().parents[1]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        if str(root / "scripts") not in sys.path:
            sys.path.insert(0, str(root / "scripts"))
        from finetune_instruct_clean import run as finetune_run

        models = [r["namespace"] for r in results]
        print(f"Post-expand instruct SFT steps={args.train_steps} models={models}")
        finetune_run(steps=args.train_steps, models=models)

    report = get_checkpoint_dir("text_enterprise").parent / ".." / "logs" / "medium_expand_report.json"
    report = Path(report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
