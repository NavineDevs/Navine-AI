import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
LOG = ROOT / "logs" / "real_ai_upgrade.log"


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def run(label: str, cmd: list[str]) -> int:
    log(f"START {label}")
    start = time.time()
    with LOG.open("a", encoding="utf-8") as handle:
        code = subprocess.call(cmd, cwd=str(ROOT), stdout=handle, stderr=handle)
    elapsed = int(time.time() - start)
    log(f"EXIT {label} code={code} elapsed={elapsed}s")
    return int(code)


def main() -> int:
    if not PYTHON.exists():
        log("ERROR missing venv python")
        return 1

    sys.path.insert(0, str(ROOT))
    from navine.text.model import NavineTextModel

    gpt2_params = NavineTextModel(
        vocab_size=12000,
        d_model=768,
        n_heads=12,
        n_layers=16,
        d_ff=3072,
        max_seq_len=1024,
        dropout=0.08,
        use_rope=True,
        use_kv_cache=True,
        use_swiglu=True,
        use_rms_norm=True,
        tie_embeddings=True,
    ).count_parameters()
    log(f"REAL_AI_UPGRADE_BEGIN target_text_params={gpt2_params:,} (GPT-2 small class)")

    stages = [
        ("prepare_data", [str(PYTHON), str(ROOT / "scripts" / "prepare_data.py")]),
        ("learn_everything", [str(PYTHON), "-u", "-m", "navine.cli", "learn", "everything"]),
        (
            "text_gpt2",
            [
                str(PYTHON),
                "-u",
                "-m",
                "navine.cli",
                "train",
                "text",
                "--config",
                "text_enterprise",
                "--require-cuda",
            ],
        ),
        (
            "code_gpt2",
            [
                str(PYTHON),
                "-u",
                "-m",
                "navine.cli",
                "train",
                "text",
                "--config",
                "text_code",
                "--require-cuda",
            ],
        ),
        (
            "image_mix",
            [
                str(PYTHON),
                str(ROOT / "scripts" / "run_image_mix_steps.py"),
                "6000",
            ],
        ),
        (
            "video",
            [
                str(PYTHON),
                "-u",
                "-m",
                "navine.cli",
                "train",
                "video",
                "--require-cuda",
                "--steps",
                "1200",
            ],
        ),
        (
            "image_lora_cycle",
            [str(PYTHON), "-u", "-m", "navine.cli", "lora", "cycle", "image"],
        ),
    ]

    for label, cmd in stages:
        code = run(label, cmd)
        if code != 0:
            log(f"WARNING {label} failed with code={code}; continuing")

    log("Starting quality loop until eval targets pass")
    code = run(
        "quality_loop",
        [str(PYTHON), str(ROOT / "scripts" / "run_custom_only_train.py")],
    )
    log(f"REAL_AI_UPGRADE_DONE code={code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
