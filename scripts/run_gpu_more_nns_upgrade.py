"""GPU-first enterprise upgrade: archive, fresh text, SFT, image/video, text_code.

Use project venv with CUDA:
  .\\venv\\Scripts\\python.exe scripts\\run_gpu_more_nns_upgrade.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / "venv" / "Scripts" / "python.exe"
LOGS = ROOT / "logs"


def _py() -> str:
    if VENV_PY.exists():
        return str(VENV_PY)
    return sys.executable


def _log_run(name: str, cmd: list[str]) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{name}.log"
    print(f"=== {name} ===", flush=True)
    print(" ".join(cmd), flush=True)
    print(f"log -> {log_path}", flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        log.write(" ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        code = proc.wait()
        log.write(f"\nexit={code}\n")
        print(f"exit={code}", flush=True)
        return int(code)


def archive_text_enterprise() -> Path:
    from navine.utils.paths import get_checkpoint_dir

    src = get_checkpoint_dir("text_enterprise")
    dest = src / "archive_34m_8x512"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("latest.pt", "best.pt", "tokenizer.json"):
        path = src / name
        if path.exists() and path.is_file():
            target = dest / name
            if not target.exists():
                shutil.copy2(path, target)
                print(f"Archived {name} -> {target}")
            else:
                print(f"Archive already has {name}")
    marker = dest / "README.txt"
    if not marker.exists():
        marker.write_text(
            "Archived pre-rebuild text_enterprise (8x512 ~34M GELU/LN word tokenizer).\n"
            "Live folder rebuild targets 10x640 SwiGLU/RMSNorm BPE.\n",
            encoding="utf-8",
        )
    return dest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-data", action="store_true")
    parser.add_argument("--skip-text", action="store_true")
    parser.add_argument("--skip-sft", action="store_true")
    parser.add_argument("--skip-image-video", action="store_true")
    parser.add_argument("--skip-text-code", action="store_true")
    parser.add_argument("--text-steps", type=int, default=4000)
    parser.add_argument("--sft-steps", type=int, default=500)
    parser.add_argument("--image-steps", type=int, default=600)
    parser.add_argument("--video-steps", type=int, default=450)
    parser.add_argument("--code-steps", type=int, default=600)
    parser.add_argument("--hf-max", type=int, default=2500)
    parser.add_argument("--require-cuda", action="store_true", default=True)
    args = parser.parse_args()
    py = _py()
    sys.path.insert(0, str(ROOT))

    from navine.device_manager import print_train_device_banner

    print_train_device_banner(require_cuda=bool(args.require_cuda))
    archive_text_enterprise()

    if not args.skip_data:
        if _log_run(
            "gpu_upgrade_hf_code",
            [py, "-m", "navine.cli", "learn", "hf-code", "--max", str(args.hf_max)],
        ):
            print("hf-code had errors (continuing if partial data exists)")

    if not args.skip_text:
        code = _log_run(
            "gpu_upgrade_text_enterprise_fresh",
            [
                py,
                "-m",
                "navine.cli",
                "train",
                "text",
                "--fresh",
                "--steps",
                str(args.text_steps),
                "--require-cuda",
                "--config",
                "text_enterprise",
            ],
        )
        if code != 0:
            return code

    if not args.skip_sft:
        for domain in (
            "chat",
            "coding",
            "games",
            "general",
            "math",
            "creative",
            "multimodal-text",
        ):
            code = _log_run(
                f"gpu_upgrade_sft_{domain.replace('-', '_')}",
                [
                    py,
                    "-m",
                    "navine.cli",
                    "train",
                    domain,
                    "--steps",
                    str(args.sft_steps),
                    "--require-cuda",
                ],
            )
            if code != 0:
                print(f"SFT {domain} failed code={code}, continuing")

    if not args.skip_image_video:
        _log_run(
            "gpu_upgrade_image_enterprise",
            [
                py,
                "-m",
                "navine.cli",
                "train",
                "image",
                "--steps",
                str(args.image_steps),
                "--require-cuda",
            ],
        )
        _log_run(
            "gpu_upgrade_video_enterprise",
            [
                py,
                "-m",
                "navine.cli",
                "train",
                "video",
                "--steps",
                str(args.video_steps),
                "--require-cuda",
            ],
        )

    if not args.skip_text_code:
        _log_run(
            "gpu_upgrade_text_code",
            [
                py,
                "-m",
                "navine.cli",
                "train",
                "text-code",
                "--steps",
                str(args.code_steps),
                "--require-cuda",
            ],
        )

    print("GPU more-NNs upgrade pipeline finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
