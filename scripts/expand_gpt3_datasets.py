from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "train" / "gpt3_scale"
CHAT_DIR = ROOT / "data" / "train" / "chat"
GENERAL_DIR = ROOT / "data" / "train" / "general"


TOPICS = [
    "science",
    "history",
    "math",
    "coding",
    "everyday life",
    "geography",
    "health basics",
    "technology",
    "language",
    "logic puzzles",
]

SKILLS = [
    "explain clearly",
    "give a short definition",
    "compare two ideas",
    "list practical steps",
    "answer with one example",
    "summarize in two sentences",
    "correct a common mistake",
]


def _blocks(pairs: Iterable[tuple]) -> List[str]:
    out: List[str] = []
    for user, assistant in pairs:
        out.append(
            "### System: You are Navine AI, a capable local assistant.\n"
            f"### User: {user.strip()}\n"
            f"### Assistant: {assistant.strip()}\n"
        )
    return out


def _synthetic_pairs(n: int, seed: int = 23) -> List[tuple]:
    rng = random.Random(seed)
    pairs = []
    for i in range(n):
        topic = rng.choice(TOPICS)
        skill = rng.choice(SKILLS)
        user = f"{skill.capitalize()} about {topic}. Item {i + 1}."
        assistant = (
            f"Here is a direct answer about {topic}. "
            f"I will {skill} without filler. "
            f"Key point {i + 1}: focus on useful facts, keep the reply short, "
            f"and stay consistent with local Navine AI behavior."
        )
        pairs.append((user, assistant))
    return pairs


def _write_lines(path: Path, lines: List[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return len(lines)


def expand(n_instruct: int = 8000, n_pretrain: int = 4000) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    GENERAL_DIR.mkdir(parents=True, exist_ok=True)

    instruct = _blocks(_synthetic_pairs(n_instruct, seed=23))
    more = _blocks(_synthetic_pairs(n_instruct // 2, seed=47))
    instruct_path = OUT_DIR / "instruct_gpt3.txt"
    chat_path = CHAT_DIR / "gpt3_instruct_extra.txt"
    n1 = _write_lines(instruct_path, instruct)
    n2 = _write_lines(chat_path, more)

    pretrain_lines = []
    for i, (user, assistant) in enumerate(_synthetic_pairs(n_pretrain, seed=91)):
        pretrain_lines.append(
            f"Document {i + 1}. {assistant} Related question: {user} "
            f"This paragraph is training text for a GPT-3 class local model."
        )
    pretrain_path = GENERAL_DIR / "gpt3_pretrain_corpus.txt"
    n3 = _write_lines(pretrain_path, pretrain_lines)

    # merge into learned corpus pointer file used by enterprise config
    learned = ROOT / "data" / "text" / "learned_corpus.txt"
    learned.parent.mkdir(parents=True, exist_ok=True)
    blob = "\n\n".join(
        [
            instruct_path.read_text(encoding="utf-8"),
            pretrain_path.read_text(encoding="utf-8"),
        ]
    )
    if learned.exists():
        existing = learned.read_text(encoding="utf-8", errors="replace")
        if "Document 1." not in existing:
            blob = existing.rstrip() + "\n\n" + blob
        else:
            blob = existing
    learned.write_text(blob, encoding="utf-8")

    report = {
        "instruct_blocks": n1,
        "chat_extra_blocks": n2,
        "pretrain_docs": n3,
        "paths": [str(instruct_path), str(chat_path), str(pretrain_path), str(learned)],
    }
    (OUT_DIR / "expand_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand GPT-3 scale local training datasets")
    parser.add_argument("--instruct", type=int, default=8000)
    parser.add_argument("--pretrain", type=int, default=4000)
    args = parser.parse_args()
    expand(n_instruct=args.instruct, n_pretrain=args.pretrain)


if __name__ == "__main__":
    main()
