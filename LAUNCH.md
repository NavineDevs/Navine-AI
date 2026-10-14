# Launch Navine AI

1. Double-click `Navine AI.bat` in this folder.
2. Click **Web UI** for chat, image, and video in the browser (`http://127.0.0.1:8765`).
3. Or use the desktop menu: Chat, Image, Video, Voice, Train.
4. Training:
   - GUI: **Train Everything** (full) or **Quick Train**
   - Command: `Navine AI.bat train`

## Modes

Chat, Code, Think, Detective (puzzles/ciphers), Analyze. Image and video have the same mode dropdown.

## First-time setup

```text
Navine AI.bat setup
```

Creates `venv` and installs `requirements.txt`. Then double-click `Navine AI.bat`.

## Sync all six AIs

Keep code, data, checkpoints, configs, and model runners aligned across all projects:

```text
python scripts/sync_all_six.py
```

Source of truth is this folder (`Navine AI`). Re-run after training or data changes until you stop syncing.

## Public tunnel (Cloudflare)

Exposes only Navine AI and Navine AI - Python:

| Hostname | Local |
|----------|-------|
| `https://ai.navinecord.dev` | `http://127.0.0.1:8765` |
| `https://pai.navinecord.dev` | `http://127.0.0.1:8766` |

Tunnel name: `navine-ai`  
Tunnel id: `8327019a-e779-472f-ab47-bf334648483d`  
Credentials/config: `%USERPROFILE%\.cloudflared\` (`navine-ai-config.yml` / `config.yml`)

### Start the tunnel

```text
cloudflare-tunnel.bat
```

Or:

```text
powershell -ExecutionPolicy Bypass -File scripts\start_cloudflared.ps1
```

Start each API locally first (`Navine AI.bat` on 8765, Python project on 8766), then start the tunnel.

### DNS for ai / pai (no cert.pem or auth errors)

`cloudflared tunnel route dns` needs `%USERPROFILE%\.cloudflared\cert.pem` (origin cert from `tunnel login`).

If that file is **missing**, or you see either of these:

```text
Cannot determine default origin certificate path. No file cert.pem
Failed to add route: code: 10000, reason: Authentication error
```

use **dashboard CNAMEs first** (fastest, no login). Do **not** restore `cert.pem.bak-20260821` or `cert.pem.stale-20260821` unless you prefer that path — those caused Authentication error 10000.

Tunnel list/run can still work without `cert.pem`; only CLI DNS routing needs it.

#### Option A (simplest): dashboard CNAMEs — no cert.pem

1. Open [Cloudflare Dashboard](https://dash.cloudflare.com/) → zone **navinecord.dev** → **DNS** → **Records**.
2. Add or edit:

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | `ai` | `8327019a-e779-472f-ab47-bf334648483d.cfargotunnel.com` | Proxied (orange cloud) |
| CNAME | `pai` | `8327019a-e779-472f-ab47-bf334648483d.cfargotunnel.com` | Proxied (orange cloud) |

3. If `ai` / `pai` already exist, edit the target to that `*.cfargotunnel.com` hostname (do not leave a random A record).
4. Start APIs (8765 / 8766), then `cloudflare-tunnel.bat`.

#### Option B: fresh login, then CLI routes

Do **not** copy bak/stale certs back. Get a new cert:

```text
scripts\cloudflare_dns_login.bat
```

Or manually:

```text
cloudflared tunnel login
cloudflared tunnel route dns navine-ai ai.navinecord.dev
cloudflared tunnel route dns navine-ai pai.navinecord.dev
```

In the browser: sign in to the Cloudflare account that owns **navinecord.dev**, then authorize that zone.

Do not delete tunnel credential JSON files (`8327019a-....json`).

#### Optional: API token instead of origin cert

Create a token with **Zone:DNS:Edit** and **Account:Cloudflare Tunnel:Edit** scoped to `navinecord.dev`, then:

```text
set CLOUDFLARE_API_TOKEN=your_token_here
cloudflared tunnel route dns navine-ai ai.navinecord.dev
cloudflared tunnel route dns navine-ai pai.navinecord.dev
```
#### Verify

```text
nslookup ai.navinecord.dev 1.1.1.1
nslookup pai.navinecord.dev 1.1.1.1
cloudflared tunnel info navine-ai
```

Both hostnames should resolve via Cloudflare (proxied). After the tunnel is running, open `https://ai.navinecord.dev` and `https://pai.navinecord.dev`.

Optional Windows service (run elevated):

```text
cloudflared service install --config %USERPROFILE%\.cloudflared\navine-ai-config.yml
```

## Troubleshooting

- `Navine AI.bat help` prints launcher commands
- `python -m navine.cli doctor` runs health checks
- Default text model: `text_enterprise`
- Port: `8765` (see `configs/brand.yaml`)
- Tunnel: `cloudflare-tunnel.bat` (see Public tunnel above)
- No `cert.pem` or auth error on `route dns`: use dashboard CNAMEs (Option A) or `scripts\cloudflare_dns_login.bat` — do not restore bak/stale certs
