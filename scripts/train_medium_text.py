from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from navine.text.arch import apply_size_tier
from navine.text.model import build_text_model
from navine.text.tokenizer import NavineTokenizer
from navine.utils.config import load_config
from navine.utils.paths import get_checkpoint_dir, get_project_root
from navine.utils.tier import modality_config_name


def _write_config_json(ckpt_dir: Path, arch: dict, params: int, size_tier: str) -> None:
    payload = {
        "size_tier": size_tier,
        "parameters": params,
        "architecture": arch,
    }
    (ckpt_dir / "config.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def init_medium_checkpoint(config_name: str, namespace: str) -> Path:
    config = apply_size_tier(load_config(config_name))
    ckpt_dir = get_checkpoint_dir(namespace)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    tok_path = ckpt_dir / "tokenizer.json"
    use_bpe = bool((config.get("tokenizer") or {}).get("use_bpe", True))
    if tok_path.exists():
        tokenizer = NavineTokenizer.load(tok_path)
    else:
        root = get_project_root()
        corpus = []
        for rel in (
            "data/text/instruction_chat.txt",
            "data/train/chat",
            "data/train/general",
        ):
            path = root / rel
            if path.is_file():
                corpus.extend([b.strip() for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()][:2000])
            elif path.is_dir():
                for fp in sorted(path.glob("*.txt"))[:20]:
                    corpus.extend([ln.strip() for ln in fp.read_text(encoding="utf-8").splitlines() if ln.strip()][:200])
        if not corpus:
            corpus = ["### User: hello\n### Assistant: Hello. I am Navine AI."]
        tokenizer = NavineTokenizer(config["model"]["vocab_size"], use_bpe=use_bpe)
        tokenizer.build(corpus[:8000], use_bpe=use_bpe)
        tokenizer.save(tok_path)
    vocab = len(tokenizer.token_to_id)
    model = build_text_model(config, vocab)
    arch = model.architecture_config()
    params = model.count_parameters()
    out = ckpt_dir / "latest.pt"
    model.save_checkpoint(out, extra={"size_tier": config.get("size_tier", "medium"), "init": True})
    _write_config_json(ckpt_dir, arch, params, str(config.get("size_tier", "medium")))
    print(f"Initialized {namespace}: params={params:,} tier={config.get('size_tier')} -> {out}")
    return out


def seed_sibling_from_enterprise(dest_ns: str) -> None:
    src = get_checkpoint_dir("text_enterprise")
    dst = get_checkpoint_dir(dest_ns)
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("latest.pt", "best.pt", "tokenizer.json", "config.json"):
        sp = src / name
        if sp.exists():
            shutil.copy2(sp, dst / name)
            print(f"Seeded {dest_ns}/{name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train or init Navine medium text model")
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--smoke-generate", action="store_true")
    parser.add_argument("--seed-siblings", action="store_true")
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args()

    cfg_name = args.config or modality_config_name("text")
    if args.init_only:
        init_medium_checkpoint(cfg_name, "text_enterprise")
        if args.seed_siblings:
            for ns in ("text_code", "hitboyx23_ai", "hitboyx23_ai_python"):
                seed_sibling_from_enterprise(ns)
        if args.smoke_generate:
            from navine.text.infer import generate

            text = generate("### User: hello\n### Assistant:", max_new_tokens=32, checkpoint=str(get_checkpoint_dir("text_enterprise") / "latest.pt"))
            print(f"Smoke generate: {text[:400]}")
        return

    from navine.text.train import train

    train(
        config_path=cfg_name,
        max_steps=args.steps,
        fresh=bool(args.fresh),
        require_cuda=bool(args.require_cuda),
    )
    if args.seed_siblings:
        for ns in ("text_code", "hitboyx23_ai", "hitboyx23_ai_python"):
            seed_sibling_from_enterprise(ns)
    if args.smoke_generate:
        from navine.text.infer import generate, clear_model_cache

        clear_model_cache()
        text = generate("### User: hello\n### Assistant:", max_new_tokens=48, checkpoint=str(get_checkpoint_dir("text_enterprise") / "latest.pt"))
        print(f"Smoke generate: {text[:500]}")


if __name__ == "__main__":
    main()
