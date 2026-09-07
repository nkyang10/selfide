# ide — Better Agentic Web for OpenCode

This folder is the **single source of truth** for building **a new web-interface layer around the
`opencode` coding agent**: a better UI, a better "agentic web", designed first for **mobile
multitasking** — run, monitor, and intervene in multiple agent sessions from any device
(phone, tablet, desktop).

The agent (opencode) acts as the **controller**: every request is planned, implemented, and logged
here. No out-of-band changes. The folder is maintained by agents for agents — any successor agent
can take over instantly.

> **Git:** local repo. GitHub mirror TBD (see `10-status/open-followups.md` FU-005).
> **Secrets policy:** real `opencode.json` / `*.env` are git-ignored. Never commit live keys.

## Operating model

```
USER (Mark)         AGENT (controller)                      ENVIRONMENT
      |  request  ────────▶  plan + confirm  ─────────────▶  dev-station (this PC)
      │                       implement + test  ─────────▶  dgx-node-01 / dgx-node-02 (candidate hosts)
      │◀──── report ──  log everything  ──────  state snapshot updated
```

## Folder map

| Path | Purpose |
|---|---|
| `AGENTS.md` | **Late-comer agent protocol.** Any future agent MUST read this first and follow it. |
| `00-env/` | Environment inventory: the dev workstation + every deployment target (DGX nodes, mobile browsers). Mirrors gdx's `00-fleet/`. |
| `10-status/` | `current-state.md` (latest known state) + `open-followups.md` (user↔agent tracker). |
| `20-logs/` | Logging system: policy, append-only command log, per-session records, incidents. |
| `30-runbooks/` | Step-by-step procedures for recurring operations (dev loop, deploy, rollback). |
| `40-knowledge/` | Reference material: **research** (agentic-web-ui, opencode server API) + `decisions-log.md` (every implementation decision and why). |
| `50-projects/` | **Per-implementation projects.** `p001-opencode-web-ui` (active — the web UI), `p002-selfdev-engine` (active design — multi-agent self\* dev engine), `p000-TEMPLATE` (blank scaffold). |
| `90-archive/` | Rotated logs and superseded docs. Never delete history — move it here. |
| `scripts/` | Project operation tools (dev/deploy/rollback helpers — populated as the project grows). |
| `.opencode/` | Agent skills for this workspace (e.g. `web-research`). |

## Golden rules

1. **Log everything.** Every executed command goes into `20-logs/command-log.md` (UTC, session ID, target, result).
2. **No secrets in this folder.** Keys/tokens live in env files or keychains — reference them, never paste them.
3. **Destructive operations need explicit user confirmation** (deleting data, changing infra, big refactors).
4. **Update `10-status/current-state.md` at the end of every session** so the next agent starts fresh.
5. **Follow-ups are tracked, never dropped.** Anything pending goes into `10-status/open-followups.md`.
6. **Record EVERY detail.** Research findings → `40-knowledge/`; implementation choices → `40-knowledge/decisions-log.md`. Nothing lives only in chat history.

## Quick start

- Want something done? Ask the agent in chat; it reads status, acts, logs.
- What's pending on you: `10-status/open-followups.md`.
- Where the product lives: `50-projects/p001-opencode-web-ui/`.
- State of the art before you build: `40-knowledge/agentic-web-ui-research.md`.
