import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data" / "learn" / "pages"


def parse_yt_json_captions(text: str) -> str:
    idx = text.find('"wireMagic"')
    if idx < 0:
        return ""
    blob = text[idx:]
    parts = re.findall(r'"utf8":\s*"((?:\\.|[^"])*)"', blob)
    out: list[str] = []
    for part in parts:
        try:
            decoded = bytes(part, "utf-8").decode("unicode_escape")
        except Exception:
            decoded = part
        decoded = decoded.replace("\n", " ").strip()
        if decoded and decoded not in out[-3:]:
            out.append(decoded)
    return " ".join(out)


def main() -> None:
    lines: list[str] = []
    for path in sorted(PAGES.glob("youtube_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        text = doc.get("text", "")
        spoken = parse_yt_json_captions(text)
        lines.append("=" * 72)
        lines.append(f"{doc.get('title')} ({doc.get('video_id')})")
        lines.append(f"spoken_words={len(spoken.split())}")
        lines.append(spoken[:2500])
        lines.append("")
    out = ROOT / "logs" / "youtube_spoken_content.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
