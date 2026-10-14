# Navine Game Bridge Protocol v1

Connect Minecraft, Fortnite, or other game mods to Navine AI for PVP coaching, speedrun learning, and agent play.

## Endpoints

| Type | URL |
|------|-----|
| WebSocket | `ws://127.0.0.1:8766/api/games/ws` (PAI) or your Navine server port |
| REST info | `GET /api/games/bridge/info` |
| Create session | `POST /api/games/session` |
| Send event | `POST /api/games/event` |
| Speedrun split | `POST /api/games/speedrun/split` |
| Coach | `POST /api/games/coach` |
| Pull AI commands | `GET /api/games/commands/{session_id}` |

## WebSocket handshake

Send JSON after connect:

```json
{
  "title": "minecraft",
  "mode": "pvp",
  "client_id": "my-mod-instance-1"
}
```

Server replies:

```json
{
  "type": "hello",
  "session_id": "abc123",
  "title": "minecraft",
  "mode": "pvp",
  "protocol": "navine-game-bridge/v1"
}
```

## Modes

- `learn` — log events for training, return coach advice
- `pvp` — PVP-focused advice (Minecraft crystal/sword, Fortnite builds)
- `speedrun` — split timing and route coaching
- `agent` / `play` / `auto` — AI queues in-game commands

## Event messages (client → server)

```json
{
  "type": "state",
  "payload": {
    "title": "minecraft",
    "health": 14,
    "food": 18,
    "x": 120.5,
    "y": 64,
    "z": -880.2,
    "dimension": "overworld",
    "held_item": "diamond_sword",
    "enemy_near": true,
    "note": "creeper behind wall"
  }
}
```

PVP elimination:

```json
{
  "type": "elimination",
  "payload": {
    "title": "fortnite",
    "kills": 3,
    "deaths": 1,
    "zone_phase": 4,
    "materials": {"wood": 120, "brick": 40, "metal": 20}
  }
}
```

Speedrun split:

```json
{
  "type": "speedrun_split",
  "payload": {
    "title": "minecraft",
    "segment": "enter_nether",
    "time_ms": 312000,
    "delta_ms": -4200
  }
}
```

## Server responses

Advice ack:

```json
{
  "type": "ack",
  "ok": true,
  "session_id": "abc123",
  "advice": "PVP (minecraft): Strafe while blocking...",
  "commands": []
}
```

AI command (when mode is `agent`):

```json
{
  "type": "command",
  "command": {
    "action": "keys",
    "keys": ["sprint", "crouch"]
  }
}
```

Command actions your mod should handle:

| action | fields | example |
|--------|--------|---------|
| `keys` | `keys[]` | `["w","space","shift"]` |
| `use` | `item` | heal, pearl, block |
| `say` | `text` | chat message |
| `click` | `button`, `x`, `y` | mouse action |
| `macro` | `name` | mod-defined macro |
| `notify` | `text` | HUD toast |

## Minecraft Fabric mod outline

1. Add dependency on a WebSocket client library (Java-WebSocket or Netty).
2. On world join, connect to `ws://127.0.0.1:8766/api/games/ws`.
3. Every tick (or every N ticks), send `state` with player position, health, inventory summary.
4. On damage, death, kill, or block break milestones, send typed events.
5. Poll `pull_commands` or listen for WebSocket `command` messages.
6. Map `keys`/`use` to Minecraft keybinds via your mod's input layer.

Example Java send (pseudo):

```java
JsonObject payload = new JsonObject();
payload.addProperty("health", player.getHealth());
payload.addProperty("x", player.getX());
payload.addProperty("y", player.getY());
payload.addProperty("z", player.getZ());
JsonObject msg = new JsonObject();
msg.addProperty("type", "state");
msg.add("payload", payload);
ws.send(msg.toString());
```

## Fortnite / external games

Fortnite has no official mod API for live PVP state. Options:

- **Replay / stats overlay** — export eliminations and zone phase from tracker apps into `POST /api/games/event`.
- **Screen bridge** — use existing `POST /api/games/observe` for vision-based coaching.
- **UEFN creative** — log training events to a local HTTP forwarder that posts to Navine.

## Training loop

Events are stored under `data/train/games/sessions/bridge_*` as `events.jsonl`.
Speedrun splits go to `speedrun_splits.jsonl` and `speedrun_corpus.txt`.
Run `python -m navine.cli train games` or include in the marathon to fine-tune the games model.

## Test without a mod

```bash
python scripts/game_bridge_client.py --title minecraft --mode pvp
```
