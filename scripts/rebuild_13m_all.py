from __future__ import annotations

import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "rebuild_13m.log"
PY = ROOT / "venv" / "Scripts" / "python.exe"
CKPT = ROOT / "checkpoints"


def _log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def _run(cmd: list[str]) -> int:
    _log("RUN " + " ".join(cmd))
    return int(subprocess.run(cmd, cwd=str(ROOT)).returncode)


def _archive(name: str) -> None:
    src = CKPT / name
    if not src.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = CKPT / f"_archive_pre13m_{name}_{stamp}"
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    for fname in ("latest.pt", "best.pt"):
        p = src / fname
        if p.exists():
            p.unlink()
    _log(f"archived {name} -> {dst.name}")


def _copy_ckpt(src_name: str, dst_name: str) -> None:
    src = CKPT / src_name
    dst = CKPT / dst_name
    dst.mkdir(parents=True, exist_ok=True)
    for fname in ("latest.pt", "best.pt", "tokenizer.json"):
        s = src / fname
        if s.exists():
            shutil.copy2(s, dst / fname)
    _log(f"copied checkpoint {src_name} -> {dst_name}")


def _param_report() -> None:
    sys.path.insert(0, str(ROOT))
    from navine.text.model import build_text_model
    from navine.image.model import NavineDiffusionModel
    from navine.video.model import NavineVideoModel
    from navine.utils.config import load_config
    from navine.utils.paths import get_checkpoint_dir
    import torch

    text_cfg = load_config("text_enterprise")
    m = dict(text_cfg.get("model") or {})
    tp = build_text_model(m, int(m.get("vocab_size", 12000))).count_parameters()
    img = NavineDiffusionModel(**load_config("image_enterprise_v2")["model"]).count_parameters()
    vid = NavineVideoModel(**load_config("video_enterprise")["model"]).count_parameters()
    _log(f"TARGET text={tp:,} image={img:,} video={vid:,} total={tp+img+vid:,}")
    for name in ("text_enterprise", "text_code", "image_enterprise_v2", "video_enterprise"):
        pt = get_checkpoint_dir(name) / "latest.pt"
        if not pt.exists():
            _log(f"MISSING {name}")
            continue
        payload = torch.load(str(pt), map_location="cpu", weights_only=False)
        state = payload.get("model_state") or payload
        n = sum(int(t.numel()) for t in state.values() if hasattr(t, "numel"))
        _log(f"CKPT {name} params={n:,} bytes={pt.stat().st_size:,}")


def main() -> int:
    if not PY.exists():
        _log("missing venv")
        return 1

    _log("REBUILD_13M_BEGIN")
    _param_report()

    for name in (
        "text_enterprise",
        "text_code",
        "hitboyx23_ai",
        "hitboyx23_ai_python",
        "image_enterprise_v2",
        "video_enterprise",
    ):
        _archive(name)

    stages = [
        ([str(PY), "-m", "navine.cli", "train", "text", "--steps", "4000"], "text_enterprise"),
        ([str(PY), str(ROOT / "scripts" / "train_text_code_specialist.py"), "--steps", "2500"], "text_code"),
        ([str(PY), str(ROOT / "scripts" / "run_image_mix_steps.py"), "800"], "image_v2"),
        ([str(PY), "-m", "navine.cli", "train", "video", "--steps", "1200"], "video"),
        ([str(PY), str(ROOT / "scripts" / "export_ai_output_gguf.py")], "gguf_export"),
    ]

    for cmd, label in stages:
        _log(f"STAGE_BEGIN {label}")
        code = _run(cmd)
        _log(f"STAGE_END {label} code={code}")
        if label == "text_enterprise" and code == 0:
            _copy_ckpt("text_enterprise", "hitboyx23_ai")
        if label == "text_code" and code == 0:
            _copy_ckpt("text_code", "hitboyx23_ai_python")
        if code != 0:
            _log(f"STAGE_FAIL {label}")
        time.sleep(3)

    try:
        from navine.text.infer import clear_model_cache

        clear_model_cache()
    except Exception:
        pass

    _param_report()
    _log("REBUILD_13M_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
