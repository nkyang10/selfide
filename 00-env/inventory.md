# Environment Inventory

> Canonical registry of every host this project touches. The agent updates this whenever facts change.
> Fields marked `TODO` are pending user input — see `10-status/open-followups.md`.

## Host aliases

| Alias | Role | How to reach |
|---|---|---|
| `dev-station` | **Primary dev + run host.** This Linux workstation; this folder (`/home/mark/Desktop/ide`) lives here. Runs `opencode`, dev servers, and (eventually) the web UI. | local shell |
| `dgx-node-01` | Deployment candidate. Host of the live DeepSeek stack + model gateway (see gdx). | SSH (`mark@192.168.1.202`) |
| `dgx-node-02` | Deployment candidate. NFS client of UP-STORE over 200G DAC. | SSH (`mark@192.168.1.249`) |
| `mobile` | Target browsers: any phone/tablet running the PWA. | network (LAN/Tailscale/VPN — TBD) |

> **Authority for DGX details:** this folder does **not** duplicate node dossiers — see
> `../gdx/00-fleet/` (dgx-node-01.md / dgx-node-02.md / access-and-network.md) for full specs.

## Hosts

### dev-station (this PC)

| Field | Value |
|---|---|
| Role | Development + primary controller host |
| Folder | `/home/mark/Desktop/ide` (this project) |
| OS | Linux (desktop) |
| Tooling | opencode CLI (model: `dgx/general`), git, python3, bun/node (TBD versions) |
| Web-research | `SERPER_API_KEY` in `~/.bashrc`; skill at `.opencode/skills/web-research/` |
| TODO | Node/bun versions to record on first install |

### dgx-node-01 / dgx-node-02

| Field | Value |
|---|---|
| Role | Candidate deployment targets for opencode servers + the web UI |
| Detail | See `../gdx/00-fleet/dgx-node-01.md` / `dgx-node-02.md` |
| TODO | Confirm which node(s) should host the UI + opencode servers (FU-002) |

## Connectivity plan (mobile → UI, TBD)

- LAN (same Wi-Fi) — simplest, `opencode serve` Basic-auth over HTTPS-in-front
- Tailscale — preferred once nodes are on the tailnet
- Cloudflare/ngrok tunnel — fallback for phone-away-from-home

Decisions land in `40-knowledge/decisions-log.md` (DEC-00x) once the deployment target is chosen.

## Ownership & policy

| Field | Value |
|---|---|
| Owner | Mark |
| Controller agent | opencode, session-based via this folder |
| Change approval | User confirms any destructive/major change before execution |
