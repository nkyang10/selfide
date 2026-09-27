# Agent Workspace — where everything lives (shared, transparent, Gitea)

> For every agent (and human) working together — the single source of truth.
> Any new agent MUST read in order: this file → `AGENTS.md` → the pinned STATUS issue on
> `mark/selfide` → `10-status/current-state.md`.

## What lives where

| Content | Location | How agents use it |
|---|---|---|
| Agent protocol + this map | `AGENTS.md`, `docs/agent-workspace.md` (mono repo `mark/selfide`) | read first on bootstrap |
| Knowledge + decisions | `40-knowledge/` (+ `decisions-log.md`), `30-runbooks/` | repo markdown; changed via **PR/review** (a librarian agent approves) |
| Status snapshot + open follow-ups | `10-status/*.md` + **pinned issue #1** on `mark/selfide` ("STATUS — agent workspace (live)") | day-to-day: comment on the pinned issue; snapshot updated each session close-out |
| **Feature list / roadmap / backlog** | Gitea-native on `mark/cloud-pos-system`: issues + `Cloud POS — 12 targets` **Milestone** + labels (`epic`, `engine/proposal`, `enhancement`, `idea`, `followup`, `do-today`) | engine files designs as `[proposal]`/`[epic]` issues → they land on the board view (`?labels=…` or the Roadmap project board when enabled) |
| Engine + automation code | mono repo `mark/selfide` · `50-projects/p002-selfdev-engine/` (driver, prompts, config) | PR-reviewed; runs target `mark/cloud-pos-system` via Gitea env |
| Product code | `mark/cloud-pos-system` | the build; engine ships via branches/PRs/direct-push |
| Audit logs / run state | `20-logs/` (command-log, sessions, incidents), `ENGINE_STATE/` (run artifacts) | append-only; incidents also become issues |
| Secrets / tokens | **never in repos** — per-agent env (`GITEA_TOKEN` from `~/.gitea-engine-token`, etc.) | reference, don't commit |

## Conventions for a growing multi-device agent team

- **GitHub is the only origin** (changed 2026-09-27): this folder's `origin` is now
  `https://github.com/nkyang10/selfide.git` and the LAN Gitea remote was **removed**, so `git push` needs no
  extra arguments. The 17 commits that had never left this machine (s012 → s071, through `7877e9af9`) went to
  GitHub as a fast-forward — the Gitea copy was two weeks behind (`5c847a6f9`, 2026-09-12) and had nothing the
  GitHub copy lacked. The credential is a GitHub fine-grained PAT in `~/.git-credentials` (mode 600, **outside**
  this folder); it also reached the LAN Gitea, which is why the mirror is a safe target. For the *other* repos the
  Gitea convention still applies (`mark/cloud-pos-system`): clone from `http://192.168.1.162:3300/…`, token in
  `~/.gitea-engine-token`. Never keep knowledge only on one device.
- **Named identities**: each agent commits with its own `user.name`/`user.email` so the log attributes work.
- **Per-agent tokens** preferred; a shared git token never goes into files.
- **Before acting**: fetch latest → read status (pinned issue + `10-status/`) → read follow-ups → claim/comment before big work, so two agents don't collide.
- **Every completed step is visible**: engine comments on issues (board), run logs land in `20-logs/`, knowledge persists to `40-knowledge/` in the same repo.
- **Roadmap kanban (optional)**: the Projects feature is currently disabled on the Gitea server; enabling it
  requires `app.ini` (`[repository]` project settings) or a server config change + restart by the admin.
  Labels + milestone already give a fully queryable board via the Issues page.

## Environment for agent runs (Gitea layer)

```
source 50-projects/p002-selfdev-engine/scripts/engine-env-gitea.sh   # sets ENGINE_GITEA=1, GITEA_TOKEN, bases
# target repo: mark/cloud-pos-system   (already the engine default)
```
