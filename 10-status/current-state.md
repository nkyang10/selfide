# Current Project State

> Snapshot of the last known state. Updated by the agent at the end of EVERY session.
> If reality differs from this file, fix it immediately (drift check).

- **Last updated:** 2026-09-09 (UTC) — session s011 (FE-004 folder-picker tweaks, pending rebuild).
  p003
  fork **deployed live at http://192.168.1.249:4447/** (pid 2617472; binary `0.0.0-dev-202609091003`,
  **built with bun 1.3.14**, includes FE-001..FE-005) with **FE-001** cookie-auth login, **FE-002**
  project-selector fix, **FE-003 foreground re-sync**, **FE-004 folder explorer on mobile**, and **FE-005 iOS
  completion notifications (Web Push)** — server `Push` LayerNode + auth-gated `/api/push/*`, `public/sw.js`
  served publicly, client subscribe util + "Background notifications" settings toggle + boot SW registration.
- **s011 change (code done, NOT deployed):** FE-004 picker tweaks in `dialog-select-directory-v2.tsx` —
  (1) removed "tap highlighted folder again → unhighlight"; (2) picker now lists the tree from filesystem
  root (`/` or `X:`) on open instead of jumping into the last-opened folder (last-opened stays default
  selection); (3) typing a path (`~/...`) + Enter now *reveals* it in the root-level tree (ancestors
  expanded + target highlighted) instead of navigating into it. Local typecheck clean + 25 picker tests
  green. **Next: rebuild + redeploy, then iPhone field test (FU-023).**
- **s010 bugfixes (all deployed):** (1) compiled single-file binary with bun ≥1.4.2 crashes all
  location-scoped v2 endpoints — pinned `scripts/build-linux.sh` to the official `bun@1.3.14`
  (`packageManager`); (2) `/api/push/*` 500'd authenticated (`Service not found: @opencode/Push`,
  request-time service lookup) — fixed in `40b1633`; (3) web-mobile "Thinking" row stuck after a session
  completes — ROOT CAUSE is Cloudflare quick tunnels buffering the SSE body (headers 200 but zero bytes;
  verified empirically), so the app never gets `session.status idle`; fixed in `d1389e2` (reconcile stale
  busy on every reconnect) + `3e46b18` (**15s status watchdog** while any session is busy). Verified end-to-end
  via tunnel with Playwright: thinking DISMISSED. All v2 endpoints + push + UI verified. Unauthed `/` 401,
  unauthed push pubkey 401. Commits on `origin/dev`: `b922fe4`, `e0511c4`, `40b1633`, `d1389e2`, `3e46b18`.
  Full `packages/app` unit suite: 730 pass; `packages/opencode` suite (LANG=C): 3527 pass / 45 fail —
  failures all pre-existing-env (ACP/TUI/plugin/network/locale); typechecks clean. :4445 still runs the
  **official 08-25 binary** (`~/.opencode/bin/opencode`, no FE changes). **HTTPS quick tunnel now**
  `https://orlando-expansion-thu-toxic.trycloudflare.com` (ephemeral; old URL dead) — NOTE: quick tunnels
  buffer SSE bodies so live streaming across the tunnel is refetch-driven, not event-driven. Health checks
  on :4447 use `LANG=C`. Gotcha: login shell exports `OPENCODE_SERVER_PASSWORD` → 401 unless started with
  `env -u`; Basic-auth username is `opencode` (default), not empty. Repeatable via
  `p003/scripts/build-linux.sh` + `run-web.sh`.

## Product vision

A web-interface wrapper around **opencode** (`opencode serve`, HTTP REST + SSE on :4096): better UI, better agentic web, **mobile-multitasking first** — run/monitor/intervene in multiple agent sessions from any device.

- Full research: `40-knowledge/agentic-web-ui-research.md`
- Engineering interface opencode exposes: `40-knowledge/opencode-server-api.md`
- Project brief + MVP: `50-projects/p001-opencode-web-ui/README.md`

## Pending decisions (user)

| FU | Decision | Status |
|---|---|---|
| FU-001 | Tech stack: fork `hsos?` · fork `portal` · fork `opencode-manager` · greenfield | open |
| FU-002 | Deployment target (dev-station / dgx-node-01 / dgx-node-02) | open |
| FU-003 | Auth model (none/Basic/Better Auth) | open |
| FU-005 | GitHub mirror name for this repo | open |

## Environment status

| Host | Status | Notes |
|---|---|---|
| dev-station | up | this folder lives here; s001 scaffold done |
| dgx-node-01 | up (per gdx) | candidate deployment target; see ../gdx |
| dgx-node-02 | up (per gdx) | candidate deployment target; see ../gdx |

## Recent significant changes

| Date (UTC) | Session | Change |
|---|---|---|
| 2026-09-07 | s001 | **Project bootstrap** — full control-center structure for `ide` created; research persisted; p001 brief written. |
| 2026-09-08 | s005 | **Engine rules changed** — 1 role at a time, no retry, timeout → park + product (DEC-011); timeout fix (`_terminate`, 7200s watchdog); marathon restarted on `20260908-0233` cycle-2 (stateful resume, pid 1722974). |
| 2026-09-08 | s006 | **FE-003 foreground re-sync** — mobile web UI auto-refreshes on foreground: heartbeat-liveness stream resume (`server-sdk.tsx`) + forced open-session re-fetch (`directory-layout.tsx`); DEC-013; live on :4447 (pid 1949123); iOS field test pending. |
| 2026-09-08 | s007 | **FE-004 mobile folder explorer** — open-project uses the `@pierre/trees` v2 dialog on all platforms, starts at the last opened project's folder, tap-to-deselect, "Select folder" opens highlighted-or-current folder; full-viewport on phones; DEC-014; live on :4447 (pid 2229139); iPhone field test pending. |
| 2026-09-09 | s009 | **FE-005 iOS completion notifications (Web Push)** — server side (WebKit research + VAPID + `Push` layer + `/api/push/*` routes) in s008; client side now complete (service worker + subscribe util + settings toggle + boot SW registration + i18n). Verified: server typecheck, app typecheck, clean `vite build` emitting `dist/sw.js`. DEC-015. Cloudflare quick tunnel brought up (ephemeral URL). |
| 2026-09-09 | s010 | **FE-005 deploy bugs fixed + "Thinking" root cause** — (1) bun ≥1.4.2 compiler breaks v2 endpoints → `scripts/build-linux.sh` pins `bun@1.3.14`. (2) `/api/push/*` 500'd authenticated → fixed `40b1633`. (3) web-mobile "Thinking" row never dismissed → **root cause: quick Cloudflare tunnel buffers SSE body** (headers OK, zero bytes; probed RX/EMIT/store empty); fixed `d1389e2` (reconcile on reconnect) + `3e46b18` (15s status watchdog); Playwright tunnel test DISMISSED. Tunnel URL changed → `orlando-expansion-thu-toxic.trycloudflare.com`. DEC-016. |

## s002 addendum (research only, 2026-09-07)
- New p002 direction proposed: **self-testing/thinking/completing multi-agent dev engine** — multiple
  role agents (PM/architect/dev/QA/reviewer) operating through a GitHub repo (issues→PRs), with a
  self-improvement loop. Research persisted → `40-knowledge/multi-agent-sdlc-engine-research.md`.
- No code written. Awaiting FU-007/FU-008 before scaffolding p002.
- Status doc updated by s002; decisions-log unchanged (no irreversible decision taken).

## s002 addendum 2 (operating model — 2026-09-07)
- p002 design now includes the **overnight cycle** (user-verbatim): hand-off → interview till "good" →
  confirmed kickoff → multi-agent GitHub run (board, self-raised issues, idle researcher) → morning
  report → loop on same repo until "requirement reached". Added FE-002 + `researcher` role; DEC-006.
- Build still not started; FU-007 (go-ahead to build) now concretely means: implement FE-001+FE-002 on a
  scratch repo.

## s002 addendum 3 (engine built — 2026-09-07)
- **p002 engine MVP implemented + dry-run validated**: `scripts/driver.py` (#handoff/clarify/run/report/cycle),
  stdlib `github_api.py`, role prompts (assembler/engineer/qa/reviewer/researcher/retro), config/engine.json,
  `--dry-run` passes end-to-end. DEC-007. Runbook rb-002 added.
- **GitHub live**: new repos `nkyang10/selfide` (main, pushed) = home of the ide control center;
  `nkyang10/cloud-pos-system` = playground for engine test runs. Token scoped admin on both.
- **Engine scope note (user)**: engine is generic — prompt it with ANY project; cloud-pos-system is only
  a test playground.
- Next: live engine run on the playground (needs user go + model config).

## s002 addendum 4 (permissions verified — 2026-09-07)
- Engine's GitHub exchange layer **live-verified all green** on the playground: issues, board comments,
  branch pushes, PR create/later merge, branch delete. Probe = `driver.py probe` (auto self-cleaning).
- Playground repaired along the way: default branch = `main` (clean README), old probe issues/branches removed.
- Git layer got retries (intermittent github.com:443 drops observed; REST unaffected).
- Next: real night-cycle run (FU-012). Token rotation still pending after use (FU-013).

## s005 addendum (engine fires + rule change — 2026-09-08)
- **Cycle-2 marathon timeout post-mortem**: all engineers killed at the 3600s watchdog. Root cause: DGX LLM
  gateway degraded 02:45–03:56Z (3–15 min/completion, 32 slow calls; single GB10 vLLM thrashed by 4–5
  concurrent agents + other boxes). Gateway healthy again after ~03:56Z. Also found: `kill()`-no-`wait()` =
  zombie agents; stdio buffering hid live progress (SIGKILL drops it).
- **New engine rules (DEC-011)**: 1 role/1 agent at a time (researcher before engineers; engineers
  sequential, per-task merge+push), **no retries** (single-attempt agents; marathon stops on a failed/parked
  cycle), **timeout → park** (`cycleN-waiting-product` + epic report) → product arranges next cycle.
  Watchdogs configurable, default 7200s. Fixes in `p002-selfdev-engine/scripts/driver.py`.
- **Marathon restarted** as a **3-cycle smoke test** (cycles 2→4 then stop): pid 1758047,
  `marathon --run 20260908-0233 --start 2 --max 4 --min-gap 0 --repo mark/cloud-pos-system` on Gitea —
  cycle-2 resumes statefully (assembler skipped; prior failed tasks re-run). Evidence: run dir trail/state/workers; gateway log on DGX.
- **Worker activity now LIVE-visible**: each role agent runs through `stdbuf -o0 script -qefc` (PTY), so
  `agent-<role>-<cycle>.log` streams JSONL events in real time (was block-buffered → looked dead). Model
  pinned `dgx/general` in `config/engine.json` → every agent hits the DGX gateway
  `deepseek-ai/DeepSeek-V4-Flash-0731`. `_terminate` uses killpg for the script grandchild.
- **Cycle model refined (s007, DEC-012)**: no park-on-timeout. Engineer task over budget → status **half**
  (worktree+branch+session preserved); marathon runs **small cycles `N.1`/`N.2`** to finish those, then
  proceeds; never-started tasks roll to the next main cycle; engineer load per cycle is "as much as it can
  do" (`engineer.cycle_time_secs`, default 12h). `--cycle` accepts "3.1"; applies from the next marathon
  spawn (cycle 3 is finishing on the previous binary).
- Open: qa/reviewer/designer timeouts still just block-merge (do NOT park) — FU pending on whether to extend rule 3.
