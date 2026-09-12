# Current Project State

> Snapshot of the last known state. Updated by the agent at the end of EVERY session.
> If reality differs from this file, fix it immediately (drift check).

- **Last updated:** 2026-09-12 (UTC) — s018 FE-007 DEPLOYED: 0.0.0-dev-202609120534 (pid 305738).
- **p003 deployed fork (current):** live at http://192.168.1.249:4447/ (pid 305738; binary
  `0.0.0-dev-202609120534`, **built with bun 1.3.14**, includes FE-001..FE-007 + s011 + s012 + s013 + s014 + s015 + s017).
  Includes **FE-001** cookie-auth login, **FE-002** project-selector fix, **FE-003 foreground re-sync,
  **FE-004 folder explorer on mobile**, **FE-005 iOS completion notifications (Web Push)**, **FE-006
  sidebar last-prompt subtitle** (session row shows the newest user prompt under the title; row tooltip
  `title\nprompt`; dense popover rows unchanged; **bulk async prefetch** fills all listed rows at 20
  msgs/session ≤25/folder, hover upgrades to 200), **FU-031 → home Sessions tab now shows the real
  last-prompt subtitle** under each title (per-row preview prefetch 20 msgs, 3 concurrent), **s011** picker
  tweaks (root-level listing, reveal-on-typed-path, no unhighlight-on-2nd-tap), **s012** logout button,
  **s013** question/permission-dock dismiss fixes + i18n parity, **s014** removes the tab close (X)
  icon (close still via context menu / middle-click / keybind), **s015** home page split into 2 tabs via
  `SegmentedControlV2` — **Sessions** (default; dedicated `createHomeSessionsTableController` — table of ALL
  folders' sessions sorted by last update; no folder pre-selection needed — `open` auto-resolves+
  selects the session's folder) and **Projects** (original folder-select + session grid, driven by the ORIGINAL
  shared controller — fully preserved, decoupled from Sessions tab in v3), **FE-007 (s018)** → the home
  **Sessions** tab rows are now **mobile-first 3-line cards** (`items-start`): title `flex-1` clamped to
  2 lines + relative time top-right (no fixed 64px), project name as a small muted line under the title with
  v2 folder icon (was a fixed 112–160px column), and the FE-006 last-prompt preview as a 3rd line clamped
  to 2 lines (only when present). Verified login 200 /
  unauthenticated `/` 401 (FE-001 intact); binary grep confirms new markup shipped; log clean. Tunnel URL unchanged
  `https://orlando-expansion-thu-toxic.trycloudflare.com`
  (ephemeral; quick tunnels buffer SSE — live streaming stays refetch-driven).
- **Deploy note (s011 follow-up):** the prior instance (pid 2790696, `0.0.0-dev-202609091626`) **crashed**
  ~6h after deploy — log ended with `MaxListenersExceededWarning: Possible EventTarget memory leak,
  11 event listeners`; tunnel returned 502 until the server was restarted (tunnel itself never expired).
  **OPEN:** root-cause the EventTarget listener accumulation (suspected SSE/EventTarget churn).
- **s013 full scope (code done, now deployed):**
  1. **Question-dock dismiss fix** — "question dock stays open after the user picks an option and submits
     (answer accepted server-side, dock never dismisses)." Root cause: the dock dismissed **only** on the
     `question.v2.replied`/`.rejected` **SSE** event; a lost/buffered event (quick-tunnel SSE buffering known
     since s010, mobile background suspension, stream drop) left the store holding the request → dock stuck.
     Fix: in `session-question-dock.tsx`, on a **successful** `question.reply`/`.reject` mutation, splice the
     answered request out of the shared store (`dismiss()`); `onError` intentionally does NOT clear.
  2. **FU-027 (permission dock)** — same latent bug fixed in `session-composer-state.ts` `decide()`: on a
     successful `permission.reply`, splice the request out of `permission[perm.sessionID]`.
  3. **FU-026 (i18n parity)** — added `sidebar.logout`/`sidebar.logoutConfirm` (English fallback) to all 61
     app-locale files after `sidebar.settings`; parity + full `test:unit` all green (730/730).
  DEC-017. Verification: typecheck clean, oxlint 0 err, `test:unit` 730/730. **Remaining:** iPhone field
  test of FE-004 picker behavior (FU-023).
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
| 2026-09-10 | s013 | **Question-dock + permission-dock dismiss bug fixes; i18n parity green (code done, NOT deployed)** — (1) question dock: dismissal was **SSE-only** (`question.v2.replied`/`.rejected`); a lost/buffered event left the store holding the request, so the dock stayed open after a 200'd reply. Fix: on a **successful** reply/reject mutation, splice the request out of the store (`dismiss()`, DEC-017). (2) FU-027: identical fix for the permission dock in `session-composer-state.ts` `decide()`. (3) FU-026: added the s012 logout keys (English fallback) to all 61 app-locale files; `i18n/parity.test.ts` 5/5. Full `test:unit` **730/730**, typecheck + oxlint clean. |
| 2026-09-12 | s018 | **FE-007 home Sessions-tab row → mobile-first multi-line card** — `home-sessions-table.tsx` `HomeSessionTableRow` redesigned from a one-line strip (fixed 112–160px project column starved text on phones; everything single-line truncated) to a 3-line stacked card: title `flex-1` 2-line clamp + relative time top-right; project name demoted to a muted line under the title with v2 folder icon; FE-006 last-prompt preview as 3rd 2-line-clamped line. `items-start`, avatar top-aligned. Verified typecheck/lint/737 unit tests; built with pinned bun 1.3.14 → `0.0.0-dev-202609120534` (pid 305738) live on :4447, log clean, binary grep confirms new markup. |

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

## s016 addendum (FE-006 code — sidebar last-prompt subtitle, 2026-09-12)
- **FE-006 DEPLOYED** (client-only, `packages/app`) as `0.0.0-dev-202609120234` (pid 219946, :4447).
  Workspace-sidebar session rows now show a **last user prompt** subtitle under the title; the row
  tooltip shows `title\nprompt`; hidden for dense project-popover rows. New util
  `session-last-prompt.ts` extracts the newest user message's real text part from the existing message
  store (prefetch fills it). No server change.
- **Verified:** `bun run typecheck` ✅; `bun run test:unit` ✅ 737 pass / 0 fail (7 new tests);
  **Bulk async prefetch** (same session): on list render, all visible sessions get a small prefetch
  (20 msgs each, ≤25/folder, 2 concurrent) so every row gets its subtitle; hover still upgrades to 200.
- **Build/deploy (10:36 UTC):** `./scripts/build-linux.sh` → 0.0.0-dev-202609120234; old pid 3967592
  killed (`0.0.0-dev-202609111028`); `run-web.sh 4447` → pid 219946. Smoke: unauth `/` 401, `/login` 200,
  authed root 200; served entry `index-BV48gH_b.js` (was `index-CAzbSeqL.js`); served bundle contains
  `lastPrompt` + `text-text-secondary`. FU-030 **closed**.
- **FU-031 (new, user-decide):** reuse FE-006's prompt extraction in the home **Sessions tab** (which
  currently uses `session.title` = last prompt as proxy — original FU-029).

## s017 addendum (chat-header close button, 2026-09-12)
- **s017 code complete (client-only, `packages/app`), NOT built/deployed.** Adds an X (close-tab)
  button in the session chat header, immediately right of the 3-dots "more options" trigger (the menu
  that contains Archive). It closes the current agent/session tab via the top-level tabs store
  `closeTab` (records for reopen, mirrors titlebar `tab.close`). Renders in both v2 and legacy layouts
  and on child agent sessions. Restores an in-body close affordance after s014 removed the titlebar X.
- **Verified:** `bun x tsgo -b packages/app` ✅; `bun x oxlint message-timeline.tsx` ✅ (no new warnings).
- **Deployed** with FU-030 build 0.0.0-dev-202609120234 (pid 219946) — **closed**, smoke verified in
  s016's deploy pass (chat-header X bundled in same binary).

## s018 addendum (FE-007 home Sessions-tab row → mobile-first multi-line card, 2026-09-12)
- **FE-007 DEPLOYED** (client-only, `packages/app`) as `0.0.0-dev-202609120534` (pid 305738, :4447).
  The starting/home **Sessions** tab's session row was a one-line strip whose fixed project column
  (112–160px) ate half a phone's width and truncated every text field. Now a **3-line mobile card**
  (`items-start`): **title** `flex-1` clamped to **2 lines** with the **relative time top-right** (no
  reserved 64px), **project name** demoted to a muted line under the title with the v2 **folder** icon,
  and the **FE-006 last-prompt preview** as a third line clamped to **2 lines** only when present.
  No controller/schema change; markup only in `home-sessions-table.tsx`.
- **Why multi-line clamp:** the question dock already used `-webkit-line-clamp`, so we reuse the same
  inline-style pattern; `truncate` was dropped for the title and prompt.
- **Verified:** `bun run typecheck` ✅; `bun run test:unit` ✅ 737 pass / 0 fail; oxlint clean.
- **Build/deploy (13:35 UTC):** `./scripts/build-linux.sh` (pinned bun 1.3.14) → version
  `0.0.0-dev-202609120534`; old pid **248812** killed (`0.0.0-dev-202609120259`, s017 build); `run-web.sh
  4447` → pid **305738**. Smoke: unauth `/` 401 (FE-001 login page active, unchanged), server log clean;
  binary grep finds `items-start justify-between gap-3` (new title row markup) → change is compiled in.
- **Follow-up:** visual check on a physical phone (FU-028 area) — confirm long titles warp to 2 lines,
  project line + folder icon render, long prompt previews wrap.
