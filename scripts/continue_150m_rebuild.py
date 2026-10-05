from __future__ import annotations

import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_150m.log"
PY = ROOT / "venv" / "Scripts" / "python.exe"
CKPT = ROOT / "checkpoints"

STAGES = [
    ("text_code", [None], "text_code"),
    ("video", [str(PY), "-m", "navine.cli", "train", "video", "--steps", "1500"], "video"),
    ("voice", [str(PY), "-m", "navine.cli", "train", "voice", "--steps", "800"], "voice"),
]


def _log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def _report(cycle: int, stage: str, running: bool = True, steps: int = 0, total: int = 0) -> None:
    try:
        from navine.api.train_progress_helper import report_train_progress

        report_train_progress(
            stage=stage,
            steps=steps,
            steps_total=total,
            label=f"rebuild 150m · {stage}",
            running=running,
            force=True,
            cycle=cycle,
            max_cycles=5,
            last_line=f"CYCLE {cycle}/5 {stage}",
            percent=min(99.0, 100.0 * max(cycle - (0 if running else 0), 0) / 5.0),
        )
    except Exception as exc:
        _log(f"progress_write_skip {exc}")


def _copy_ckpt(src_name: str, dst_name: str) -> None:
    src = CKPT / src_name
    dst = CKPT / dst_name
    dst.mkdir(parents=True, exist_ok=True)
    for fname in ("latest.pt", "best.pt", "tokenizer.json", "config.json"):
        s = src / fname
        if s.exists():
            shutil.copy2(s, dst / fname)
    _log(f"copied checkpoint {src_name} -> {dst_name}")


def _seed_text_code() -> int:
    src = CKPT / "text_enterprise" / "latest.pt"
    if not src.exists():
        _log("text_code seed missing text_enterprise")
        return 1
    _copy_ckpt("text_enterprise", "text_code")
    _copy_ckpt("text_code", "hitboyx23_ai_python")
    return 0


def main() -> int:
    if not PY.exists():
        _log("missing venv")
        return 1
    sys.path.insert(0, str(ROOT))
    _log("REBUILD_150M_CONTINUE")
    _log("===== CYCLE 3/5 continue =====")

    # text_code failed earlier; seed from text_enterprise 150M
    _report(3, "text_code", True)
    _log("STAGE_BEGIN text_code")
    code = _seed_text_code()
    _log(f"STAGE_END text_code code={code}")
    if code != 0:
        _log("STAGE_FAIL text_code")

    for idx, (label, cmd, _) in enumerate(STAGES[1:], start=4):
        _log(f"===== CYCLE {idx}/5 {label} =====")
        _report(idx, label, True)
        _log(f"STAGE_BEGIN {label}")
        rc = int(subprocess.run(cmd, cwd=str(ROOT)).returncode)
        _log(f"STAGE_END {label} code={rc}")
        if label == "voice" and rc == 0:
            _copy_ckpt("voice", "voice_enterprise")
        if rc != 0:
            _log(f"STAGE_FAIL {label}")
        time.sleep(2)

    _report(5, "complete", False, 1, 1)
    _log("REBUILD_150M_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
