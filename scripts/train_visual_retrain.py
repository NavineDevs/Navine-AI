from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _py() -> str:
    venv = ROOT / "venv" / "Scripts" / "python.exe"
    return str(venv) if venv.exists() else sys.executable


def _log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    path = ROOT / "logs" / "visual_retrain.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    try:
        from navine.api.train_progress_helper import report_train_progress

        stage = "image" if " image " in f" {msg} " else ("video" if " video " in f" {msg} " else "visual")
        report_train_progress(stage=stage, label=msg[:120], running=True, percent=3.0, force=True, last_line=line)
    except Exception:
        pass


def main() -> int:
    image_steps = 6000
    video_steps = 4500
    if len(sys.argv) > 1:
        try:
            image_steps = int(sys.argv[1])
        except ValueError:
            pass
    if len(sys.argv) > 2:
        try:
            video_steps = int(sys.argv[2])
        except ValueError:
            pass

    py = _py()
    _log(f"Visual retrain start image_steps={image_steps} video_steps={video_steps}")

    cmds = [
        [py, "-m", "navine.cli", "train", "image", "--steps", str(image_steps), "--require-cuda"],
        [py, "-m", "navine.cli", "train", "video", "--steps", str(video_steps), "--require-cuda"],
    ]
    ok = True
    for cmd in cmds:
        _log("RUN " + " ".join(cmd))
        code = subprocess.call(cmd, cwd=str(ROOT))
        _log(f"DONE returncode={code} cmd={' '.join(cmd[-4:])}")
        if code != 0:
            ok = False
            break

    try:
        from navine.api.train_progress_helper import report_train_progress

        report_train_progress(
            stage="idle",
            running=False,
            percent=100.0,
            label="visual retrain complete" if ok else "visual retrain failed",
            force=True,
        )
    except Exception:
        pass
    _log("Visual retrain finished ok=" + str(ok))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
