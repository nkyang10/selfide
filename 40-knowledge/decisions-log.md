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
