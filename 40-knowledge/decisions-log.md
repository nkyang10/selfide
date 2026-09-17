# Implementation Decisions Log (ADR-lite)

> Every non-trivial implementation/setup decision gets an entry here: what was decided, why,
> what was rejected. Append-only. This is how future sessions understand *why things are the way they are*.

Format:

```
### DEC-<NNN> — <title> (<YYYY-MM-DD>)
- **Decision:**
- **Rationale:**
- **Alternatives rejected:**
- **Consequences / revisit when:**
```

---

### DEC-001 — Folder-as-control-center, agent-maintained docs (2026-09-07)
- **Decision:** All project work runs from this folder; AGENTS.md bootstraps any future agent; logs are append-only markdown (no database/tooling dependency). Structure mirrors gdx.
- **Rationale:** Same benefits as gdx: portable, human-readable, works offline, full auditability; user explicitly asked for the same structure.
- **Alternatives rejected:** External PM tooling; chat-only memory (lost between sessions).
- **Consequences:** Agents must diligently close out sessions or the system decays; rotation policy in `20-logs/POLICY.md`.

### DEC-002 — Capture the 7-level research as permanent knowledge (2026-09-07)
- **Decision:** The web/UX/architecture research done for this project is persisted verbatim-ish into `40-knowledge/agentic-web-ui-research.md` + `40-knowledge/opencode-server-api.md`, with source URLs, so no re-research is needed.
- **Rationale:** Golden rule #6; research consumed expensive parallel searches; future sessions must not repeat it.
- **Alternatives rejected:** Leaving it in chat history only.
- **Consequences:** Knowledge docs are the reference for the p001 brief; update them when new facts land.

### DEC-003 — Build on opencode's HTTP+SSE server API, NOT ACP, for the web UI (2026-09-07)
- **Decision:** The web UI (backend) will talk to `opencode serve` over REST + SSE (port 4096) via `@opencode-ai/sdk` or raw HTTP. ACP (stdio JSON-RPC) is out of scope for the browser path.
- **Rationale:** opencode's server API is exactly what all working community UIs use (portal, oc-web, opencode-vibe, native mobile clients); browsers cannot spawn stdio children so ACP requires a stdio→HTTP bridge (ngent-style) with no benefit here; one codebase can later drive multiple opencode instances by pointing at multiple ports.
- **Alternatives rejected:** ACP-over-stdio fixed to a local proxy (extra moving part); WebHook-only model (no push channel).
- **Consequences:** All live/SSE event subscriptions use `GET /event`; auth is opencode's HTTP Basic (see FU-003).

### DEC-004 — Stack decision DEFERRED to user (FU-001) with recommendation (2026-09-07)
- **Decision:** No code yet. Three candidate paths on the table: (A) greenfield Bun+Hono+React PWA, (B) fork `hosenur/portal` (lean mobile-first baseline), (C) fork `chriswritescode-dev/opencode-manager` (most complete: auth, push, cron, supervision). Recommendation: B or C to bootstrap, then beat the incumbent on mobile multitasking UX.
- **Rationale:** All three proven; greenfield costs time but zero legacy; forking captures working SSE/process-management fast.
- **Alternatives rejected:** — (open, awaiting user).
- **Consequences:** Revisit when FU-001 is answered; record the pick here.

### DEC-006 — p002 operating model is a user-driven overnight night-cycle (2026-09-07)
- **Decision:** p002's primary user-facing flow is the **overnight cycle**: user hands off work +
  target feature before sleep → engine↭user clarifying interview until both say "good" → confirmed
  kickoff → autonomous multi-agent run on **one GitHub repo** (planning, deploying, shared board via
  issue/PR comments, self-raised child issues solved by other agents, an idle **researcher** agent
  doing web research to steer toward the requirement) → morning report → loop on the same repo until
  the user says "requirement reached". Captured as FE-002; roles grow a `researcher`.
- **Rationale:** this is the user-specified usage (async, mobile-friendly, bounded overnight cost,
  GitHub as workspace+board+audit trail); it also demos the "agents raising issues other agents solve"
  emergent pattern from the research (MetaGPT SOP teams + Copilot-issue-to-PR spine + researcher).
- **Alternatives rejected:** synchronous day-time full-autonomy loop with no gates (user stays out, but
  wanted interview + "good" gate before kickoff); separate external board tool (use GitHub only).
- **Consequences / revisit when:** `kickoff: confirm` default is a hard safety gate; morning report is
  mandatory; `duration_hours` caps night spend. When p001 exists, the interview + morning report move
  to the mobile push channel.

### DEC-007 — p002 MVP engine: driver in stdlib Python, roles as generated opencode agents (2026-09-07)
- **Decision:** Engine = `scripts/driver.py` (argparse, subcommands handoff|clarify|run|report|cycle) +
  a thin stdlib `github_api.py` REST client; role agents are **generated** into each worktree's
  `.opencode/agent/` from canonical `prompts/<role>.md` (frontmatter table in driver). Config is
  `config/engine.json` (TOML/YAML avoided — stdlib only). Target repo is pluggable (`--repo owner/name`).
- **Rationale:** stdlib-only keeps the engine dependency-free; generated agents keep `prompts/` as a
  single improvable source of truth (RETRO edits prompts, not copies). `--dry-run` gives risk-free testing.
- **Alternatives rejected:** `gh` CLI dependency (not installed here); YAML/TOML config (no yaml in stdlib);
  hand-maintained agent files per checkout (drift risk with RETRO).
- **Consequences / revisit when:** opencode agent `permission` must be **block-style YAML** (inline `{...}`
  was rejected by opencode's schema validator — verified live 2026-09-07); agents use `mode: all` so
  `opencode run --agent` can drive them; re-verify on opencode upgrades.

### DEC-005 — p002: the self* development engine, designed not built (2026-09-07)
- **Decision:** New active project `50-projects/p002-selfdev-engine`: a self-hostable engine where role
  agents (assembler, engineer, QA, reviewer, retro) drive a product through GitHub (issue→branch→PR),
  with a test-to-green gate and a retrospective loop that improves the engine's own briefs. User chose
  **design-doc-first** and **fresh scratch repo** as the first target. Blank scaffold renamed
  `p002-TEMPLATE` → `p000-TEMPLATE` to free the p002 number.
- **Rationale:** The final IDE (p001) is a large target; smallest proof of the core *self-test/
  think/complete* loop first. Design-doc-first per user; scratch repo avoids risk to real code early.
- **Alternatives rejected:** building directly (user chose design first); self-hosting the loop on the
  ide repo itself as first run (deferred); using SWE-bench as the initial eval substrate (heavy — MVP
  uses a small scratch task set instead).
- **Consequences / revisit when:** FE-001 spec + config drafted, prompts v1 placeholders. Code starts
  next session once prompts are written and scratch repo flow verified. If promises/drivers change, the
  driver may move from bash/Python to opencode-server API — that's also the p001 integration point.

### DEC-008 — Engine is deployed inside the selfide repo as a subfolder (2026-09-07)
- **Decision:** The p002 engine ships as `50-projects/p002-selfdev-engine/` inside `nkyang10/selfide`
  (not its own repo). User chose "push into selfide (subfolder)" over a dedicated public/private repo.
- **Rationale:** keeps the control-center single-repo model; the engine's self-improvement loop can
  still operate on its own subfolder via branch/PR.
- **Alternatives rejected:** dedicated `nkyang10/selfdev-engine` repo (public/private) — offered, not chosen.
- **Consequences / revisit when:** if the engine gains independent consumers, split it out then (git subtree).

### DEC-009 — Live-run findings: opencode agent path, git ref namespace, GitHub 5xx (2026-09-07)
- **Decision:** Keep three hard-won rules in the driver: (1) always pass **absolute** `--dir` to opencode
  subprocesses (relative `.` fails agent loading when exec'd without a shell → "Unexpected server error");
  (2) task branches are **flat** `engine/<rid>-tN` (a `engine/<rid>/tN` sub-branch conflicts with the
  `engine/<rid>` ref in git's namespace); (3) the GitHub REST client **retries on 5xx** (observed a
  transient `500` on create_pr that succeeded minutes later).
- **Rationale:** all three were discovered during the first live run — each caused a real abort, once
  against DNS-flaky and slow GitHub connectivity.
- **Alternatives rejected:** treating those as environment noise (they're reproducible: repro showed
  relative-dir fails 6/6 when python-exec'd); dot-nested task branch names.
- **Consequences:** next cycle should self-complete the ship phase without manual help.

### DEC-010 — p003: opencode fork project, vendored clone + own Linux build (2026-09-08)
- **Decision:** New active project `50-projects/p003-opencode-fork`: the **upstream opencode source is
  vendored** as a git-ignored nested clone at `p003/opencode/`, we build our own binary on this machine
  (Bun 1.4.2 in `~/.bun`; `scripts/build-linux.sh`), and every future modification to opencode itself is
  developed here, then optionally upstreamed as a PR. The cloned repo is **not** tracked by the ide repo.
- **Rationale:** the mbot end-goal (p001/p002) will eventually need changes inside opencode (server API,
  auth, SSE, permissions). Having a validated from-source build (aarch64) makes patches cheap to test
  locally instead of waiting for upstream releases.
- **Alternatives rejected:** relying on prebuilt opencode binaries only (cannot carry local patches);
  `git submodule` (nested plain clone is simpler; history is upstream-owned).
- **Consequences / revisit when:** keep the clone shallow (`--depth 1`); re-run `build-linux.sh` after
  pulling upstream. Watch upstream rename/`dev`-branch instability. Build host is aarch64 → binary is
  `opencode-linux-arm64`. **Update (same day):** GitHub fork exists at `nkyang10/opencode`; vendored
  clone remotes = `origin` (fork) + `upstream` (original). API fork failed — user created it via the
  GitHub app (fine-grained PAT lacked fork permission). Re-point pushes at origin; unshallow before first PR.

### DEC-011 — FE-001: login landing page with cookie auth instead of the raw Basic prompt (2026-09-08)
- **Decision:** When the server has a password configured, an unauthenticated **browser** request to any
  path gets a served **login landing page** (401 HTML, `?next` preserved) instead of the browser's Basic
  dialog. `POST /login` validates against `ServerAuth` and sets an `oc_creds` cookie (`base64(user:pass)`,
  `HttpOnly; SameSite=Lax; Path=/`; `Max-Age=1y` when **remember-me** is ticked, session cookie otherwise);
  both the UI router gate and the JSON API gate translate that cookie into Basic credentials. `GET /logout`
  clears it. No password configured → behavior unchanged (open server).
- **Rationale:** requested by user for iOS "Add to Home Screen" shortcuts: a server-set cookie persists in
  WKWebView where app localStorage/headers can be unreliable; a real login page gives a typical
  fail/retry/redirect-back flow. Cookie is passed automatically on every subrequest (SPA shell + SSE/API).
- **Alternatives rejected:** client-side-only login (localStorage) — dies on iOS shortcut scope; keeping
  the native Basic prompt — ugly, no remember-me, breaks redirect-back; token-in-URL (existing
  `auth_token`) — leaks in logs/history.
- **Consequences / revisit when:** `oc_creds` is base64 (not armored) — same trust as Basic on a LAN;
  don't expose 0.0.0.0 outside a trusted network. Raw router routes got no request-time
  `ServerAuth.Config` (Effect service-error) — resolved by resolving config in the router builder and
  passing it into the handler. Re-check upstream merge conflict risk: `packages/server` and
  `packages/opencode` auth files will conflict if upstream refactors auth (likely — it's experimental).

### DEC-012 — FE-002: guard the dev-branch file-search 500 so the project picker works (2026-09-08)
- **Decision:** `FileHttpApi.list` + `.findFile` (the endpoints the project selector needs) 500 with a
  layer-compile defect (`TypeError: undefined is not an object (evaluating 'a.name')`) on this dev-branch
  build — **pre-existing, unrelated to our auth changes** (stock stable build serves them fine). Rather
  than fix Effect's `LayerNode` compiler internals (deep/risky), wrap both handlers with
  `Effect.catchCause` and make `list` fall back to a **plain FSUtil listing** (real dir entries,
  no gitignore filtering) when the per-location layer fails to build.
- **Rationale:** restores the project selector ("button next to (dev)") end-to-end while keeping the
  change small and isolated to one handler file. The location layer `LocationServiceMap.Service.get(ref)`
  at request time is the fragile part in this snapshot.
- **Alternatives rejected:** patching `layer-node.ts` compile internals (high regression risk); returning
  hard empty arrays (selector opened but directory browsing dead).
- **Consequences / revisit when:** fallback listing ignores gitignore and sorts plainly — acceptable on a
  personal server. If upstream fixes the layer compile, drop the guard. See `file.ts` FE-002 comments.

### DEC-010 — Engine repo layer moves to a local Gitea (2026-09-08)
- **Decision:** The p002 engine now targets a self-hosted **Gitea** (http://192.168.1.162:3300, gitea 1.27.3,
  user `mark`). Repos migrated from GitHub by import: `mark/cloud-pos-system` (full git history; issues not
  imported) and `mark/selfide`. Engine adapter: `ENGINE_GITEA=1` + `GITEA_TOKEN` (~/.gitea-engine-token) +
  `ENGINE_GITEA_BASE` + `ENGINE_GIT_ROOT`; API differences handled (label name→id, PR head without owner
  prefix, merge via POST `{"Do":"merge"}`, DELETE branches, base URL + token auth).
- **Rationale:** GitHub `POST /pulls` was returning 500 (empty body) persistently on this account (inc-001);
  a local Gitea removes that dependency and the network flakiness, and keeps PR/review semantics.
- **Alternatives rejected:** continuing on GitHub (blocked); plain `direct_push` only (loses PR semantics
  long-term); migrating to GHES self-host (heavier than Gitea).
- **Consequences / revisit when:** engine runs double as remote GH (default) or Gitea (`ENGINE_GITEA=1`).
  Git notes: `git <owner>` default config is currently GitHub; launch scripts set GITEA env. GitHub remote
  repos remain authoritative for the ide control center; Gitea selfide is a second mirror.

### DEC-011 — Engine operating rules: one role / no retry / park on timeout (2026-09-08)
- **Decision:** The p002 driver runs **at most one agent per role** (researcher blocks before engineers;
  engineer tasks strictly sequential), **never retries** a failed or timed-out agent/cycle, and on a task
  exceeding its timeout **reports to the product (epic board) and parks** the run
  (`cycleN-waiting-product`, marathon stops) until the product arranges the next cycle.
- **Rationale:** The single GB10 LLM backend was saturated by 5 concurrent agents (cycle-2: 4 engineers +
  researcher) → per-completion latency 3–15 min → all killed by the 1h watchdog with no usable result
  (s005 diagnosis). Serial roles + a bigger configurable watchdog (7200s) keep the GPU load sane, and
  "parks, never retries" makes every failure a visible product decision instead of silent churn.
- **Alternatives rejected:** bigger parallel pools + longer timeouts (still thrashes the backend);
  auto-retry (wasted hours on a degraded gateway, hides failures); background-resume of a parked cycle
  (product explicitly wants control of the next cycle).
- **Consequences / revisit when:** state is preserved per-task (merged+pushed immediately; `workers-*.jsonl`
  + `_phase()` resume), so a parked cycle re-runs only incomplete tasks. Follow-ups: decide whether
  qa/reviewer/designer timeouts should also park (currently only researcher/engineer park).

### DEC-013 — FE-003: foreground re-sync via heartbeat liveness + forced open-session sync (2026-09-08)
- **Decision:** The web app re-syncs on mobile foreground with two client-only changes in `packages/app`:
  (1) `server-sdk.tsx` tracks the last SSE event time and, on `visibilitychange`→visible / `pageshow`
  (persisted), restarts the event stream **only if it has been silent > 20 s** (both v1/v2 streams emit
  `server.heartbeat` every 10 s, so a healthy stream is never that quiet); a restarted stream re-emits
  `server.connected`, which drives the existing connected-time refresh (session lists, statuses,
  bootstrap). (2) `directory-layout.tsx` force-syncs the open session on foreground
  (`session.sync(id, {force:true})`), the same merge-safe path the tab switch already uses.
- **Rationale:** SSE has no replay; events emitted while the phone is suspended are lost, and nothing
  re-fetches the open session's messages until a tab switch remounts the session page. This closes the
  gap exactly at the point the user hit it, reusing tested existing APIs (`sync`, `server.connected`
  refresh) instead of adding server-side buffering or push.
- **Alternatives rejected:** service-worker/push buffering (large server+client change, iOS SW limits);
  unconditional stream restart on every foreground (needlessly churns healthy desktop tabs);
  freshness-gated session re-fetch (the bounded one-request re-fetch matches tab-switch semantics and is
  simpler; a gate can be added later if it proves wasteful).
- **Consequences / revisit when:** one bounded message-page re-fetch per foreground; desktop unaffected
  while the stream is healthy. If foreground churn ever becomes noticeable, add a freshness gate on the
  session re-fetch. iOS field test pending (FU-022/FU-020).

### DEC-012 — Cycle flow refined: sub-cycles for half-done work, no park-on-timeout (2026-09-08)
- **Decision:** Replace "timeout → park run for product" with a continuous flow (user spec):
  - An engineer task that does NOT finish within its budget is recorded **"half"** (its worktree, task
    branch and opencode session are preserved) and the cycle continues with the next task.
  - Before the next main cycle, the marathon runs a **small cycle `N.1`** (then `N.2`…) that processes
    ONLY the half-done tasks of cycle N (resuming their original sessions via the knowledge bridge), then
    QA/review/ship for the completed delta.
  - Tasks never started roll forward to the next **main** cycle (`N+1`).
  - Engineer workload per cycle is **"as much as one engineer can do"** — bounded by a per-cycle time
    budget (`engineer.cycle_time_secs`, default 12h), not a fixed task count.
- **Rationale:** a hard park turns transient slowness into a stop-the-world decision; flowing half-done
  work into small cycles keeps progress monotonic and lets the product only manage boundary decisions,
  matching how a human dev would hand over a WIP. Sub-cycles reuse the same session/context for continuity.
- **Alternatives rejected:** keep parking (staleness, manual churn); merge half-done work into the next
  main cycle's tasks (mixes WIP with new scope, loses the "small cycle" clarity).
- **Consequences / revisit when:** `--cycle` is now a string ("3", "3.1"); `workers-<base_cycle>.jsonl`
  statuses are done/half; sub-cycles skip assembler+researcher; `assembler` failure still stops the run
  (no plan ⇒ cannot proceed). `_park_cycle` removed. Active only from a new marathon spawn.

### DEC-014 — FE-004: mobile folder explorer via @pierre/trees in the open-project dialog (2026-09-08)
- **Decision:** Use `DialogSelectDirectoryV2` (built on **@pierre/trees** web component, already a
  dependency / used on desktop) on **every** platform, not just desktop: `directory-picker.tsx` now gates
  only on `newLayoutDesigns()`. The tree **starts at the last opened project's folder**
  (`projects.forServer(key).last()`), falls back to server dir / home. Plain tapping the highlighted row
  **unhighlights it** via a capture-phase click on the tree container reading the row's `data-item-path`
  and calling `item.deselect()` — the lib otherwise only toggles selection on Ctrl/⌘-click (absent on touch).
  A ≤680px media query makes the fixed 640×480 dialog full-viewport so it fits a phone.
- **Rationale:** gives phones the Windows-style folder explorer (drill down by tap, highlight →
  "Select folder" opens it, else the current folder = existing `pickerMode.result`) with zero new deps;
  the v1 search-list dialog was the painful part on mobile. Component research confirmed @pierre/trees as
  the purpose-built file-tree (virtualization, lazy load, selection) vs generic SolidJS trees.
- **Alternatives rejected:** switching to generic SolidJS tree libs (solidjs-treeview-component, Zag,
  kobalte, shadcn-tree) — none are drop-in file explorers with server-side lazy listing; building a custom
  drill-down from scratch — duplicating @pierre/trees features.
- **Consequences / revisit when:** v1 search-list dialog becomes dead code if we ever drop the legacy
  layout. The capture-phase click intercept relies on the row `data-item-path` attribute — re-verify on
  @pierre/trees major updates. iPhone field test pending (FU-023).

### DEC-015 — FE-005: iOS completion notifications via Web Push, server-initiated (2026-09-09)
- **Decision:** Deliver "session finished" notifications to iOS through **Web Push (RFC 8030/8291, VAPID)**
  driven by the opencode server, not by any client polling. Server (s008): new `Push` LayerNode
  (`packages/opencode/src/push/push.ts`) that generates/persists VAPID keys under `Global.Path.state/push/`,
  stores per-origin push subscriptions in `subscriptions.json`, and on each `session.status idle` event
  sends `{title, body, url}` (deep link `/<base64url-dir>/session/<id>`) via the `web-push` lib, skipping
  child (sub-agent) sessions. Raw auth-gated HTTP routes (`GET /api/push/pubkey`, `POST
  /api/push/subscribe|unsubscribe`) added in `src/server/push/route.ts` with the same login middleware as
  the login page. Client (s009): `public/sw.js` handles `push`→`showNotification` + `notificationclick`→
  focus/open the session URL; `src/utils/web-push.ts` guards secure-context support, subscribes with the
  VAPID pubkey and unsubscribes on toggle-off; settings toggle "Background notifications"
  (`NotificationSettings.webPush`) in the general→Notifications section; `/sw.js` registers at app boot.
- **Rationale:** iOS suspends background tabs so no client-side mechanism can wake to notify; only a
  server-initiated push can. The session `idle` state is exactly the "finished" signal the user asked for.
  Same-origin embedded deployment serves `/sw.js` and the push API from the same origin the app runs on
  (login-page flow), so cookies/secure context line up.
- **iOS constraints (from s008 WebKit source check):** origin must be a secure context (HTTPS; LAN IP is
  not); the page must be added to the Home Screen once (iOS 16.4+); the permission prompt must be in a user
  gesture (satisfied by the settings toggle); SW must not network-loop on iOS (design is server-push, so ok).
- **Alternatives rejected:** client background polling (impossible on iOS), third-party push service
  (VAPID is self-hosted and sufficient), firing on any event rather than the explicit idle state (would
  annoy the user).
- **Consequences / revisit when:** requires an HTTPS origin in practice (FU-020/FU-025). SW cache-control on the
  real origin may need no-cache to avoid stale SW on updates. Service-worker copy is intentionally not i18n'd
  (outside React; notifications are short and system-styled).
- **Follow-up (s009):** `disableLogger` reverted to `true` before commit — the running fork binary keeps the
  default (request logs off); only debug restarts add `--print-logs --log-level DEBUG`.

### DEC-016 — Build toolchain pin + raw-router service resolution (2026-09-09)
- **Decision A (build toolchain):** `scripts/build-linux.sh` now downloads and uses **`bun@1.3.14`**
  (the version pinned by the repo's `packageManager`) into `~/.cache/opencode-build/bun-1.3.14` rather than
  relying on whatever `bun` is on PATH. Root cause found when every location-scoped v2 endpoint
  (`/api/reference`, `/api/agent`, `/api/model`, `/api/fs/list`, ...) returned 500 with
  `TypeError: undefined is not an object (evaluating 'a.name')` in the effect app-node
  `resolve`/`recur` compile path — reproduced on a **pristine upstream `ecbc6cc`** build, while running the
  server **from source** worked. Local bun 1.4.2's compiler embeds a broken schema/layer-node graph; bun
  1.3.14 compiles clean. Context: `packages/opencode/script/build.ts` uses `minify:true` + `compile` into a
  single binary; a `NO_MINIFY` experiment did NOT help (not a minification bug), the bun version did.
- **Decision B (raw HttpRouter service access):** in `packages/opencode/src/server/push/route.ts`, resolve
  `Push.Service` once at **router-construction** time (inside `HttpRouter.use`'s `Effect.gen`) and capture it
  into the handler closures, instead of `yield* Push.Service` inside request-time handler effects. Request-time
  raw-handler effects have no service environment, so every authenticated call to `/api/push/pubkey`,
  `/api/push/subscribe`, `/api/push/unsubscribe` failed with `500 Service not found: @opencode/Push`. This
  matches the working login/SPA routes (`server.ts` `uiRoute`), which also resolve services at build time.
- **Rationale:** upstream CI builds with the pinned bun; reproducing the toolchain in our build script keeps
  our binaries identical-by-construction. Raw `HttpRouter` handlers are plain request → response functions with
  no `Context` environment, unlike `HttpApi` handlers which get services inserted by `HttpApiBuilder`.
- **Consequences / lessons:** (1) Always test authenticated endpoints for a new API surface, not just the
  auth gate (the 401-vs-500 split hid this for a full session). (2) Compile-only bugs are spliced by comparing
  source-run vs compiled-run; keep `git worktree` + pinned-toolchain rebuild in the debug checklist
  (`30-runbooks`?). (3) Health checks on this host should run with `LANG=C` — two `project-copy` assertions
  fail on the Chinese locale's git error text.

### DEC-017 — Dismiss request docks locally on a confirmed response, don't rely only on the reply SSE event (2026-09-10)
- **Decision:** In `packages/app/.../session-question-dock.tsx`, on a **successful** `question.reply` /
  `question.reject` mutation, splice the answered request out of the shared store
  (`sync().set("question", request.sessionID, splice-out request.id)`) so the dock dismisses immediately.
  The splice mirrors the existing SSE-event handlers (`context/global-sync/event-reducer.ts:454`,
  `context/server-session.ts:1280`); the local clear just makes it independent of SSE.
- **Rationale:** the dock was dismissed **only** by the `question.v2.replied`/`.rejected` SSE event. When that
  event is lost — quick-tunnel SSE buffering (known since s010), mobile background suspension killing the
  stream, or any transient stream drop — the reply succeeds server-side (HTTP 200) but the store never
  clears, so the dock stays open forever. Clearing on `onSuccess` (which fires only after the API call
  resolved) is race-free and matches the server state; `onError` intentionally does NOT clear so the dock
  stays open to retry.
- **Consequences / revisit when:** `SessionPermissionDock` (session-composer-state.ts `decide`) has the
  **identical** latent bug (dismisses only on the `permission.replied` SSE event) — see FU-027; apply the
  same local-clear-on-success there if it reproduces. This is the same fix *class* as the s010 "Thinking row"
  watchdog (DEC-016-era): **never make a UI dismissal depend on a single fire-once SSE event with no local
  reconciliation.**

### DEC-018 — Home page split into "Projects" / "Sessions" tabs (2026-09-11, s015)

- **Context:** user wanted the `/home` landing restructured into a 2-tab view: (1) original folder
  selection + project select, (2) a table of **all project sessions gathered across all projects,
  sorted by last prompt** — WITHOUT the need to pre-select a folder each time. An earlier draft of tab 2
  listed *projects* (`HomeProjectsList`); the user clarified they want *sessions*, so it was replaced by
  a sessions table. v2 removes the folder pre-selection entirely; v3 (final) decouples the two tabs so the
  Projects tab is preserved exactly.
- **Decision:** top `SegmentedControlV2` in `pages/home.tsx`. Tab "Sessions" (default) renders
  `HomeSessionsTable`; tab "Projects" renders the original home grid unchanged. Reused existing i18n
  keys (`home.projects`, `home.sessions.search.sessions`) — no new keys, so the 66-locale parity test
  is untouched. **v3:** the Sessions tab uses a DEDICATED `createHomeSessionsTableController`
  (`home-sessions-table-controller.tsx`) with its own query (`loadHomeSessionIndex`, all projects'
  worktrees+sandboxes), its own `records` build, its own `open`/`isOpenTab`/`server`. The original
  `createHomeSessionsController` is left UNCHANGED (project-scoped `projectDirectories`,
  `showProjectName = !selected`) and drives only the Projects tab. `HomeSessionStatusController` +
  `SessionTabAvatarView` are stateless presentational/status pieces over the global avatar store, shared
  by rows everywhere without affecting tab logic. Sorted by `session.time.updated ?? time.created`
  descending; unread dot + bold when unread; session title (last prompt) from `session.title`. Row click =
  the table controller's `open(...)` which resolves the project from `session.directory` and calls
  `ctx.projects.open(directory)` — folder auto-selected per session.
- **Rationale:** tab 1 preserves the folder-based flow for users who want it. Defaulting to the
  cross-folder Sessions list removes the friction of always picking a folder the user never uses.
  A separate controller per tab guarantees changes to one never leak into the other (the user hit this
  leakage in v2 when mutating the shared controller changed the Projects sidebar). Reuses already-loaded
  home-session records — no new persistence or per-session message sync needed.
  Deriving "last prompt" from `session.title` avoids loading every session's messages.
- **Consequences / revisit when:** if an exact raw last-user-message line is wanted, add per-session
  message sync (FU-029). Visual check on iPhone pending (FU-028). If the two tabs feel redundant with the
  sidebar, consider merging them and/or adding sort controls.

### DEC-019 — Sidebar last-prompt subtitle via the client message store (2026-09-12, s016)

- **Context:** FE-006 — user wants each session in the workspace sidebar to show the **last prompt I
  sent** under the session title. Options: (a) persist a `lastPrompt` field server-side on `Session`
  (schema + DB + Server HttpApi + SDK regen), (b) derive it client-side from the in-app message store.
- **Decision:** **(b) client-only.** New util `sessionLastPrompt(sync, sessionID)`: walk
  `serverSync().session.data.message[sessionID]` newest-first, take the newest **user** message whose
  `part[sessionID][message.id]` contains a real text part (`type === "text"`, not `synthetic`, not
  `ignored`) — same convention as `components/dialog-fork.tsx` — and return its text with whitespace
  normalized to single spaces. `SessionRow` renders it as a `text-13-regular` subtitle (hidden for
  `dense` rows); the row tooltip shows `title\nprompt`. Pure additive — no persistence, no API change.
- **Rationale:** the existing session **prefetch** path (layout.tsx `prefetchSession` →
  `shouldPrefetch`) already populates `data.message`/`data.part` for listed sessions, so the text is
  available at render time for near-zero cost and stays reactive (subtitle appears as messages load).
  Scaffolding a server field (option a) is heavier and touches generated code and DB migrations on a
  vendored fork for unchanged visual value.
- **Consequences / revisit when:** cold sessions show the subtitle only once prefetched (acceptable —
  brief blank state). Dense overlay rows intentionally skip the subtitle. **Revisit:** if the home
  **Sessions tab** should also show the exact raw prompt instead of the `session.title` proxy (DEC-018;
  FU-029 / FU-031), the same `sessionLastPrompt` technique applies there; a server-side field becomes
  worthwhile only if many sessions need prompt text without prefetch.
  - **Update (s016, same day):** to cover EVERY listed session (not just hover/neighbors), the prefetch
    queue was widened — items now carry `{ id, limit, keep }`, and a bulk effect on `currentSessions()`
    enqueues all visible sessions at `previewLimit = 20` messages each and per-dir cap 25; the eviction
    keep-count follows each item so preview data isn't swept after fetch; hover still upgrades to 200.
    Cost: up to N small fetches on open (2 concurrent) — accepted by user explicitly ("async ajax / call
    API").

### DEC-020 — Home Sessions-tab row: mobile-first multi-line card instead of a single-line strip (2026-09-12, s018)

- **Context:** FE-007 — the starting (home) **Sessions** tab's session row was a one-line horizontal
  flex with 4 columns: `[avatar] [project w-28 sm:w-40] [title + last-prompt (both truncate)] [time w-16]`.
  On a ~360px phone the fixed project column (112–160px) ate ~half the width, starving the title, and
  every text field was single-line truncated so long prompts vanished entirely.
- **Decision:** redesign the row as a **3-line stacked mobile card** (client-only, markup change in
  `home-sessions-table.tsx`): (1) **title** is `flex-1` clamped to **2 lines** via inline
  `-webkit-line-clamp:2` / `-webkit-box-orient:vertical` (the pattern the question dock already uses);
  (2) **relative time** moves to the **top-right**, top-aligned with the title (no reserved 64px next to
  the text); (3) **project name** drops out of the fixed-width column — it becomes a small muted line
  under the title with the v2 **folder** icon, single-line truncate; (4) the **FE-006 last-prompt
  preview** becomes a third line, also clamped to **2 lines**, only when present. Row container switched
  `items-center` → `items-start`, avatar top-aligned.
- **Rationale:** on phones a linear "table" with a fixed meta column is unreadable — every pixel of
  horizontal space should go to the content text, and meta (project/time) should either float top-right
  (time, doesn't wrap) or stack as a secondary line (project). Multi-line clamps keep the list scannable
  without expanding rows unboundedly; 2 lines covers virtually all real titles/prompts at phone widths.
- **Consequences / revisit when:** rows are vertically taller (3 lines max ≈ title 2 + project 1 + prompt
  2); dense lists show fewer rows per viewport but each is far more informative. No controller/schema/API
  change — pure markup; verified by typecheck + oxlint + 737 unit tests and built with the pinned bun
  1.3.14 (DEC-016). **Revisit:** if a future compact list view is wanted (e.g. many rows scrolling fast),
  add a CSS density toggle rather than reintroducing the fixed project column.

### DEC-021 — p003 fork: `visual_model` config key for image-message fallback (2026-09-12, s023)
- **Decision:** add a top-level `visual_model` config key (`provider/model`, mirrors `small_model`)
  to the p003 opencode fork. At each turn (`session/prompt.ts` per-turn `getModel` interception), if
  the active model's `capabilities.input.image === false` and the **last user message** carries a
  `file` part with an `image/*` mime or `data:image/` url, substitute `provider.getVisualModel()`
  for that turn only. The assistant message's stored `providerID/modelID` and the LLM processor use
  the visual model; the session's stored default model is never mutated.
- **Rationale:** Hermes-class models declare no vision (`attachment:false`,
  `modalities.input:["text"]`); a global fallback key lets users keep the cheap model as default
  while still answering image prompts. Substitution at the per-turn model site (prompt.ts ~L1141)
  is the single clean interception point; `getVisualModel` mirrors `getSmallModel` (config → parse →
  `getModel`, `undefined` when `visual_model === cfg.model` or the model doesn't exist — silent no-op).
- **Key facts:**
  - `config/v1/config/migrate.ts` `keys` set deliberately NOT extended — `visual_model` never existed
    in legacy V1 files, and adding it would misdetect modern configs and drop the key during `migrate()`.
  - Client capability mapping already exposes `capabilities.input.image` (global-sync/utils.ts).
- **Verified:** typecheck clean (core + opencode); end-to-end on the fork over HTTP —
  image message + `dgx/general` → `dgx-vision/vision-model-default`; text-only follow-up → stays
  `dgx/general`; session model untouched. Config lives in global `~/.config/opencode/opencode.jsonc`.
- **Revisit when:** supporting non-last-user historical image context (a text follow-up referencing an
  earlier image still routes to the non-vision model — current scope is "image-bearing turns" only).

### DEC-022 — Dialog/DialogV2 shells render only when open (2026-09-13)
- **Decision:** in the p003 opencode fork, gate the shell divs of both `Dialog` components —
  `packages/ui/src/v2/components/dialog-v2.tsx` and legacy `packages/ui/src/components/dialog.tsx` —
  on `useDialogContext().isOpen()` via `<Show when={...}>`. Closed dialogs no longer emit the
  `fixed inset-0` container + centered `dialog-container` box into the DOM.
- **Rationale:** the shells rendered unconditionally; only the inner `Kobalte.Content` was gated
  by the Root's open state. The per-tab close-tab confirm dialog (`titlebar-tab-nav.tsx:394`,
  mounted under `data-titlebar-tab-slot`) therefore always displayed an empty opaque centered box
  (z-50, `pointer-events:auto`) after login, blocking the middle of the view. Playwright
  `elementFromPoint` at screen-center returned the empty container — proof it was the blocker.
  Gating on the context's `isOpen` (Kobalte 0.13.11) is available in every current usage (local
  `Root` and portal DialogContext), and `isOpen` stays true through the closing transition so the
  exit animation is preserved.
- **Alternatives rejected:** app-level `Show when={confirmCloseOpen()}` around just the close-tab
  dialog — would fix the reported case but leave the same latent bug in the shared
  Dialog components for any future always-mounted dialog.
- **Consequences / revisit when:** while closed, `[data-component="dialog-v2"]` / `"dialog"` no
  longer exist in the DOM; code must not depend on their presence when closed. No transitions
  affected (Kobalte keeps `isOpen=true` while animating out). The `useDialogContext` hook throws
   if used outside a Kobalte Root — all current `Dialog` usages are inside one.

### DEC-023 — p003 fork keeps its own SQLite, separate from official main (2026-09-14, s030)
- **Decision:** declined a request to make the current dev version read the same sqlite file
  (`opencode.db`) as the official main opencode build. The fork continues to use its own channel-suffixed
  DB (`opencode-mark-dev.db`). No code or build change was made.
- **Rationale:** the separate-channel DB is a deliberate design decision, recorded directly in the
  build script (`p003-opencode-fork/scripts/build-linux.sh`: "Pin a distinctive channel so this fork
  never shares SQLite state with another opencode build on the same machine"). Two live processes
  (`:4447` dev fork, `:4445` official main) both running against one WAL SQLite file risks locking
  conflicts and cross-build schema-migration issues. The user explicitly chose to stop and change nothing.
- **Alternatives rejected (if revisited):** (a) code fix `database.ts:path()` to add the fork channel to
  the ["latest","beta","prod"] set → resolves to `opencode.db`; (b) build fix, set `OPENCODE_CHANNEL=latest`
  in the fork build → naturally drops the suffix.
- **Consequences / revisit when:** the fork and official builds keep isolated session/account/event data.
  If the user later insists on sharing, revisit with both processes stopped (single writer) and confirm
  whether the fork's existing `opencode-mark-dev.db` data should be merged or discarded.

### DEC-024 — Serper key: self-loaded by the skill script, not read from opencode.jsonc (2026-09-14, s031)
- **Decision:** the `web-research` Serper fallback resolves its API key **by env var first, then by
  reading `SERPER_API_KEY="…"` out of `~/.bashrc`/`~/.profile`**. `serper.py` gained a
  `_load_key_from_bashrc()` + `_get_key()` fallback so the script works from the agent's
  **non-interactive** bash tool. The key export was also moved **above** the interactive-only
  `return` guard in `~/.bashrc` (line 6-9) so non-interactive shells inherit it too.
- **Rationale:** the user asked for "a default skill that reads the key from `opencode.jsonc`".
  That is **not possible**: `opencode.jsonc` only injects provider `options.apiKey` values into the
  LLM runtime; it does NOT expose arbitrary config values to bash/skill scripts. The only supported
  channel for a skill script to get a secret is an **environment variable**. The key was already in
  `~/.bashrc:137` but *after* the interactive guard (`case $- in *i*)…*) return;;`), so the agent's
  non-interactive bash tool never saw it → Serper failed with "env var not set" even though it worked
  in the user's terminal. Fix keeps a single source of truth (`~/.bashrc`) with no secret duplicated
  into the repo.
- **Alternatives rejected (if revisited):** (a) hardcode key in a `.env` inside the skill dir —
  would store a secret in the workspace (violates "no secrets in this folder"); (b) an MCP server for
  Serper — heavier than needed for a single-key search call; (c) read `opencode.jsonc` — not possible
  (see rationale).
- **Consequences / revisit when:** `SERPER_API_KEY` in env always wins over the `~/.bashrc` parse.
  The `~/.bashrc` parse is best-effort and regex-matched (first `SERPER_API_KEY=` line). If the key
  moves to a different dotfile or a different var name, update `_load_key_from_bashrc()`. SKILL.md
  now documents the two-step resolution so a successor agent doesn't re-diagnose the "key not set" error.

### DEC-025 — web-research promoted to a GLOBAL skill with aggressive real-data-first triggering (2026-09-14, s031)
- **Decision:** `web-research` now lives in the **global** skill dir
  `~/.config/opencode/skills/web-research/` (SKILL.md + storage/serper.py), so it loads in **every**
  opencode project, not just this one. The `SKILL.md` `description` was rewritten to be
  **proactive and trigger-heavy**: it instructs the LLM to search by default for ANY question needing
  real/current/external data (versions, prices, "latest", dates, install commands, API/library usage,
  debugging, comparisons, who/what/when/where facts) and to **not** answer from stale memory.
  Trigger keywords enumerated: search, look up, find out, research, check, verify, what is, latest,
  current, how to, install, compare, release, docs, etc.
- **Rationale:** the user wants the LLM to **always get real data** because its training is stale and
  it should "get real data regardless of its knowledge". Skills are only triggered when the LLM
  matches the `description` against the request, so the description is the lever — it must be loud,
  keyword-rich, and instruct default-on behavior. Serper stays primary (self-loads the key, see
  DEC-024); SearXNG demoted to an optional self-hosted fallback.
- **Alternatives rejected (if revisited):** (a) keep it workspace-only (`ide` only) — would not
  satisfy "default for everything"; (b) a dedicated `serper-search` skill — redundant, folded into the
  rewritten `web-research`; (c) an MCP server — heavier than needed; (d) a forced slash command —
  would bypass LLM judgment, but the user asked for the LLM to *know* when to use it, so a skill is
  the right primitive.
- **Consequences / revisit when:** every project's `.opencode/skills/web-research/` (e.g. this one,
  and `gdx`'s) is now **redundant** — the global copy is authoritative. If a project needs a custom
  variant, the local one overrides the global for that project. The aggressive description may
  over-trigger on trivial codebase questions; the "Do NOT trigger" carve-out (pure codebase / pure
  math) is the guard. Revisit if the LLM searches too eagerly on internal-only questions.

### DEC-026 — opencode auto-creates `~/.config/opencode` (base) but NOT the `skills/` subdir (2026-09-14, s031)
- **Decision / fact:** on every opencode start, the **base config dir** `~/.config/opencode` (plus
  data/state/tmp/log/bin/repos under `~/.local/share/opencode`, `~/.cache/opencode`,
  `~/.state/opencode`) is created automatically. The **`skills/` subdir is NOT** auto-created — opencode
  only *scans* for skills and silently ignores a missing directory.
- **Rationale (source, p003 fork, `packages/core/src`):**
  - `global.ts:35-43` — boot runs `fs.mkdir(Path.config, { recursive: true })` (and the other base
    dirs) on module load. `Path.config = path.join(xdgConfig, "opencode")` (`global.ts:13`).
  - `config/plugin/skill.ts:23-33` — for each configured directory it registers a **directory source**
    at `<dir>/skill` and `<dir>/skills` (note the singular + plural). These are *scan targets*, not
    mkdir targets.
  - `skill.ts:78-80` — the loader does `fs.glob("{*.md,**/SKILL.md}", { cwd: directory … })` piped to
    `.pipe(Effect.catch(() => Effect.succeed([])))` → **missing dir = empty list, no creation**.
- **Consequences:** the `~/.config/opencode/skills/` dir I created (s031) was made by **my `mkdir -p`**,
  not by opencode. It will persist, but if it were deleted, the next run would **not** recreate it —
  the global `web-research` skill would just be absent until the dir + files are re-added. The base
  `~/.config/opencode/` dir, by contrast, is self-healing (recreated each start). Also note opencode
  scans **both** `skill/` and `skills/` under every configured dir (and `opencode.jsonc` `skills:[]`
  can add URL or `~/…` sources), so the global location could equally be `~/.config/opencode/skill/`.

### DEC-027 — "kickoff" pre-install plugin auto-creates global skills dir + seeds a starter skill (2026-09-14, s032)
- **Decision:** added `~/.config/opencode/plugin/kickoff.ts`, an **opencode plugin** that runs on
  **every opencode start** (auto-loaded by the external-plugin loader, no fork rebuild). On boot it:
  (1) `mkdir -p ~/.config/opencode/skills/` (opencode scans but never creates it — DEC-026, so this
  makes the global skill location **self-healing**); (2) seeds
  `~/.config/opencode/skills/starter-kit/SKILL.md` if absent — a "make opencode useful out of the box"
  onboarding skill (real-data-first web research, repo orientation, safe defaults, verify); (3)
  promotes the `web-research` skill (serper.py + SKILL.md) into the global dir if a source copy exists
  on this machine and the global copy is missing. All steps **idempotent + best-effort** (never throws,
  never overwrites user files, degrades silently).
- **Rationale (source, p003 fork):** the cleanest user-space "on kickoff" hook is the **external
  plugin** loader — `packages/opencode/src/plugin/loader.ts` + `index.ts`. It globs
  `<config-dir>/{plugin,plugins}/*.{ts,js}` (`config/plugin/external.ts:58-70`) and, for the v1
  runtime, decodes `export default` a **function** (`index.ts:88-90` `isServerPlugin =
  typeof value === "function"`), called as `server(input, options)` whose return becomes the plugin's
  hooks (`index.ts:123`). `input = { client, project, directory, worktree, $, serverUrl }`
  (`packages/plugin/src/index.ts:56-66`). So a function that does its seeding and `return {}` is the
  correct, supported shape. Chose a plugin over: (a) editing the fork to add an embedded skill —
  requires a rebuild and touches shared code; (b) a bashrc hook — fragile, not opencode-owned; (c) a
  plain global skill file — works but doesn't self-heal the missing `skills/` dir (DEC-026).
- **Alternatives rejected (if revisited):** (a) an **embedded** skill in the fork
  (`packages/core/src/plugin/skill.ts:13-31`, the `customize-opencode` pattern) — most "built-in" but
  needs a fork rebuild + re-deploy and is machine-specific content in shared source; (b) a `bun`
  plugin via `opencode.jsonc` `plugins:["file://…"]` — equivalent but more moving parts than a file in
  the auto-scanned dir; (c) keep the starter skill as a plain file — fine, but then the `skills/` dir
  still isn't auto-created.
- **Consequences / revisit when:** `starter-kit` is now a **global default skill in every project**.
  It is seeded (not overridden) — delete `~/.config/opencode/skills/starter-kit/` to remove the skill
  (the plugin will re-create it on next start unless you also delete the plugin). Delete the plugin
  with `rm ~/.config/opencode/plugin/kickoff.ts`. **Verified live**: a fresh `opencode serve` (1.18.23)
  loaded it and `/skill` returned `customize-opencode`, `web-research`, **and** `starter-kit` — so the
  real loader picks up `~/.config/opencode/plugin/*.ts` and the seeded skill is registered. The
  production :4447 fork will pick it up on its next (re)start; no change made to the running process.


### DEC-028 — Replace `@pierre/trees` web-component picker with Zag.js TreeView (2026-09-14, s029)
- **Decision:** swapped the folder/project picker's visual browse tree in the p003 fork web UI from the
  `@pierre/trees` **web-component `FileTree`** (beta `1.0.0-beta.4`, shadow-DOM + imperative
  `getItem/expand/select`) to **Zag.js TreeView** (`@zag-js/solid` + `@zag-js/tree-view` 1.43.3) in
  `packages/app/src/components/directory-tree-zag.tsx`. Kept the existing path text-input, autocomplete
  suggestions, and the domain-layer mid-level reveal logic in `dialog-select-directory-v2.tsx`.
- **Rationale:** the web app is **SolidJS**; the `@pierre/trees` beta widget was the fragile/buggy
  surface (shadow-root scroll hack, `unsafeCSS`, trailing-slash `getItem` path lookups). Zag is
  **Solid-native, framework-agnostic** (chakra-ui / Ark-backed, actively maintained), has native
  **lazy `loadChildren`** (matches backend `file.list`), WAI-ARIA keyboard nav, programmatic
  `expand`/`select` (for the mid-level reveal e.g. `C:\infrasys\java\jre\`), and renders plain DOM
  with `data-state`/`aria-selected` CSS hooks. peerDependency `solid-js >=1.1.3` is compatible with the
  app's solid 1.9.10. Decision recorded (location): `40-knowledge/directory-picker-lib-options.md`.
- **Alternatives rejected (if revisited):** React-only trees (react-arborist, react-d3-tree,
  react-sortable-tree) — not usable in a Solid tree; browser-native `showDirectoryPicker()` — requires a
  secure context, unavailable on the HTTP :4447 LAN URL, and can't browse the **server** filesystem the
  agent works in.
- **Consequences / revisit when:** the picker renders a lazy Zag tree (no shadow DOM). If the mid-level
  reveal or expansion UX feels off in the field, revisit the `reveal()` reveal-timing/synchronization or
  add virtualization via `getVisibleNodes()` + `@tanstack/solid-virtual`. On-device retest pending (FU-047).

### DEC-029 — New-folder project selection must bootstrap the directory server-side (2026-09-14, s033)
- **Decision:** `createPromptProjectControls` in the p003 fork web UI (`session-composer-controls.ts`)
  now calls a `bootstrapProject(target, worktree)` helper from `selectProject`/`addProject` when a
  **brand-new folder** is picked as the project: if the folder has no files, `project.initGit({directory})`
  is called; then `sync.child(directory, {bootstrap:false})[1]("project", project.id)` seeds the
  directory as a real server project scope. Mirrors the reference Home path (`home-controller.ts:89-109`).
- **Rationale:** before the fix, the draft path only did client-side `projects.open/touch` +
  `tabs.updateDraft`. Server-side `Project.resolve` (`core/src/project.ts:110-122`) falls back to the
  **global project** when the directory has no git repo, so a session created for a fresh folder was
  scoped to the global project while the client subscribed to the directory child store → streamed
  parts were orphaned (server-session orphan gate) and the prompt appeared to never reach the LLM.
  Initializing the folder makes `git.repo.discover` succeed so the project resolves to its own scope.
- **Alternatives rejected:** pre-scanning/registering every picked directory unconditionally (wasteful
  for already-registered projects); touching the server API surface (no change needed — `initGit` +
  `project.current` + child seeding already exist).
- **Consequences / revisit when:** the bootstrap is fire-and-forget (non-blocking) so rapid use of a
  brand-new folder + immediate submit could still race; if it ever shows up in the field, await the
  bootstrap promise (or sequence `tabs.updateDraft` after it) in `selectProject`'s draft branch. Retest
  pending (FU-046).

### DEC-030 — On an up-walk, an unreadable parent is "no config there", not a server error (2026-09-14, s034)
- **Decision:** `FSUtil.up` (`packages/core/src/fs-util.ts`) now probes each candidate with
  `existsSafe` (any error ⇒ `false`) instead of raw `fs.exists`. During config/git/location discovery
  the walk ascends from the routed directory up to the stop dir probing `.git`, `.opencode`,
  `opencode.json`, `opencode.jsonc`. When the server user cannot traverse a parent (root-owned
  `drwx------` dirs like `/root` or `/lost+found`), `fs.exists` yields `PlatformError: PermissionDenied`
  which, crossing a `.orDie` in config load, became a **die** → every routed endpoint
  (`/file`, `/config`, `/session`, `/event`) returned 500 with a masked ref.
- **Rationale:** the folder picker legitimately browses to the filesystem root and lists root-owned
  dirs; selecting/expanding one must not cripple the whole routed request. `existsSafe` treats a
  permission-denied stat exactly like a missing path — the safest fallback for discovery probes,
  and it matches the pre-existing intent (the same `existsSafe` is already used for home-dir probing).
- **Alternatives rejected:** catching the die at `config` load only (fixes only one of the many
  up-walk callers: `Project.resolve`/git discovery run the same walk); widening `file.list`'s
  kill-switch fallback (the 500 wasn't `/file`-specific); surfacing 403 to the UI (breaks the picker's
  browse-root UX and adds an error channel for a non-actionable condition).
- **Consequences / revisit when:** unreadable dirs now render as **empty folders** in the picker
  rather than 500ing. Also added `Project.resolve` `Effect.catchCause` around `git.repo.discover` as
  defense-in-depth (degrades to global project on any discover failure). No behavior change for
  readable dirs. If a user genuinely needs to *select* `root`/`lost+found` as their project the empty
  listing is still acceptable UX and server-side operations for it will surface real permission errors
  where they matter (file writes), not in listing.

### DEC-031 — FE-003 gap: decision dock (question store) re-synced on foreground (2026-09-16, s039)
- **Decision:** the foreground re-sync (DEC-013) only force-synced session **messages**; the question
  store (`data.question`, which drives `SessionQuestionDock`) is mutated only by live SSE event handlers
  (`question.asked/replied/rejected`) or a full bootstrap (runs only on fresh `server.connected`). So a
  question asked while backgrounded stayed invisible after unlock if the stream never restarted. Fix:
  `directory-sync.ts` gains `session.syncQuestions(sessionID)` — v1: `serverSDK.client.question.list()`;
  v2: `serverSDK.api.question.request.list({ location: { directory } })` — filtered to the session via new
  pure helper `sessionPendingQuestions` and written back with the same merge-safe
  `set("question", sessionID, reconcile(...))` path the tab switch / bootstrap use (stale entries dropped).
  `directory-layout.tsx` foreground handler now calls it alongside the existing force-sync.
- **Rationale:** the stream-restart guard (>20 s silence) is exactly right for chat, but a "healthy" stream
  is precisely the case where the message list stays current and the question dock does not — the two
  refresh on different stores. Fetching pending questions from server state is idempotent and small.
- **Alternatives rejected:** extending the SSE restart to always fire on foreground (needlessly churns the
  stream, and a restarted stream does not replay missed `question.asked` anyway); server-side buffering/push.
- **Consequences / revisit when:** decision dock self-heals on return to foreground. Deploy + on-device
  retest pending (FU-050).

### DEC-032 — Skills management: marker-file rename for enable/disable; manage via v2.skill API (2026-09-17, s049)
- **Decision:** web-UI "Skills" tab manages skills through the existing `v2.skill` HTTP surface
  (`GET /api/skill` + new `POST /api/skill/:name`, `POST /api/skill/:name/enabled`,
  `DELETE /api/skill/:name`), backed by `SkillV2` (core) service operating on disk. A skill is
  **disabled** by renaming its `<dir>/SKILL.md` to `<dir>/.SKILL.md.disabled` (and back on enable) —
  the discovery glob `**/SKILL.md` skips it, so it stops being offered to agents, yet still appears in
  the management list (now with `enabled:false`) for re-enabling. `SkillV2.Info` gained `enabled?`.
- **Rationale:** the marker-rename matches the confirmed user preference, needs no new config-runtime
  state, and is reversible at the filesystem level. Building on `v2.skill` (the surface the web app's
  SDK already calls) avoids wiring an entire second skill system.
- **Alternatives rejected:** a local (UI-only) opt-out store (would not affect agent discovery);
  permission-rule based toggling (semantic mismatch — permissions gate *use*, not *availability*);
  using the agent's `@/skill` discovery service (different instance-disk lifecycle; much larger blast
  radius, and not what `/api/skill` exposes).
- **Consequences / scope caveat:** the tab manages the **SkillV2 directory-source set only**
  (`.opencode/skills` + configured skills dirs) — NOT `.claude/skills` or per-project SKILL.md
  discovery, which live in the agent-level `@/skill` system. If the user later wants those too, a
  second management surface (instance skill group) is required.

### DEC-033 — Re-scope: Skills tab stays view+edit ONLY; revert "merge other agent systems read-only" (2026-09-17, s049)
- **Decision:** the exploratory "merge all agent-skill discovery into `/api/skill` as read-only extra
  rows (hide edit/delete icons, `editable:false`) on the Skills tab" was **reverted**. The tab keeps its
  original scope from DEC-032: list + edit + copy + enable/disable + delete, over the SkillV2
  directory-source set.
- **Rationale:** the user clarified the feature intent is **view + edit `SKILL.md` only**. The merge
  pulled in schema (`RecordSource` + `Info.editable`), core (`mergeReadonly`, read-only guards),
  server wiring (`skillDiscoveryMergeLayer`, `Layer.provideMerge(Skill.node)`), all uncommitted; it
  also forced an SDK/OpenAPI regeneration (the plugin-facing `SkillV2Source` union in
  `packages/sdk/js`/`types.gen.ts` must gain `record` — schema changes ripple to generated SDK types
  referenced by `packages/plugin/src/v2/effect/skill.ts`). Reverting removed that dependency entirely.
- **Alternatives rejected:** shipping the merge (scope creep, new SDK dependency, unresolved
  per-location `SkillV2.Service` scope risk in a static startup merge layer); UI-only hiding of icons
  without server read-only (would still allow writes to foreign dirs).
- **Consequences / revisit when:** nothing in the tree reflects the merge; clean working tree, no SDK
  regen needed. If the user later wants `.claude/skills` / project skills surfaced on the tab,
  revisit DEC-032's caveat with a read-only instance-level listing (re-apply merge machinery + SDK
  regen).

### DEC-034 — deploy-web-4447.sh is cwd-independent (2026-09-17, s050)
- **Decision:** the fork deploy script resolves its own absolute path **before any `cd`**, so it no
  longer breaks when invoked as `./deploy-web-4447.sh` from inside `scripts/`. The root cause was
  `readlink -f "$0"` running *after* `cd "$ROOT"`: with a relative `$0`, the link resolved against
  the new cwd and produced a wrong path (missing `scripts/`). Deploy+restart procedure is now
  documented in `30-runbooks/rb-003-echo-web-deploy-restart.md`.
- **Rationale:** script should work regardless of invocation style (relative/absolute/any cwd);
  a future agent reading RB-003 can also use the exact right command.
- **Alternatives rejected:** moving the script to a shared `ide/scripts/` (user wants no relocation —
  just the knowledge that how to deploy/restart is discoverable).
- **Consequences / revisit when:** the script lives only in `p003-opencode-fork/scripts/`; RB-003 is
  the single source of truth for how to run it. Revisit if deployment moves to a shared location.
