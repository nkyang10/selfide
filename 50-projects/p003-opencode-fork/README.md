# p003 — opencode fork: local clone, modifications, own Linux build

**Project:** Vendor the **opencode** source (`github.com/anomalyco/opencode`, MIT), modify it, and build our own
Linux binary instead of relying on prebuilt releases.
**Status:** 🟢 CLONED + SELF-BUILT + SERVING (s003) — `opencode web` live on `http://127.0.0.1:4447/` (cwd `testing/`). No source modifications yet.
**Source:** `opencode/` — vendored clone (git-ignored as a nested repo; never commit it to the ide repo).

## Mission

A sandbox where we can patch opencode itself. Upstream build toolchain is **Bun 1.3+** (never assume it's
installed — bootstrapping the toolchain is part of this project).

## Deliverables map

- `config/` — build/env templates, configs for the fork
- `notes/` — design notes for planned modifications
- `scripts/` — build/bootstrap scripts (source-of-truth)
- `sessions/` — per-modification working notes

## Build recipe (VALIDATED s003 — host is aarch64)

Toolchain used: Bun **1.4.2** (`~/.bun`). Run from `opencode/`:

```bash
bun install                         # OK — 2346 packages
bun ./packages/opencode/script/build.ts --single   # OK — smoke test passed
# binary: packages/opencode/dist/opencode-linux-arm64/bin/opencode
```

## Running the local build (web)

```bash
cd testing
env -u OPENCODE_SERVER_PASSWORD setsid nohup ../opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode web --port 4447 > web-4447.log 2>&1 < /dev/null &
```

- **URL:** http://0.0.0.0:4447/ on the host; from the LAN use `http://192.168.1.249:4447/` (see `hostname -I`). Bound `0.0.0.0`, no auth password.
- **Gotchas (recorded in `notes/build-runtime.md`):** the login shell exports `OPENCODE_SERVER_PASSWORD` (from the older `~/.opencode` install that still runs `web` on 0.0.0.0:4445). If set, the server demands HTTP Basic auth — unset it (`env -u`) or the browser gets 401. **Network exposure:** binding 0.0.0.0 with no password exposes the UI to anyone on the LAN — add a password before serving untrusted networks.

## Vendored clone state

- Cloned: 2026-09-08 (s003) from `https://github.com/anomalyco/opencode.git`
- HEAD at clone: `ecbc6ccac85b3e8087b6445e584318419b9e2b34` (branch `dev`, shallow, 2026-09-08)
- **Forked (s003):** `nkyang10/opencode` (fork of anomalyco/opencode, public). Remotes on the vendored clone:
  - `origin`  → https://github.com/nkyang10/opencode.git (our fork — push here)
  - `upstream` → https://github.com/anomalyco/opencode.git (original — pull latest from here)
- Note: shallow clone (`--depth 1`); consider `git fetch --unshallow` before first push/PR.

## References

- Decisions: DEC-010 (fork project created + vendored as nested repo, 2026-09-08)
- Follow-ups: FU-018 (define first modification on opencode)
- Runtime notes: `notes/build-runtime.md`
