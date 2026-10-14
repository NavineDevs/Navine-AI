# GPT-3 class local roadmap (RTX 4060 8GB)

Full OpenAI GPT-3 is **175B** and is not trainable or loadable on this GPU.

We climb the **real GPT-3 paper size ladder** with unique trainable weights:

| Tier | Target | Status |
|------|--------|--------|
| GPT-3 125M-class | ~100-150M | available (`150m`) |
| GPT-3 350M-class | ~300-350M | prior (`medium`) |
| GPT-3 760M-class | ~650-780M | **current default for all modalities** (`gpt3_760m`) |
| GPT-3 1.3B-class | ~1.1-1.4B | stretch (`gpt3_1p3b`) |
| GPT-3 175B | 175B | not local |

Modalities on `gpt3_760m`: text, text_code, image, video, voice, deepfake.  
Detective / think / OSINT / analyze share `text_enterprise`.

## Commands

```text
python scripts/expand_gpt3_datasets.py
python scripts/rebuild_gpt3_760m.py
python scripts/rebuild_gpt3_760m_modalities.py
python -m navine.cli train text --steps 4000 --require-cuda
```

Proof files:
- `logs/verify_real_gpt3_760m.json` (text)
- `logs/verify_real_gpt3_760m_all.json` (all modalities)

