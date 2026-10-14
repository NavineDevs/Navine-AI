from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "train_rotate.log"
PY = ROOT / "venv" / "Scripts" / "python.exe"


def _log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def _run(cmd: list[str]) -> int:
    _log("RUN " + " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(ROOT))
    return int(completed.returncode)


def main() -> int:
    if not PY.exists():
        _log("missing venv python")
        return 1

    stages = [
        ([str(PY), str(ROOT / "scripts" / "run_chat_sft.py"), "500"], "chat_sft"),
        ([str(PY), str(ROOT / "scripts" / "run_image_mix_steps.py"), "600"], "image_mix"),
        ([str(PY), "-m", "navine.cli", "train", "video", "--steps", "800"], "video_ft"),
        ([str(PY), str(ROOT / "scripts" / "train_text_code_specialist.py"), "--steps", "1200"], "text_code"),
        ([str(PY), str(ROOT / "scripts" / "export_ai_output_gguf.py")], "gguf_export"),
    ]

    _log("TRAIN_ROTATE_BEGIN")
    for cmd, label in stages:
        _log(f"STAGE_BEGIN {label}")
        code = _run(cmd)
        _log(f"STAGE_END {label} code={code}")
        if code != 0:
            _log(f"STAGE_FAIL {label}")
        time.sleep(5)
    _log("TRAIN_ROTATE_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
