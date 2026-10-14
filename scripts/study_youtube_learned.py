import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data" / "learn" / "pages"


def clean_transcript(text: str) -> str:
    idx = text.find('"wireMagic"')
    if idx > 200:
        text = text[:idx]
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^\d{1,2}:\d{2}", s):
            continue
        if "weeklyhow" in s.lower() or "discord.gg" in s.lower():
            continue
        if len(s) < 4:
            continue
        lines.append(s)
    return "\n".join(lines)


def extract_snippets(text: str, limit: int = 20) -> list[str]:
    pattern = re.compile(
        r".{0,90}\b(transformer|attention|embedding|tokenizer|backprop|loss|learning rate|"
        r"optimizer|adam|rope|rms|swiglu|softmax|layer norm|positional|hidden|fine.?tun|"
        r"lora|ddpm|diffusion|unet|vae|latent|caption|frame|lstm|conv|pytorch|jax|cuda|"
        r"batch|gradient|warmup|from scratch|cross.?entropy|chatbot|video gen|image gen)"
        r".{0,110}",
        re.I,
    )
    seen = set()
    out = []
    for m in pattern.finditer(text):
        sn = re.sub(r"\s+", " ", m.group(0)).strip()
        key = sn.lower()[:80]
        if key in seen or len(sn) < 35:
            continue
        seen.add(key)
        out.append(sn)
        if len(out) >= limit:
            break
    return out


def main() -> None:
    rows = []
    for path in sorted(PAGES.glob("youtube_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        title = doc.get("title", "")
        vid = doc.get("video_id", path.stem.replace("youtube_", ""))
        cleaned = clean_transcript(doc.get("text", ""))
        rows.append(
            {
                "id": vid,
                "title": title,
                "words": len(cleaned.split()),
                "snippets": extract_snippets(cleaned),
            }
        )

    lines = []
    for row in rows:
        lines.append("=" * 72)
        lines.append(f"{row['title']} ({row['id']})")
        lines.append(f"words: {row['words']}")
        lines.append("snippets:")
        for sn in row["snippets"]:
            lines.append(f"  - {sn[:240]}")
        lines.append("")

    out = ROOT / "logs" / "youtube_study_report.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
