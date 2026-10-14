import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from navine.lora.cycle import run_lora_cycle
from navine.utils.config import load_config
from navine.utils.tier import resolve_checkpoint_dir


def _base_ready(config_name: str) -> bool:
    cfg = load_config(config_name)
    ckpt = resolve_checkpoint_dir("image" if "image" in config_name else "video", cfg) / "latest.pt"
    return ckpt.exists() and ckpt.stat().st_size > 1024 * 1024


def main() -> None:
    print("Navine AI: waiting for base image checkpoint before LoRA cycle...")
    while not _base_ready("image_enterprise_v2"):
        time.sleep(60)
    print("Navine AI: image base ready. Running LoRA train-merge cycle.")
    result = run_lora_cycle("image")
    print(f"Image LoRA cycle: {result}")
    print("Navine AI: waiting for base video checkpoint before LoRA cycle...")
    while not _base_ready("video_enterprise"):
        time.sleep(60)
    print("Navine AI: video base ready. Running LoRA train-merge cycle.")
    result = run_lora_cycle("video")
    print(f"Video LoRA cycle: {result}")


if __name__ == "__main__":
    main()
