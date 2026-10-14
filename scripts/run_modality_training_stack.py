import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LOG = ROOT / "logs" / "modality_training_stack.log"


def log(line: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    text = f"[{stamp}] {line}"
    print(text, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")


def run_step(name: str, fn) -> None:
    log(f"START {name}")
    try:
        fn()
        log(f"DONE {name}")
    except Exception as exc:
        log(f"FAIL {name}: {exc}")
        log(traceback.format_exc())
        raise


def main() -> int:
    from navine.deepfake.train import train_deepfake
    from navine.image.train import train as train_image
    from navine.text.train import train as train_text
    from navine.utils.tier import modality_config_name
    from navine.video.train import train as train_video
    from navine.voice.train import train_voice

    log("Modality training stack starting")

    run_step(
        "text",
        lambda: train_text(
            config_path=modality_config_name("text"),
            max_steps=4000,
            require_cuda=True,
        ),
    )
    run_step(
        "text-code",
        lambda: train_text(config_path="text_code", max_steps=8000, require_cuda=True),
    )
    run_step("voice", lambda: train_voice(steps=4))
    run_step(
        "image",
        lambda: train_image(
            config_path=modality_config_name("image"),
            finetune=True,
            finetune_steps=800,
            require_cuda=True,
        ),
    )
    run_step(
        "video",
        lambda: train_video(
            config_path=modality_config_name("video"),
            finetune=True,
            finetune_steps=800,
            require_cuda=True,
        ),
    )
    run_step("deepfake", lambda: train_deepfake(steps=4))

    log("Modality training stack complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
