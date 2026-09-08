# Session s003 — p003: opencode fork project (local clone + own Linux build)

- **Date:** 2026-09-08 (UTC)
- **Goal:** Create a new project under `50-projects/` whose purpose is **modifying opencode itself**. Pull the opencode source, build our own Linux binary, and start the web UI in the `testing/` folder on port 4447.
- **Status:** ✅ COMPLETE — cloned, built, serving.

## Actions

1. Scaffolded `50-projects/p003-opencode-fork/` (README, config/, notes/, scripts/, sessions/) + added `.gitignore` entry for the vendored clone.
2. Cloned `https://github.com/anomalyco/opencode.git` (shallow) → `opencode/`, HEAD `ecbc6cc…` on `dev`.
3. Confirmed with user, then installed Bun 1.4.2 (`~/.bun`) via official installer.
4. `bun install` (2346 pkgs) + `bun ./packages/opencode/script/build.ts --single` → `packages/opencode/dist/opencode-linux-arm64/bin/opencode` (host is aarch64). Smoke test passed (`0.0.0-dev-202609072334`).
5. Created `testing/` folder; first `opencode serve --port 4447` returned Basic-auth 401 — traced to the login shell leaking `OPENCODE_SERVER_PASSWORD` (from the older `~/.opencode` install running on :4445). Restarted as `opencode web --port 4447` with `env -u OPENCODE_SERVER_PASSWORD` → http://127.0.0.1:4447/ returned 200.
6. Rebound to `--hostname 0.0.0.0`: web UI now reachable from the LAN at http://192.168.1.249:4447/. Updated `scripts/run-web.sh`.
7. **Forked** `anomalyco/opencode` → **`nkyang10/opencode`** (user tapped Fork in the mobile GitHub app after the fine-grained PAT got `Resource not accessible` on the forks API). Re-wired the vendored clone: `origin` = our fork, `upstream` = original. PAT session token deleted from `/tmp` after use.
8. Wrote repeatable scripts `scripts/build-linux.sh` + `scripts/run-web.sh`, runtime gotchas in `notes/build-runtime.md`.

## Results / evidence

- Clone + build tree: `50-projects/p003-opencode-fork/opencode/`
- Fork: https://github.com/nkyang10/opencode (public, fork of anomalyco/opencode)
- Running process: `opencode web --port 4447 --hostname 0.0.0.0` (pid 1445769) in `testing/`, log `testing/web-4447.log`
- Refs: DEC-010 · FU-018 · FU-019 · `notes/build-runtime.md`

## Follow-ups created

- FU-018: define the first source modification to make in the p003 fork (owner: user/agent, due: next session).
- FU-019: rotate the GitHub PAT shared in chat during this session (never reuse it).
