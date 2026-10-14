"""Sequential 760M training: text-code -> text -> image -> video."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"
LOG_DIR = ROOT / "logs" / "gpt3_train"
LOG_DIR.mkdir(parents=True, exist_ok=True)
QUEUE = LOG_DIR / "queue.log"

JOBS = [
    ("text_code", ["train", "text-code", "--steps", "1200", "--require-cuda"]),
    ("text_enterprise", ["train", "text", "--steps", "1200", "--require-cuda"]),
    ("image", ["train", "image", "--steps", "800", "--require-cuda"]),
    ("video", ["train", "video", "--steps", "600", "--require-cuda"]),
]


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    with QUEUE.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def run_job(name: str, args: list[str], skip_if_running: bool = False) -> int:
    out = LOG_DIR / f"{name}.out.log"
    err = LOG_DIR / f"{name}.err.log"
    cmd = [str(PY), "-u", "-m", "navine.cli", *args]
    log(f"START {name} {' '.join(args)}")
    with out.open("ab") as out_f, err.open("ab") as err_f:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=out_f,
            stderr=err_f,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"},
        )
        code = proc.wait()
    log(f"END {name} code={code}")
    return int(code)


def main() -> int:
    start_from = ""
    if len(sys.argv) > 1:
        start_from = sys.argv[1].strip().lower()
    log(f"QUEUE BEGIN start_from={start_from or 'text_code'}")
    started = not start_from
    for name, args in JOBS:
        if not started:
            if name.lower() == start_from or start_from in name.lower():
                started = True
            else:
                log(f"SKIP {name}")
                continue
        code = run_job(name, args)
        if code != 0:
            log(f"STOP after failure in {name}")
            return code
    log("QUEUE DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
