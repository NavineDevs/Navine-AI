from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_TXT = ROOT / "data" / "train" / "coding" / "real_code_sft.txt"
OUT_JSONL = ROOT / "data" / "train" / "coding" / "real_code_sft.jsonl"


EXAMPLES = [
    (
        "python",
        "Write a Python function that binary-searches a sorted list and returns the index or -1.",
        "def binary_search(arr, target):\n"
        "    lo, hi = 0, len(arr) - 1\n"
        "    while lo <= hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        if arr[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid - 1\n"
        "    return -1\n",
    ),
    (
        "python",
        "Write a Flask hello world app on port 5000.",
        "from flask import Flask\n"
        "\n"
        "app = Flask(__name__)\n"
        "\n"
        "@app.get('/')\n"
        "def home():\n"
        "    return 'Hello World'\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    app.run(host='0.0.0.0', port=5000)\n",
    ),
    (
        "javascript",
        "Write a JavaScript function that debounce-calls fn after wait ms.",
        "function debounce(fn, wait) {\n"
        "  let timer = null;\n"
        "  return function (...args) {\n"
        "    clearTimeout(timer);\n"
        "    timer = setTimeout(() => fn.apply(this, args), wait);\n"
        "  };\n"
        "}\n",
    ),
    (
        "python",
        "Write a Python class LRUCache with get and put methods.",
        "from collections import OrderedDict\n"
        "\n"
        "class LRUCache:\n"
        "    def __init__(self, capacity: int):\n"
        "        self.capacity = capacity\n"
        "        self.data = OrderedDict()\n"
        "\n"
        "    def get(self, key: int) -> int:\n"
        "        if key not in self.data:\n"
        "            return -1\n"
        "        self.data.move_to_end(key)\n"
        "        return self.data[key]\n"
        "\n"
        "    def put(self, key: int, value: int) -> None:\n"
        "        if key in self.data:\n"
        "            self.data.move_to_end(key)\n"
        "        self.data[key] = value\n"
        "        if len(self.data) > self.capacity:\n"
        "            self.data.popitem(last=False)\n",
    ),
    (
        "python",
        "Write a tkinter window that shows Hello from Navine AI.",
        "import tkinter as tk\n"
        "\n"
        "def main():\n"
        "    root = tk.Tk()\n"
        "    root.title('Navine AI')\n"
        "    root.geometry('360x160')\n"
        "    tk.Label(root, text='Hello from Navine AI', font=('Segoe UI', 14)).pack(expand=True)\n"
        "    root.mainloop()\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
    ),
    (
        "sql",
        "Write SQL to select the top 5 customers by total order amount.",
        "SELECT c.customer_id, c.name, SUM(o.amount) AS total_amount\n"
        "FROM customers c\n"
        "JOIN orders o ON o.customer_id = c.customer_id\n"
        "GROUP BY c.customer_id, c.name\n"
        "ORDER BY total_amount DESC\n"
        "LIMIT 5;\n",
    ),
    (
        "rust",
        "Write a Rust function that reverses a string.",
        "fn reverse_string(input: &str) -> String {\n"
        "    input.chars().rev().collect()\n"
        "}\n",
    ),
    (
        "go",
        "Write a Go HTTP handler that returns JSON status ok.",
        "package main\n"
        "\n"
        "import (\n"
        "    \"encoding/json\"\n"
        "    \"net/http\"\n"
        ")\n"
        "\n"
        "func statusHandler(w http.ResponseWriter, r *http.Request) {\n"
        "    w.Header().Set(\"Content-Type\", \"application/json\")\n"
        "    _ = json.NewEncoder(w).Encode(map[string]string{\"status\": \"ok\"})\n"
        "}\n",
    ),
    (
        "python",
        "Write a FastAPI endpoint that accepts JSON {name:str} and returns a greeting.",
        "from fastapi import FastAPI\n"
        "from pydantic import BaseModel\n"
        "\n"
        "app = FastAPI()\n"
        "\n"
        "class GreetingIn(BaseModel):\n"
        "    name: str\n"
        "\n"
        "@app.post('/greet')\n"
        "def greet(payload: GreetingIn):\n"
        "    return {'message': f'Hello, {payload.name}!'}\n",
    ),
    (
        "python",
        "Write a Python async function that fetches a URL with aiohttp and returns text.",
        "import aiohttp\n"
        "\n"
        "async def fetch_text(url: str) -> str:\n"
        "    async with aiohttp.ClientSession() as session:\n"
        "        async with session.get(url, timeout=20) as resp:\n"
        "            resp.raise_for_status()\n"
        "            return await resp.text()\n",
    ),
    (
        "python",
        "Write a Python function that merges two sorted lists into one sorted list.",
        "def merge_sorted(a, b):\n"
        "    i = j = 0\n"
        "    out = []\n"
        "    while i < len(a) and j < len(b):\n"
        "        if a[i] <= b[j]:\n"
        "            out.append(a[i])\n"
        "            i += 1\n"
        "        else:\n"
        "            out.append(b[j])\n"
        "            j += 1\n"
        "    out.extend(a[i:])\n"
        "    out.extend(b[j:])\n"
        "    return out\n",
    ),
    (
        "python",
        "Write a Python CLI that counts lines, words, and chars in a file path argv[1].",
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "def main():\n"
        "    path = Path(sys.argv[1])\n"
        "    text = path.read_text(encoding='utf-8')\n"
        "    lines = text.count('\\n') + (1 if text and not text.endswith('\\n') else 0)\n"
        "    words = len(text.split())\n"
        "    chars = len(text)\n"
        "    print(f'{lines} {words} {chars} {path}')\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
    ),
    (
        "javascript",
        "Write a Node.js Express server with GET /health returning {ok:true}.",
        "const express = require('express');\n"
        "const app = express();\n"
        "\n"
        "app.get('/health', (req, res) => {\n"
        "  res.json({ ok: true });\n"
        "});\n"
        "\n"
        "app.listen(3000, () => {\n"
        "  console.log('listening on 3000');\n"
        "});\n",
    ),
    (
        "typescript",
        "Write a TypeScript function that typesafely picks keys from an object.",
        "export function pick<T extends object, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {\n"
        "  const out = {} as Pick<T, K>;\n"
        "  for (const key of keys) {\n"
        "    out[key] = obj[key];\n"
        "  }\n"
        "  return out;\n"
        "}\n",
    ),
    (
        "python",
        "Write a Discord.py bot command !ping that replies with Pong.",
        "import discord\n"
        "from discord.ext import commands\n"
        "\n"
        "bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())\n"
        "\n"
        "@bot.command()\n"
        "async def ping(ctx):\n"
        "    await ctx.send('Pong')\n"
        "\n"
        "bot.run('TOKEN')\n",
    ),
    (
        "python",
        "Write a pygame window 640x480 titled Navine that exits on quit.",
        "import pygame\n"
        "\n"
        "def main():\n"
        "    pygame.init()\n"
        "    screen = pygame.display.set_mode((640, 480))\n"
        "    pygame.display.set_caption('Navine')\n"
        "    running = True\n"
        "    clock = pygame.time.Clock()\n"
        "    while running:\n"
        "        for event in pygame.event.get():\n"
        "            if event.type == pygame.QUIT:\n"
        "                running = False\n"
        "        screen.fill((20, 24, 32))\n"
        "        pygame.display.flip()\n"
        "        clock.tick(60)\n"
        "    pygame.quit()\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
    ),
    (
        "bash",
        "Write a bash script that finds and deletes *.tmp files under the current directory.",
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "find . -type f -name '*.tmp' -print -delete\n",
    ),
    (
        "python",
        "Write a recursive Python directory walker that yields file paths.",
        "from pathlib import Path\n"
        "\n"
        "def walk_files(root: str):\n"
        "    base = Path(root)\n"
        "    for path in base.rglob('*'):\n"
        "        if path.is_file():\n"
        "            yield str(path)\n",
    ),
    (
        "python",
        "Write a Python function that validates an email with a simple regex.",
        "import re\n"
        "\n"
        "_EMAIL = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')\n"
        "\n"
        "def is_valid_email(value: str) -> bool:\n"
        "    return bool(_EMAIL.match(value or ''))\n",
    ),
    (
        "java",
        "Write a Java method that returns the factorial of n.",
        "public class MathUtils {\n"
        "    public static long factorial(int n) {\n"
        "        if (n < 0) throw new IllegalArgumentException(\"n must be >= 0\");\n"
        "        long result = 1L;\n"
        "        for (int i = 2; i <= n; i++) {\n"
        "            result *= i;\n"
        "        }\n"
        "        return result;\n"
        "    }\n"
        "}\n",
    ),
]


def main() -> None:
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    rows = []
    for lang, user, code in EXAMPLES * 60:
        code = code.rstrip() + "\n"
        blocks.append(
            "### System: You are Navine AI. Write complete runnable code only. "
            "No placeholders, no TODO, no explanations.\n"
            f"### User: {user}\n"
            f"### Assistant: ```{lang}\n{code.rstrip()}\n```\n"
        )
        rows.append({"language": lang, "prompt": user, "code": code})
    OUT_TXT.write_text("\n".join(blocks), encoding="utf-8")
    with OUT_JSONL.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "examples": len(EXAMPLES),
        "blocks": len(blocks),
        "txt": str(OUT_TXT),
        "jsonl": str(OUT_JSONL),
    }
    (OUT_TXT.parent / "real_code_sft_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
