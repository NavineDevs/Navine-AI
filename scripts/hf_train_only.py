"""Ingest HF-fetched data and train text-code + chat (skip re-download)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"
LOG = ROOT / "logs" / "hf_train_only.log"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(msg.rstrip() + "\n")
    print(msg, flush=True)


def run(args: list[str]) -> int:
    log("$ " + " ".join(args))
    proc = subprocess.run(args, cwd=str(ROOT))
    log(f"exit {proc.returncode}")
    return int(proc.returncode)


def main() -> int:
    if not PY.exists():
        log(f"Missing venv: {PY}")
        return 1
    base = [str(PY), "-u", "-m", "navine.cli"]
    run(base + ["learn", "ingest"])
    code = run(base + ["train", "text-code", "--steps", "500", "--require-cuda"])
    if code != 0:
        return code
    return run(base + ["train", "chat", "--steps", "300", "--require-cuda"])


if __name__ == "__main__":
    raise SystemExit(main())
