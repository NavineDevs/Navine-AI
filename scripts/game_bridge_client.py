"""Test client for Navine game bridge (Minecraft/Fortnite-style events)."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time

try:
    import websockets
except ImportError:
    print("Install websockets: pip install websockets")
    raise SystemExit(1)


async def run_client(host: str, port: int, title: str, mode: str) -> None:
    uri = f"ws://{host}:{port}/api/games/ws"
    async with websockets.connect(uri) as ws:
        await ws.send(
            json.dumps(
                {
                    "title": title,
                    "mode": mode,
                    "client_id": f"test-{int(time.time())}",
                }
            )
        )
        hello = json.loads(await ws.recv())
        print("connected:", json.dumps(hello, indent=2))
        session_id = hello.get("session_id")
        samples = [
            {
                "type": "state",
                "payload": {
                    "title": title,
                    "health": 12,
                    "x": 100,
                    "y": 64,
                    "z": -200,
                    "enemy_near": True,
                },
            },
            {
                "type": "elimination" if mode == "pvp" else "speedrun_split",
                "payload": {
                    "title": title,
                    "kills": 2,
                    "deaths": 1,
                    "segment": "first_nether",
                    "time_ms": 305000,
                    "delta_ms": -1500,
                },
            },
        ]
        for msg in samples:
            await ws.send(json.dumps(msg))
            reply = json.loads(await ws.recv())
            print("reply:", json.dumps(reply, indent=2))
            cmd = await asyncio.wait_for(ws.recv(), timeout=2.0)
            try:
                extra = json.loads(cmd)
                if extra.get("type") == "command":
                    print("command:", json.dumps(extra, indent=2))
            except Exception:
                pass
            await asyncio.sleep(0.5)
        await ws.send(json.dumps({"type": "pull_commands"}))
        cmds = json.loads(await ws.recv())
        print("commands:", json.dumps(cmds, indent=2))
        print(f"session_id={session_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Navine game bridge test client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--title", default="minecraft")
    parser.add_argument("--mode", default="pvp", choices=["learn", "pvp", "speedrun", "agent"])
    args = parser.parse_args()
    asyncio.run(run_client(args.host, args.port, args.title, args.mode))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
