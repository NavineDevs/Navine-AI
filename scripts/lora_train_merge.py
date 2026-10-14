import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from navine.lora.cycle import run_lora_cycle


def main() -> int:
    modality = sys.argv[1] if len(sys.argv) > 1 else "image"
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else None
    result = run_lora_cycle(modality, steps=steps)
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
