"""Search Hugging Face, fetch datasets, and train text-code + chat."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"
LOG = ROOT / "logs" / "hf_fetch_train.log"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = msg.rstrip()
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def run(cmd: list[str]) -> int:
    log("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT))
    log(f"exit {proc.returncode}")
    return int(proc.returncode)


def main() -> int:
    if not PY.exists():
        log(f"Missing venv: {PY}")
        return 1

    code = run([str(PY), "-u", "-m", "navine.cli", "learn", "hf-pack", "--code-max", "600", "--chat-max", "1200"])
    if code != 0:
        return code

    code = run([str(PY), "-u", "-m", "navine.cli", "learn", "ingest"])
    if code != 0:
        log("ingest failed (continuing)")

    code = run([str(PY), "-u", "-m", "navine.cli", "train", "text-code", "--steps", "500", "--require-cuda"])
    if code != 0:
        log("text-code train failed")
        return code

    code = run([str(PY), "-u", "-m", "navine.cli", "train", "chat", "--steps", "300", "--require-cuda"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
