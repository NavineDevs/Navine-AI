import json
import sys
from pathlib import Path

import torch

from navine.text.infer import generate
from navine.text.quality import candidate_score, pick_best_candidate
from navine.utils.paths import get_checkpoint_dir, get_project_root

MODELS = [
    "text_enterprise",
    "text_code",
    "hitboyx23_ai",
    "hitboyx23_ai_python",
]
MODES = ["chat", "code", "think", "detective"]
PROMPTS = {
    "chat": "Explain the difference between TCP and UDP in 4 concise sentences.",
    "code": "Write a short Python function that checks if a string is a valid parentheses sequence. Output only code.",
    "think": "Think carefully about this debugging scenario and then answer: why might CI tests fail intermittently but pass locally?",
    "detective": "Decode and explain: what is the plaintext of the Caesar cipher KHOOR ZRUOG with shift 3?",
}
PASS_SCORE = 8.0


def run_round(label: str) -> dict:
    out = {"round": label, "pass_score": PASS_SCORE, "models": {}}
    for model in MODELS:
        ck = str(get_checkpoint_dir(model) / "latest.pt")
        out["models"][model] = {}
        for mode in MODES:
            gen = []
            for seed in (42, 43):
                torch.manual_seed(seed)
                gen.append(
                    generate(
                        PROMPTS[mode],
                        checkpoint=ck,
                        mode=mode,
                        max_new_tokens=160,
                        temperature=None,
                        num_candidates=1,
                    )
                )
            best = pick_best_candidate(gen)
            best_score = candidate_score(best)
            out["models"][model][mode] = {
                "best_score": best_score,
                "passed": best_score >= PASS_SCORE,
                "best": best[:280],
            }
    scores = [
        row["best_score"]
        for model in out["models"].values()
        for row in model.values()
    ]
    out["summary"] = {
        "avg_score": sum(scores) / max(len(scores), 1),
        "min_score": min(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
        "passed_modes": sum(1 for s in scores if s >= PASS_SCORE),
        "total_modes": len(scores),
    }
    return out


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "round"
    report = run_round(label)
    log_dir = get_project_root() / "logs" / "iterative_training"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{label}_smoke.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
