from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from navine.text.data_pipeline import load_clean_instruct_blocks
from navine.train.base import finetune_texts
from navine.train.data_loaders import read_jsonl
from navine.utils.paths import get_checkpoint_dir, get_project_root


TEXT_MODELS = (
    ("text_enterprise", "general"),
    ("text_code", "coding"),
    ("hitboyx23_ai", "hitboyx23"),
    ("hitboyx23_ai_python", "hitboyx23_python"),
)


def _coding_examples(limit: int = 80) -> List[str]:
    root = get_project_root()
    path = root / "data" / "train" / "coding" / "python.jsonl"
    if not path.exists():
        return []
    blocks: List[str] = []
    for entry in read_jsonl(path)[:limit]:
        prompt = str(entry.get("prompt") or "").strip()
        code = str(entry.get("code") or "").strip()
        if not prompt or not code:
            continue
        blocks.append(
            "### System: You are Navine AI. Provide clean runnable Python code in a markdown block.\n"
            f"### User: {prompt}\n"
            f"### Assistant: Here is the Python code:\n\n```python\n{code}\n```"
        )
    return blocks


def _load_extra_dialogue(rel: str) -> List[str]:
    path = get_project_root() / rel
    if not path.is_file():
        return []
    chunks = [b.strip() for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    return [c for c in chunks if "### Assistant:" in c]


def load_instruct_corpus() -> List[str]:
    blocks = load_clean_instruct_blocks()
    blocks.extend(_coding_examples(120))
    blocks.extend(_load_extra_dialogue("data/train/unrestricted/instructions.txt"))
    blocks.extend(_load_extra_dialogue("data/train/unrestricted/controversial_dialogue.txt"))
    blocks.extend(_load_extra_dialogue("data/train/nsfw/instructions.txt"))
    blocks.extend(_load_extra_dialogue("data/train/nsfw/clean_adult_dialogue.txt"))
    return blocks


def run(steps: int = 500, models: List[str] | None = None) -> None:
    texts = load_instruct_corpus()
    if not texts:
        raise SystemExit("No clean instruct blocks found.")
    print(f"Clean instruct blocks: {len(texts)}")
    selected = models or [name for name, _ in TEXT_MODELS]
    for ckpt_name, config_name in TEXT_MODELS:
        if ckpt_name not in selected:
            continue
        ckpt_dir = get_checkpoint_dir(ckpt_name)
        latest = ckpt_dir / "latest.pt"
        if not latest.exists():
            print(f"Skip {ckpt_name}: missing {latest}")
            continue
        print(f"Instruct finetune {ckpt_name} -> {ckpt_dir} steps={steps}")
        finetune_texts(
            config_name,
            texts,
            desc=f"Instruct SFT {ckpt_name}",
            max_steps=steps,
            checkpoint_dir=ckpt_dir,
            require_cuda=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Optional subset: text_enterprise text_code hitboyx23_ai hitboyx23_ai_python",
    )
    args = parser.parse_args()
    run(steps=args.steps, models=args.models)


if __name__ == "__main__":
    main()
