import argparse
import json
from pathlib import Path

import torch
from torchvision.utils import save_image

from navine.image.model import NavineDiffusionModel
from navine.utils.config import load_config
from navine.utils.paths import get_project_root
from navine.utils.tier import resolve_checkpoint_dir


PROMPTS = {
    "blue_sky": "clear blue sky with soft white clouds, wide open atmosphere, natural daylight",
    "photoreal": "photorealistic adult woman portrait, natural skin texture, natural lighting, sharp focus",
    "hentai_nude": "nude hentai anime girl, detailed face and body, clean lineart, vibrant colors",
    "porn_explicit": "photorealistic explicit adult woman nude, detailed boobs ass pussy, natural light",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="image_enterprise_v2_mix")
    parser.add_argument("--tag", default="mix")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=0)
    parser.add_argument("--guidance", type=float, default=0.0)
    parser.add_argument("--scheduler", default="")
    args = parser.parse_args()

    root = get_project_root()
    config = load_config(args.config)
    infer = config.get("inference") or {}
    ckpt_dir = resolve_checkpoint_dir("image", config)
    ckpt = ckpt_dir / "latest.pt"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = NavineDiffusionModel.load_checkpoint(ckpt, config, device).to(device)
    model.eval()

    steps = int(args.steps or infer.get("num_steps") or config.get("diffusion", {}).get("timesteps", 200))
    guidance = float(args.guidance or infer.get("guidance_scale") or 1.5)
    scheduler = str(args.scheduler or infer.get("scheduler") or "ddpm").lower()
    out_dir = root / "outputs" / "image" / f"{args.tag}_pure"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "checkpoint": str(ckpt),
        "config": args.config,
        "tag": args.tag,
        "seed": args.seed,
        "steps": steps,
        "guidance": guidance,
        "scheduler": scheduler,
        "params": model.count_parameters(),
        "outputs": {},
    }

    for name, prompt in PROMPTS.items():
        torch.manual_seed(args.seed)
        if device.type == "cuda":
            torch.cuda.manual_seed_all(args.seed)
        with torch.no_grad():
            sample = model.sample(
                batch_size=1,
                text=prompt,
                device=device,
                num_steps=steps,
                guidance_scale=guidance,
                scheduler=scheduler,
            )
        path = out_dir / f"{name}_seed{args.seed}.png"
        save_image((sample + 1) / 2, path)
        report["outputs"][name] = str(path)
        print(f"{name}: {path}")

    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
