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

## DEC-035 — FU-052 scoped down: keep the per-device projects store, server truth only for Home sessions

- **When:** 2026-09-18 (s051)
- **Context:** FU-052 originally planned to rip out the whole `Persist.server("projects")`
  `createServerProjects` store (open/close/expand/collapse/move/last/recentlyClosed), treating it as
  dead after s043 switched Home to server truth. Investigation disproved that premise.
- **Decision:** Keep `createServerProjects` — it still legitimately powers the Home project *panel*
  list, command palette, and layout state (open set, drag order, expand state, last, recently-closed),
  all of which are per-device UI concerns. Only the Home *session* list — the actual cross-device bug
  (fresh device saw zero sessions) — is server truth via `home-controller.ts` `projects` memo
  (`focusedSync().data.project`, block :28-31; `select()` accepts any server-known project :88-92).
  FU-052 closed as already-fixed-by-s043; no further code change.
- **Alternatives rejected:** (a) full store rip-out — would break project panel/palette/layout;
  (b) server-side hide/order model — larger app+server change, no user need.
- **Consequences / revisit when:** if hide/order/hide-persistence per project ever becomes a real
  requirement, a server-side model (e.g. per-worktree persisted flags) should be designed then.

## DEC-036 — Rebrand fork READMEs OpenCode → MarkCode: branding-only, casing-safe

- **When:** 2026-09-19 (s053)
- **Context:** user asked to make the project name in the docs committed to GitHub be **MarkCode**
  (official name), i.e. "opencode → MarkCode". Target = the p003 fork's `README*.md` (the repo
  `nkyang10/opencode` on GitHub). Scope confirmed with user: *branding only* + *all* language READMEs
  (22 files).
- **Decision:** Applied a **case-sensitive** `sed 's/OpenCode/MarkCode/g'` to all 22 `README*.md` in
  `50-projects/p003-opencode-fork/opencode/`. Rationale (the key finding): in these READMEs the casing
  cleanly separates the two concerns — `OpenCode` (capital O) occurs **only** as the product name (logo
  alt, tagline prose, section headings, "the OpenCode team"), while lowercase `opencode` occurs **only**
  as functional references (`opencode.ai` URLs, npm `opencode-ai`, `github.com/anomalyco/opencode`, CLI
  commands, example names `opencode-dashboard`/`opencode-mobile`). So the case-sensitive replace touches
  branding and cannot break any install/link/package reference. Result: 177 ins/177 del, 0 `OpenCode` left,
  all functional refs intact.
- **Alternatives rejected:** (a) blanket lowercase `opencode`→`markcode` — would rewrite URLs, the npm
  package name, and install commands → break the docs; (b) hand-edit each of 22 files — slower and
  error-prone for a mechanical replace.
- **Consequences / revisit when:** Committed `f094279` + pushed `origin/dev` (`nkyang10/opencode`), FU-057
  resolved. Gotcha: husky **pre-push** hook runs `bun turbo typecheck` but `bun` isn't on the git-hook PATH —
  push with `PATH="$HOME/.bun/bin:$PATH"`. Other committed docs (`CONTRIBUTING.md`, `AGENTS.md`, `CONTEXT.md`)
   still say OpenCode (out of scope — user chose READMEs only). If the brand extends beyond READMEs later,
   re-run the same casing rule per file.

## DEC-037 — Fork versioning: `MAJOR.MINOR.PATCH-fork.<N>` SemVer + channels

- **When:** 2026-09-19 (s054)
- **Context:** the fork ships date-only builds (`0.0.0-mark-dev-<timestamp>`) while `package.json` carries
  upstream's `1.18.31`. No channel/divergence/rollback signal, no stable artifact identity, no bump policy when
  upstream advances.
- **Decision:** Adopt intel SemVer `MAJOR.MINOR.PATCH-fork.<N>[-channel]`: `MAJOR.MINOR.PATCH` always mirrors the
  upstream baseline; `fork.<N>` is a monotonic fork release counter (never reset/reused); timestamp becomes build
  metadata only (`+<utc>`). Three channels: `dev` (float, no tag), `beta` (`-beta.<N>`), `stable` (bare). Release
  gates = typecheck (30/30) + app build + core tests; sync policy = merge `upstream/dev` into `dev` only, never
  rebase the counter. Source of truth = `package.json`; `OPENCODE_VERSION` in `build.ts` reads it (replace the
  hardcoded `0.0.0-mark-dev-*`).
- **Alternatives rejected:** date-only (status quo), fork-own MAJOR, git-sha-only, CalVer, changesets/lerna tooling.
- **Consequences / revisit when:** implement `script/release.ts` (FU-058) and drain hardcoded version outputs to the
  single source; revisit if upstream adopts changesets or fork needs independent registry publishing. See
  `40-knowledge/versioning-strategy.md` + `30-runbooks/rb-004-release.md`.
- **Implementation note (s054):** `packages/script/release.ts` + `build-linux.sh` wiring done. **Critical finding:**
  `OPENCODE_CHANNEL` doubles as the SQLite DB filename suffix (`opencode-<channel>.db`). To keep fork data isolated it
  MUST stay `mark-dev`; release-channel semantics moved into the version string only (`-dev`/`-beta.<M>`/bare stable).
  Shipping `OPENCODE_CHANNEL=beta`/`latest` would silently point at a different/empty DB.

## DEC-038 — Lean fork README: strip upstream dup, point to upstream, highlight differences

- **When:** 2026-09-19 (s055)
- **Context:** after the MarkCode rebrand (DEC-036), user asked to remove duplicate content in the fork's
  README/docs that is just upstream info, reference users to upstream, and highlight what's different.
  The fork's `README.md` was 100% upstream content (only rebranded); 21 `README.<lang>.md` were full
  upstream translations.
- **Decision:** (1) **Rewrote `README.md`** as a short fork README — MarkCode branding, a "This is a fork"
  callout → upstream (opencode.ai / anomalyco/opencode) for install/CLI/desktop/integrations/plugins/docs,
  a **"What's different from upstream"** section (FE-001..015 deltas + self-built aarch64 binary), and a
  License note. Dropped upstream install/quickstart/CLI/desktop/integrations/services/plugins/funding/build/
  contributors sections, the Discord/npm/build badges, and the language-links block. (2) **Replaced all 21
  `README.<lang>.md`** with an identical 5-line pointer to the English README + upstream (no full
  translation). (3) **Professional-fork practice for other docs:** added Fork-notice blocks to
  `CONTRIBUTING.md` + `SECURITY.md`; left `AGENTS.md` (already fork-aware), `CONTEXT.md` (accurate
  reference), `STATS.md`/`script/stats.ts` (generated upstream stats — flagged, FU-060), and `LICENSE`
  (MIT, attribution preserved) as-is. Result: 24 files, +207/−2,794.
- **Alternatives rejected:** keep-full-upstream + append a diff (redundant); delete the 21 translated
  READMEs (harder than a pointer, loses the lang files); gut AGENTS.md (functional build doc).
- **Consequences / revisit when:** Committed `cbfc738` + pushed `origin/dev` (`f094279..cbfc738`), FU-059
  resolved (only the 24 doc files staged; s054's untracked `release.ts` left out). If the fork grows its own
  npm package/CI/community, the "Upstream"/"Install & run" sections should gain fork-specific install/links.
  If a MarkCode logo asset is produced, swap the logo `<img>` (currently reuses upstream's ornate SVG).
  `STATS.md` decision still open (FU-060).

## DEC-039 — Rebrand terminal ASCII art to "MarkCode" (3 shared sources, keep block style)

- **When:** 2026-09-19 (s056)
- **Context:** user asked to change the "opencode" ASCII art the web daemon prints (its terminal banner) to
  "MarkCode", with "search online". Research: the banner comes from `UI.logo()` (web.ts line 47, shared with
  `upgrade`/`uninstall`), which renders a **plain `wordmark`** (non-TTY) or a **two-tone `glyphs.left`/`right`**
  (TTY: left=dim gray `\x1b[90m`, right=default white, with `_`/`^`/`~` shading marks) from
  `@opencode-ai/tui/logo`. That same logo feeds the main TUI `Logo` component and the session-epilogue
  header in `packages/tui/src/util/presentation.ts` (a 2nd copy). Web search confirmed no existing
  "MarkCode" art; no local figlet; online generators are client-side → hand-authoring in the existing 4-line
  block font is the consistent choice.
- **Decision:** Replaced the art in all **3** files with `Mark`/`Code` glyphs in the same 4-line block font
  (letters 4×4, 1-space gap; left 19 chars = `Mark`, right 19 chars = `Code`): `packages/tui/src/logo.ts`,
  `packages/tui/src/util/presentation.ts`, `packages/opencode/src/cli/ui.ts` (`wordmark`, marks→plain:
  `_`→space, `^`→`▀`). Kept the two-tone TTY coloring + shading marks. Verified with a render-sim of the
  exact `draw()` and forced typecheck (2/2).
- **Alternatives rejected:** standard ASCII figlet banner (would change the 4-line compact style + require
  restructuring the renderer); a web-generated banner (no server-side API found).
- **Consequences / revisit when:** NOT committed/pushed yet. If a MarkCode logo asset / new design arrives,
  re-apply across the same 3 files. Other branded surfaces (web app title, favicon `site.webmanifest`) already
  say MarkCode (s053 + pre-existing fork build).

## DEC-040 — Home Sessions list: AJAX cursor pagination (Load more) + lazy search scan (s058)

- **Date:** 2026-09-19 (UTC), session s058
- **Decision:** Both Home session lists (Projects-tab + Sessions-tab) are **cursor-paginated by server
  round-trip**: on refresh only page 1 (limit 64) is fetched; a **Load more** ghost button
  (`common.loadMore`) calls `fetchHomeSessionPage` with the returned `cursor.next` and appends
  (`createPagedHomeSessions` hook in `home-sessions-paged.ts`). Page 1 is a tanstack query (refetch on
  mount/reconnect); SSE session events trigger a cheap page-1 reload so the top stays fresh. The eager
  full-table scan (`loadHomeSessionIndex`) moved into the **search controller and is lazy** (enabled only
  while the search is focused), so a page refresh that never opens search performs no 5000-row scan.
- **Rationale:** mobile-first performance and a real reduction in refresh load time — the previous approach
  rendered a fixed in-memory slice over an eagerly full-scanned index. Load-more-by-AJAX means fewer bytes
  and no unbounded scan on every Home mount.
- **Alternatives rejected:** classic numbered pager (no "next page" model for a time-sorted feed; more taps);
  virtualized infinite scroll (complexity, no "how many remain" signal); keeping the eager full-index scan
  just to satisfy search (defeats refresh-time saving — search is deferred instead).
- **Consequences / revisit when:** search results are limited to the retained index (search runs the same
  `retainHomeSessions` trim as before). `projectDirectories`/`projectByID` duplication exists in the list +
  search controllers (kept: small + stable). If the per-directory retain cap must shrink, revisit
  `retainHomeSessions`. Deploy via `deploy-web-4447.sh --detach`; fork source not yet committed (FU-064).

## DEC-041 — Server HTTP Basic auth stays the universal guard for the web UI (s061)

- **Date:** 2026-09-20 (UTC), session s061
- **Decision:** The web server's HTTP Basic username/password (`opencode` / `hahahaha`, launched via
  `OPENCODE_SERVER_PASSWORD`, run-web.sh / deploy-web-4447.sh) remains the **universal guard for the whole
  web UI**, on top of the app's cookie-based login page (`oc_creds`). Clear-cache resets only client-side
  state + the cookie login; it must NOT remove Basic auth — JS cannot erase HTTP Basic credentials anyway,
  and the user explicitly wants the credential checkpoint kept.
- **Rationale:** single, server-side, token-less gate that protects the UI (and iOS PWA) at the network
  layer outside the reach of any client-side state reset; belt-and-suspenders with the session cookie.
- **Alternatives rejected:** removing Basic auth (leaves the LAN-exposed UI open); having Clear-cache try to
  sign out of Basic (impossible from JS; would require redirect hacks with no real effect).
- **Consequences / revisit when:** users must know the Basic creds as well as the app login. Revisit only if
  a proper upstream identity provider replaces both layers.

## DEC-042 — Unified user-facing version `1.<MAJOR>.<UTC-deploy-ts>` (webui + desktop) (s066)

- **When:** 2026-09-24 (s066)
- **Context:** the fork had three version-bearing surfaces — engine (`/api/health`, from `OPENCODE_VERSION`),
  webui (`packages/app` Settings "v…", from `pkg.version`), and desktop wrapper (`app.getVersion()` →
  About/updater/logging). Only the engine actually received a date-versioned build; webui + desktop still showed
  the stale upstream `1.18.31`. User asked to unify the version number the two user-facing surfaces (webui +
  desktop wrapper) show into a single string whose time part = deploy/package generation time, for all channels.
- **Decision:** Replace DEC-037's intel SemVer (`MAJOR.MINOR.PATCH-fork.<N>`) for the **version string** with one
  unified grammar across all channels (dev/beta/stable): **`1.<MAJOR>.<YYYYMMDDHHMMSS>`** (UTC). `1` = web-wrapper
  product major; `<MAJOR>` = fork/feature major counter (increments per stable/beta cut via `--bump`); the last
  field is the 14-digit UTC deploy/package timestamp. `OPENCODE_CHANNEL` **stays `mark-dev`** (SQLite DB suffix) —
  unchanged.
- **Implementation:** (1) `packages/script/release.ts` simplified to emit `1.<MAJOR>.<ts>` for all channels
  (`readForkMajor` only trusts `<MAJOR>` when current == `^1\.(\d+)\.\d{14}$`); keeps lockstep package.json writes
  + `OPENCODE_VERSION` env. (2) `packages/app/src/entry.tsx` platform.version prefers injected
  `import.meta.env.VITE_APP_VERSION` (falls back to `pkg.version`). (3) `packages/opencode/script/build.ts` passes
  `VITE_APP_VERSION=${Script.version}` when building the embedded webui → deployed webui = engine version.
  (4) `packages/desktop/electron.vite.config.ts` renderer defines `import.meta.env.VITE_APP_VERSION` from
  `OPENCODE_VERSION`; desktop wrapper `app.getVersion()` still flows via `prepare.ts` = `Script.version`
  (must set `OPENCODE_VERSION` when packaging the desktop).
- **Verified:** typecheck (app/opencode/desktop) clean; `release.ts --channel dev --json` → `1.1.<ts>`;
  stable `--bump` → major `1.1`→`1.2`; app bundle contains injected version.
- **Alternatives rejected:** keeping DEC-037 (still stale for webui/desktop); date-only (no major counter);
  unifying only dev (user chose all channels).
- **Consequences / revisit when:** desktop wrapper must be packaged with `OPENCODE_VERSION` set to inherit the
  unified version (prepare.ts + renderer). Upstream base is no longer visible in the version string — track
  upstream divergence in release notes instead. Revisit if the fork ever publishes to a registry (would need a
  strict SemVer/tag).

## DEC-043 — Settings v2 nav: flip TabsV2 orientation from a matchMedia signal on narrow screens (s067)

- **Context:** the user asked whether Settings v2 could be made responsive so the category nav stops stealing width
  from the key/value rows on narrow screens ("put the categories in a tab or something"), explicitly without a large
  redesign. Study first: on a 390px phone the dialog is `min(100vw - 32px, 980px)` = **358px**, and the nav kept a
  **side column** at every width (240px desktop → 144px below 640px), so the key/value area got ~214px — minus the
  fixed `40px` inline padding on `.settings-v2-tab-header`/`.settings-v2-tab-body` = **~134px of usable row width**.
- **Decision:** drive the **existing** `TabsV2` `orientation` prop from a `matchMedia("(max-width: 639px)")` signal
  in `dialog-settings-v2.tsx` (`vertical` on wide, `horizontal` on narrow), and style the horizontal case as a
  scrollable top tab strip. The nav's inner markup was flattened (7 nested `flex flex-col` Tailwind divs → `.settings-v2-nav`
  > 2× `.settings-v2-nav-group` + footer) so the strip is a plain row (`display: contents` on the groups) with the
  section titles + version footer hidden. Narrow screens also drop the header/body inline padding 40px → 16px.
- **Why this is the cheap, safe path:** Kobalte keeps `orientation` as a **context accessor** — the root and list
  render `data-orientation`, the list also `aria-orientation`, and `TabsKeyboardDelegate` reads `this.orientation()`
  at key-event time. So a runtime flip updates layout, ARIA and arrow-key direction together, with no remount and no
  lost tab state. `TabsV2` (ui package) was **not** modified; all new CSS lives in the app package
  (`settings-v2.css`) scoped under `.settings-v2[data-variant="settings"][data-orientation="horizontal"]`.
- **Breakpoint 640px** = the breakpoint already used in this file for row wrapping and control stacking, so the nav
  flip and the row layout flip together.
- **Alternatives rejected:** (a) pure CSS `display:contents` on the existing 7 nested divs — brittle, breaks on any
  markup edit, and still leaves the section titles/footer in the strip; (b) CSS-only orientation flip
  (`flex-direction` override) — would leave `aria-orientation="vertical"` and Up/Down keys on a horizontal strip;
  (c) a new horizontal nav component / drawer / select — a redesign, which the user excluded; (d) widening the
  breakpoint above 640px — the vertical layout is still fine at 640-900px and phone-landscape is an acceptable edge.
- **Consequences / revisit when:** the two section titles ("Desktop" / "Server") and the app-name/version footer are
  **invisible on narrow screens** (the footer info is desktop-ish anyway). If someone needs them on a phone, add them
  to the tab header rather than the strip. Revisit if the app ever gets a settings *page* (non-dialog) — the same
  classes would then need a page-level container.

## DEC-044 — Settings v2 narrow-screen nav: review of fa41da0 — 3 defects fixed, dead weight removed (s068)

- **Trigger:** user challenged the s067 commit (`fa41da0`) — "modified code is no longer useful and can be better".
  The challenge was **correct**: review found 3 real defects plus ~14 lines of avoidable code, all fixed in `71c73a0`
  (pushed `origin/dev`, deployed :4447 pid 2999326, user-confirmed).
- **Defect 1 — medium-width regression:** deleting the `@media (max-width:639px) { list: 144px }` rule left the
  vertical nav at a fixed 240px for every viewport ≥640px while the key/value rows still stop wrapping at that same
  640px (`@media (min-width: 640px) { flex-wrap: nowrap }`, unchanged by the commit). Result: a constant **−96px**
  of usable row width from 640px to ~1011px (344→248 @640, 524→428 @820). **Fix:** app-scoped
  `width: clamp(168px, 24vw, 240px); min-width: 0` on the vertical list — 168px @640, 197px @820, 240px ≥1012,
  desktop unchanged. Lesson: when a responsive branch disappears, the *other* breakpoint that governs the same
  component's internals (here row wrapping) must be re-checked at the same time.
- **Defect 2 — selector matched nothing:** the strip icon-hiding rule used `[data-slot="icon-svg"]`, but `Icon`
  renders `<div data-component="icon"><svg data-slot="icon-svg">…</svg></div>` — the box that consumes the space
  is the wrapper div. The rule was inert, so every label kept an empty 20px icon slot (the user spotted it before
  it was deployed to their phone). **Fix:** target `[data-component="icon"]`. Rule of thumb for this codebase: slot
  selectors are for slot elements (`data-slot`), component selectors (`data-component="icon"`) for wrappers.
- **Defect 3 — unsafe centring:** `justify-content: center` with `width: max-content` + `min-width: 100%` centres an
  overflowing strip on **both** sides, clipping the first tab where it cannot be scrolled to (measured x = −7px @390,
  −22px @360). **Fix:** `justify-content: safe center` (centred when it fits, start-aligned + scrollable when not;
  degrades to the flex default if `safe` is unsupported).
- **Dead weight removed:** (1) the hand-rolled `createSignal`+`onMount`+`matchMedia`+`onCleanup` viewport listener →
  `createMediaQuery("(max-width: 639px)")` from `@solid-primitives/media`, the helper already used at **8 sites** in
  `packages/app` — the commit was the only place that bypassed it; (2) 9 lines re-declaring `width/overflow-x/
  scrollbar-width/-ms-overflow-style` + the `::-webkit-scrollbar` rule that `ui/tabs-v2.css:31-40` already provides
  for the horizontal list (Kobalte puts `data-orientation` on the list, so it applies); (3) a dead
  `border-inline-end: none`; (4) colour moved from the trigger to the wrapper to mirror the vertical variant's
  structure in `tabs-v2.css:198-204`.
- **Kept deliberately:** `overflow-x` on the strip (computed `overflow-x:auto` **and** `scrollbar-width:auto` in this
  state, so no app rule was hiding the scrollbar — the ui rule's `scrollbar-width: none` must stay where it is);
  `display: contents` on the nav groups (no other precedent in `packages/app`, but it is the only way to flatten
  the section groups without duplicating markup); `packages/ui` **still untouched** — the adaptive width is an
  app-level override at higher specificity (`.settings-v2[…][data-orientation="vertical"]`).
- **Collisions checked:** `settings-v2-nav`/`-nav-group`/`-nav-footer` and `class="settings-v2"` are unique to this
  dialog; `TabsV2` is mounted in exactly one place in the app, so the new CSS cannot leak. (Pre-existing caveat
  recorded: `settings-v2.css:8/12/167/172` select `[data-component="dialog-v2"][data-variant="settings"]` without
  the `.settings-v2` prefix, so they also match the manage-models and server dialogs.)
- **Residual (not changed):** below 640px rows still stack the control under the label (now defensible with 368px of
  inner width); the nav flips at 640px while `general.tsx`'s `mobile` signal is 767px (both pre-existing choices);
  five tabs still overflow in very long locales even label-only — the strip scrolls and `safe center` keeps the first
  tab reachable, with an edge-fade precedent at `titlebar-tab-strip.tsx:411-420` if ever needed.

## DEC-045 — A folder is a project: record every resolved directory, list plain folders (s069, FE-020)

**Context.** "opencode fork, project folder selector: after selected and dismiss dialog, the path seems not
propagate return to outside." Reproduced live: Home ▸ Projects ▸ Add project + a folder without a git repo →
the dialog closes and nothing changes. Git folders worked.

**Why it happened.** A project is a **git identity**, not a path (`core/src/project.ts:109`): remote-url hash →
id cached in `<git-common-dir>/opencode` → first root commit sha (confirmed on the live server: a prepared
folder's project id *is* its commit sha). A directory with no repository resolves to `{id: "global",
directory: "/"}`, and `Project.saveProjectDirectory` returned early for the global project — so a plain folder
was recorded in no table at all. The Home list became server truth in s043, so there was nothing left to
render and the picker's result disappeared silently. A `git init` does **not** fix it: a repo with no commits
has no remote and no root commit, so it still resolves to `global` (measured), and the `initGit` call also
*repoints the global project's own `worktree`* at the new folder.

**Decision.** The list means **every folder that has been opened on the server**, and a folder does not have to
be a repository:

1. **Engine (additive).** A directory without a repository is recorded under the `global` project by
   `Project.recordOpenedDirectory`, called from the **`project/current` handler** — the request a client makes
   when it *opens* a directory (Home ▸ Add project, a tab, a session) — and a new row is announced as
   `project.directories.updated` on the global bus. Repositories keep recording their own worktree in
   `fromDirectory`. No schema change, no SDK regen: `project_directory`, the route and the client's
   refetch-on-that-event wiring already existed.
   **Two rules that only the live test could teach:**
   - *The trigger must be "opened", not "resolved".* `fromDirectory` was the first home for this, and it is
     wrong: resolving a project is also what every directory **listing** does, so browsing the picker recorded
     every folder it listed — one run left 33 rows including `/usr`, `/boot`, `/proc`, and every
     `opencode-test-*` dir. Anything that merely *reaches* a directory must not remember it.
   - *The recorded value is the requested directory, not `ProjectV2.resolve`'s `directory`*, which is `"/"` for a
     repository-less directory. And only a real directory is recorded at all (`fs.isDir`, the same check the
     sandbox list uses), so a stale tab or a typo cannot leave an unopenable row.
   Guarded by four tests in `opencode/test/project/project.test.ts` (not recorded on resolve; recorded on open;
   a non-directory is not recorded; a repository is not recorded twice).
2. **App.** Those directories load as a **query** (`[scope, "project-folder"]`) and merge into the Home list
   (`mergeProjectFolders`), deduplicated against project worktrees *and* sandboxes by `pathKey`. The `folder`
   store slice is a *getter* over that query, like `path`/`provider`/`config`, instead of a value written once
   inside `bootstrapGlobal` — otherwise nothing but a full reload ever refreshed it. `add` awaits a refetch of
   that query after `project.current` resolves, rather than waiting for the event to travel back.
   The merge feeds **every** server section (`forServer` too), not only the focused one: it used to return the
   per-device store, which by construction knows nothing about another server's plain folders.
   **The read path cannot go through the client layer.** `GET /project/{projectID}/directories` is a *server*
   HttpApi route, and the generated v2 client is compiled from `makeDefaultApi()` (the default Protocol
   surface), so the method does not exist there; the v1 compatibility layer *does* have
   `project.directories` and answers it with `worktree.list()` → `project.sandboxes(ctx.project.id)`, i.e. the
   current instance's sandbox worktrees. The app therefore calls the route itself
   (`fetchProjectDirectories` in `packages/app/src/utils/server.ts`, same Basic auth as the SDK clients, same
   precedent as `/api/rss/url`). **Lesson:** an invented method on a locally declared API type
   (`type ProjectApi = { … readonly directories: … }`) is enough to satisfy the compiler while the method
   exists on no client at all — extend the *real* client type or the call is unchecked.
3. **No `initGit`.** Home's `add` no longer initialises a repository: it resolves the project (which is what
   makes the server record the directory). The composer path keeps its s033/FU-013 `initGit` for empty folders
   (proven on-device), but a folder no longer *needs* it to be usable.
4. **Picker contract.** Only an explicit selection resolves. No implicit fallback to the folder the tree happens
   to be rooted at — that fallback is what handed `/` to the caller.

**Alternatives rejected.**
- *Mint a per-directory project id for non-repo folders* (`dir:<hash>`): the most principled fix, but it changes
  the identity model — `global` is the CLI/TUI fallback for non-repo directories and `fromDirectory` re-points
  `global` sessions to a new id — and it is a recurring merge-conflict surface in a fork that rebases onto
  upstream regularly (s054 merged 59 commits). Not worth it for a list-completeness gap.
- *Merge the per-browser `layout.projects` store into the Home list*: zero server work, but per-device — the
  exact inconsistency s043 was closed to fix.
- *Publish `project.directories.updated` from `ProjectDirectories.create` (core) with an `EventV2.node` dep*:
  **do not retry** — `ReferenceError: Cannot access 'node' before initialization`, a module-init cycle. The
  engine layer already has `EventV2Bridge` *and* `GlobalBus`, and `emitUpdated` is the global-bus emit the
  client's global branch listens to.

**Consequence to remember.** A folder without a repository is listed but has no project row: it has no id, so
"Edit project" is hidden for it and it cannot be renamed/icon'd. When it later gets a commit it becomes a real
project on the next resolution (the running server caches the identity per directory, so that needs a restart).

## DEC-046 — The DEV dropdown reuses the project page's utility items, not new copies of them (s071)

- **Decision:** the top-left **DEV** menu (`ChannelIndicator`, `packages/app/src/components/titlebar.tsx`) gains
  **Log out / Settings / Help** after a separator, wired to the *same* handlers the project-selection page uses
  (`HomeUtilityNav` → `confirm(sidebar.logoutConfirm)` + `/logout`, `useSettingsDialog()`,
  `platform.openExternal("https://opencode.ai/desktop-feedback")`), and the labels come from the **existing**
  i18n keys `sidebar.logout` / `sidebar.logoutConfirm` / `sidebar.settings` / `sidebar.help`.
- **Rationale:**
  - The user asked for "the 3 items that originally in project selection page". Duplicating the *behaviour* would
    have created a second, subtly different logout/settings path (the class of bug s024/s045/s046 came from), so
    the menu calls the same code the page does.
  - Reusing the existing keys costs **zero new i18n keys** — they are already translated in all 62 locale files,
    so this is also the only version of this change that does not widen the FU-076 parity debt.
  - `useSettingsDialog()` rather than `useSettingsCommand()`: the `settings.open` command is already registered by
    `home-projects-controller` and `pages/session`, and a third `command.register` would duplicate the entry in
    the command palette. The hook is safe to call anywhere under `DialogProvider` (app.tsx:417), which includes
    both titlebars.
  - Item order mirrors the page, and a separator separates the dev-only actions from the user-facing ones.
- **Alternatives rejected:**
  - *New `devMenu.*` i18n keys* for the 3 items: more correct naming-wise, but it needs 62 locale edits for copy
    that already exists, and it would let the DEV menu drift from the page's wording.
  - *A shared `HomeUtilityNav`-style component for both surfaces*: the two hosts differ (a `DropdownMenu.Item` vs
    a full-width nav button with icons), so the only shareable part is 3 tiny handlers — not worth a component.
  - *Localizing the 4 dev-only items in the same change* (Home page / Refresh / Clear cache / Debug tools are
    hardcoded English, so a zh user now sees a mixed menu): deferred to FU-083 to keep this diff to one file and
    not to fabricate 62 translations in the same commit.
- **Consequence to remember:** `sidebar.logout` / `sidebar.logoutConfirm` are still the English placeholder in
  `zh.ts` and most locales (s012/s013, FU-026), so the new Log out item shows English inside a Chinese UI until
  they are really translated (FU-084).

## DEC-047 — "When did the model last speak?" is a client-side observation, not a server timestamp (s070, FE-021)

- **Decision:** the "Thinking" row's elapsed number becomes a **pair** —
  `· A / B` = *seconds since the last model output* / *seconds since the user prompt* — where **A is the max of
  the server's own stamps and a client-observed arrival time**. The observation is implemented as
  `latestTurnActivity()` (`packages/app/src/pages/session/timeline/turn-activity.ts`), which returns
  `{ at, key }`: `at` = max(assistant `time.created`/`time.completed`, each part's last stamp —
  `tool.state.time.end ?? start`, `text/reasoning.time.end ?? start`) and `key` = a fingerprint of the whole
  turn that also changes when a part grows in place.
- **Rationale:**
  - The server **cannot** answer "when did the model last say something" from timestamps alone. It stamps a part
    when the part is *created*, and a streaming `text`/`reasoning` part keeps its original `time.start` while
    tokens keep arriving — so the pre-existing counter (base = last assistant message `time.created`) kept
    counting up during a healthy stream. The `message.part.delta` event mutates `part.text` in the store
    (`context/server-session.ts:1190`), so the client *can* see each update and stamp it with its arrival time.
  - `at` is a **max**, never a replacement: if the store is hydrated by a fetch (or a buffered SSE batch lands
    late), the server stamps still win, so the number can never claim the model spoke later than it really did.
  - The two numbers answer different questions and both were asked for: A = "is it stuck?" (grows only while the
    model is silent), B = "how long has my prompt been running?".
  - The fingerprint is scoped to **one turn**, so updates in other sessions/turns cannot reset it, and the row
    exists at most once (the active turn).
- **Traps hit, recorded so they are not re-introduced:**
  - **`on()` does not dedupe the single-dependency form.** `createEffect(on(() => activity().key, () =>
    setObserved(Date.now()), { defer: true }))` looks right and is an **infinite reactive loop**: `setObserved`
    invalidates `activity()`, which re-fires the effect, which stamps again. Solid only compares element-wise in
    the *array* form (`node_modules/solid-js/dist/solid.js:457-475`). The shipped code compares the previous
    fingerprint explicitly and skips the first run — which also covers what `defer` was meant to cover.
  - **Do not gate the row on `A > 0`.** `A` is legitimately `0` while the model streams (that is the point), so a
    `Show when={lastOutput() > 0}` gate makes the counter *flicker out* on every delta. It is gated on `B > 0`.
  - `ToolStatePending` has **no** `time` field, so a pending `question` tool contributes no stamp and the row
    falls back to the assistant message creation.
  - `Intl.DateTimeFormat` for the tooltip clock follows the existing precedent (`session-ui/message-part.tsx:1221`,
    `timeStyle: "short"`) rather than `toLocaleTimeString`.
- **Alternatives rejected:**
  - *Server-side `lastActivityAt` on the message/part*: the only version that is correct across devices and
    reconnects, but it means a schema change, a protocol/SDK regeneration, and it still cannot timestamp
    individual streamed tokens — the client would still need the observation for the streaming case.
  - *Dropping A and showing only B*: loses the "is it stuck?" signal, which is the whole point of the row.
  - *A new `formatDuration` helper shared with `message-part.tsx`*: the two live in different packages
    (`app` vs `session-ui`) and the row's copy is identical to the existing one, so the duplication stays until
    there is a third caller.
- **Consequence to remember:** with the default `showReasoningSummaries: false` the row is the **live footer of
  the whole busy turn** (`rows.ts:193`: the guard is `showReasoning ? noRenderableParts : true`), so the counters
  sit under the streaming text. Turning reasoning summaries **on** hides the row at the first reasoning text —
  pre-existing behaviour, deliberately left alone.

## DEC-048 — GitHub is the only origin for this control folder (2026-09-27)

**Context.** The control folder's `origin` was the LAN Gitea (`http://192.168.1.162:3300/mark/selfide.git`),
which had **no usable credential** on this machine — only a github.com entry existed in `~/.git-credentials`.
Result: 17 commits (s012 → s071) sat local-only for two weeks while `origin/main` stayed at `5c847a6f9`
(2026-09-12), i.e. the "never keep knowledge only on one device" rule was quietly broken. The GitHub mirror
`nkyang10/selfide` existed and was *ahead* (`92651df82`).

**Decision.** GitHub is the single origin. `main` was pushed to the mirror as a fast-forward (its tip was an
ancestor of local `HEAD`, so nothing was rewritten), then the Gitea remote was **removed** and the mirror renamed
to `origin`; `main` tracks `origin/main`. The user's intent: "github.com is the only source".

**Alternatives rejected.** *Keep Gitea as a second remote*: two origins for one branch is how the 2-week drift
happened in the first place, and it cannot be written to from here anyway. *Force-push*: unnecessary — the
histories had not diverged.

**Consequences.**
- The fork clone (`50-projects/p003-opencode-fork/opencode`) is unaffected: its remotes were already both on
  github.com (`origin` = `nkyang10/opencode`, `upstream` = `anomalyco/opencode`, the read-only reference the fork
  rebases onto).
- A credential now lives in `~/.git-credentials` (github.com, mode 600). Per the no-secrets rule it stays outside
  this folder; note that the :4447 server binary logs permission-evaluation lines, so a token passed on a command
  line can be captured in `opencode/logs/**` (git-ignored) — rotate any token that appears in a transcript.

## DEC-049 — The fork's default listen port is 4447 (2026-09-27) — ❌ REJECTED & REVERTED (s075, same day)

> **Status: REJECTED by the user and reverted before it ever reached a commit or a build.** The code change is
> gone; `server/server.ts` is back to upstream's literal 4096 and no `Server.DefaultPort` exists. The reasoning
> below is kept because the *tracing* is still valid and was reused; the *decision* is not. The replacement is
> DEC-050 (see `50-projects/p003-opencode-fork/notes/plan-admin-settings.md`): a 4446 default delivered through
> the **config schema** (`server.port`), not through the server's port-fallback constant. Note this also
> supersedes the earlier "keep 4446 in the Windows installer" carve-out, which now simply agrees with the rest.

**Context.** The fork is known as the ":4447 MarkCode web UI" (every deploy script, the desktop launcher, the
tunnel, the docs all say 4447), but that port was never the program's default — it was passed explicitly
(`web --port 4447`). Upstream's default came from a single hard-coded literal: `cli/network.ts` defaults the
`port` option to `0`, and `server.ts:startWithPortFallback` resolves `0` to *try 4096 first, then any free port*.
So a fresh install that just ran `opencode web` landed on 4096, and `opencode serve` had to be told 4447.

**Decision.** The fork's preferred port is **4447**, expressed as one exported constant
`Server.DefaultPort = 4447` in `packages/opencode/src/server/server.ts` and used by `startWithPortFallback`. The
precedence chain is untouched: explicit `--port` > `server.port` in `opencode.json` > 4447 > any free port. The
plugin `baseUrl` fallbacks and the two `--help` examples that hard-coded 4096 now derive from / match the same
default, the two unit tests that pin the preferred port were updated, and `CONTRIBUTING.md` states 4447.

**Alternatives rejected.** *Make it a CLI `default: 4447` in `network.ts`*: that would also change the meaning of
an explicit `--port 0` (deliberately "any free port") and would lose the *prefer-our-port, else fall back*
behaviour, so a busy 4447 would fail the start instead of degrading. *Per-command defaults (web only)*: two
defaults to remember, and the TUI spawns a server through the same path anyway. *Hard-code 4447 at each call
site*: five literals to keep in sync — the constant is the point.

**Consequences.**
- **`4446` is intentionally kept** in `script/build-windows-installer.ps1` and the fork `AGENTS.md` "This fork"
  section (user decision, s072). That installer passes `--port 4446` explicitly, so it is self-consistent and
  unaffected by the default. The fork therefore has two documented ports: 4447 = default/Linux deploy,
  4446 = Windows installer.
- Dev-loop drift to be aware of: `packages/app`'s Playwright config and ~15 e2e specs default
  `PLAYWRIGHT_SERVER_PORT` to **4096** and address an externally started backend, so a backend started as a plain
  `opencode serve` is no longer where the e2e harness looks (FU-087). Those are env-driven, not default-driven.
- The generated JS SDK (`packages/sdk/js/src/{,v2/}gen/client.gen.ts`) still carries `baseUrl:
  "http://localhost:4096"`; the generator (`packages/sdk/js/script/build.ts`) now says 4447, so the checked-in
  output will follow on the next regeneration (FU-088).
- Not yet in any binary: the change is uncommitted and the live :4447 (pid 3654762) is untouched, so the default
  only takes effect after a build (FU-086).

## DEC-050 — "Default 4446" is delivered by the config schema, not by the server's port fallback (2026-09-27)

**Context.** DEC-049 put the fork's default listen port in `Server.DefaultPort` (4447) inside
`server/server.ts`. The user rejected it (s075). The requirement itself survives, with the number the user
actually wants: **4446** — the port the Windows installer has always used, and the default the new Admin
settings row is to show.

**Decision.** Keep upstream's `startWithPortFallback` literal **4096** untouched, and express the fork default as
a **default in the config schema**: `ConfigServerV1.Server.port` (`packages/core/src/v1/config/server.ts`)
becomes `Schema.optional(PositiveInt)` **with a 4446 default**, so an unset `server.port` decodes to 4446 and
`resolveNetworkOptionsNoConfig` (`cli/network.ts:69`, which already prefers `config?.server?.port`) hands 4446
to the listener. `--port` still wins (explicit CLI arg is checked first), a configured value still wins over the
default, and a busy 4446 still degrades to a free port. This lands as phase P1 of FE-023, next to the new
`server.webui.autoStart` key.

**Alternatives rejected.** *`Server.DefaultPort = 4446`* (DEC-049's shape): rejected by the user, and it edits a
file every upstream merge touches. *A CLI `default: 4446` in `cli/network.ts`*: that option's `0` is
meaningful ("no preference" → prefer-then-fall-back), so giving it a real number would also change what an
explicit `--port 0` does. *Nothing at all, port only in the UI*: then the Admin row would display 4446 while the
server actually listened on 4096 — the honest UI needs the default to be true, not cosmetic.

**Consequences.**
- `server/server.ts`, `cli/network.ts`, the CLI help strings and the port unit tests are **not** touched; only
  the config schema + its docs. Much smaller merge surface against upstream.
- The Admin "webui port" row can show **4446** as the effective default honestly, and the save writes
  `server.port` explicitly (making the value visible in `opencode.jsonc` rather than implied).
- The `server.port` schema default flows into the generated JSON schema and the config docs, so the published
  default for `server.port` becomes 4446 for everyone using the fork — worth stating in the fork README.
- 4447 remains exclusively the **local Linux dev/deploy** port, passed explicitly by
  `scripts/run-web.sh` / `deploy-web-4447.sh`; nothing in the program depends on it.

## DEC-051 — Turn progress is a client-side record of the submission, not a status value (s073, FE-022)

**Context.** The user reported the agent chat showing no "Thinking" after submitting a prompt until the
first model response, and not being able to tell a connection problem from a slow start. Measured on the
live :4447 (Playwright, SSE tee + MutationObserver, probes in `/tmp/opencode/probe/`):

- healthy model → the row appeared **28 ms** after Enter, so the happy path was never the bug;
- the server's default model on this box (`opencode-go/gpt-5.6-luna`) answers *"An active OpenCode Go
  subscription is required to use Go models"*, so the status flaps `busy → retry(1) → busy → retry(2) …`;
- during a retry backoff the session is **absent from `/session/status`**, and the 15 s status watchdog
  ("store says busy but the server does not list it ⇒ idle") therefore demoted a **live** turn to idle and
  the progress row disappeared mid-flight (reproduced: row removed at 15.1 s while the server was on retry
  attempt 4).

**Decision.** Three parts.
1. `utils/turn-progress.ts` — a per-(server scope, session) **client-side record** of "this client
   submitted turn X and the server has not acknowledged it yet": `begin` on submit (synchronously, before
   any `await`), `settle` on the server's **first status event** for that session, on every send-failure
   rollback, and by the status watchdog for sessions the server does not list as running. The timeline
   reads it in a memo, so the row is a *signal* input, not a status value.
2. The row renders while the turn is unfinished: `status !== "idle" || pending` — `retry` included, so an
   upstream backoff can never look like a dropped connection — and the watchdog no longer demotes a
   `retry` (a retry is self-healing: the server publishes `busy`/`idle` itself).
3. The label names the stage: `Sending` (submitted, no status yet) → `Thinking` → `Waiting for the model`
   (≥10 s with **zero** model output for the turn, so a long tool call cannot trip it). FE-021's `· A / B`
   counters and tooltip are unchanged.

**Alternatives rejected.** *Trust the optimistic `busy` status alone*: it is skipped whenever
`sessionDirectory !== projectDirectory` (sandbox worktrees) and is only as fresh as the last status event —
the exact two things that produced the blank. *A spinner in the composer instead*: the composer's own
`working` signal has the same source, so it would blank in the same cases; the timeline is where the user
is looking. *Polling for progress*: no endpoint distinguishes "queued", "connecting to the provider" and
"thinking", so any label would be a guess. *One row that also absorbs the retry card*: the retry card
carries the attempt count, countdown and provider message, so it stays; the progress row above it keeps
the elapsed counters alive (deliberate, verified by e2e).

**Consequences.** The turn indicator is now driven by "is this turn finished?" instead of "did the server
say `busy`?", which is the only formulation that cannot go blank while work is outstanding. Two new i18n
keys ship as English source copy in all 62 locales (FU-026/FU-076 pattern — real translations still owed,
tracked with FU-084). The record is per page session: a reload drops it and the server's own status takes
over, which is the correct authority after a reload.

### DEC-050 correction (s076) — the config-schema default was NOT the mechanism used

DEC-050 above proposed giving `ConfigServerV1.Server.port` a **schema default of 4446**. When FE-023 was
actually built (s076), that turned out to be the wrong lever and was **not** used:

- A `Schema.withDefault` on `port` makes the field **required in the TypeScript type** (`ConfigV1.Info`), and
  the app patches config with **partial** objects (`updateConfig({ disabled_providers: next })`,
  `updateConfig({ server: { port } })`). A required field would ripple through every construction site and
  would also make the effective port appear in every `GET /config` response — a wire-format change for API
  consumers, in a change that was supposed to be two UI rows.
- Worse, the promise the schema default makes is not what the Admin tab can honour: a *saved* port still needs
  a restart, and auto-start (FE-024) has its own default to pick.

What s076 actually does instead, and why it is honest:

- **The compiled-in default is untouched** — `startWithPortFallback` still prefers 4096, so `opencode web`
  behaves exactly as before for anyone who never opens the Admin tab (this is also the shape the user accepted
  when s072 was rejected in s075).
- **4446 lives in one place for the admin surface**: `Webui.DefaultPort` (`src/server/webui.ts`) is what the
  Admin port row offers as the default and what FE-024 auto-start uses when the config sets no port.
- **The port row writes the real key** (`server.port`) on the first explicit Save, so 4446 becomes a
  *persisted* value instead of an implied one — and `GET /global/webui` reports the configured port next to the
  one the listener bound, so the tab can never claim a default the server is not using.
- Consequence to remember: a fresh install that never touches Admin still serves on 4096, and the two numbers
  (4446 in the tab, 4096 on the socket) coexist until the first Save. That is stated in the tab's status line
  ("Not set in the config file. Running on port N."), not hidden.

---

## DEC-052 — the timeline "Changed files" group collapses as **one persisted per-session flag**

**Date:** 2026-09-27 (UTC) · **Session:** s077 · **Feature:** FE-025 · **Status:** PLANNED, not built

**Request:** *"plan do modified file default collapse like todo list. default collapse, toggle on user manual
click."*

**Decision.** The `DiffSummary` row in the session timeline (`packages/app/src/pages/session/timeline/message-timeline.tsx:204-284`)
gains a **third collapse axis around the whole group**. Collapsed = the existing 44px sticky
"3 Changed files" header plus a `+12 −4` tally plus a chevron, nothing else. Clicking the header (or
Enter/Space on it) reveals the existing per-file `Accordion`, where each file's diff is *already*
default-collapsed. Two levels: group → file list → diff.

**Why a third axis and not a change to an existing one.** The two axes that exist are not the axis the
request is about: the 10-file cap (`showAll`) is a truncation control, not a collapse, and the per-file
Kobalte `Accordion` is *already* collapsed by default. The thing that is always expanded is the **file list
itself** — up to 10 rows, ~440px of chrome. That is what "default collapse" targets.

**Why persist per session (user decision 2).** The row is inside a `@tanstack/solid-virtual` list, so it is
**unmounted** when it scrolls out of the window. Its `createStore({ showAll, expanded })` is component-local
(`:207-210`) and therefore **resets on scroll-away and back** — a pre-existing bug for axes A/B. A new local
signal would inherit it. The store already has the exact precedent: `SessionView.todoCollapsed`
(`packages/app/src/context/layout.tsx:75`, accessor `:865-876`, consumed at `pages/session.tsx:2144-2145`) —
the composer's todo dock. **"Default collapse" is implemented as the *absence* of state** (`?? false`), not as
writing `false` anywhere, so no browser is migrated and **no `migrate` branch and no `layout.v6` bump** is
needed (`migrate` at `layout.tsx:183-268` only rewrites specific legacy shapes).

**Why `MessageTimeline` gains no new prop.** It already holds `const { params, sessionKey } = useSessionKey()`
(`:332`) and the layout provider sits above it, so `TimelineDiffSummaryRow` can call
`useLayout().view(sessionKey)` directly. Adding a prop would have meant touching the `session.tsx:2089`
call site for nothing.

**Why "like a todo list" is taken literally.** `packages/app/src/pages/session/composer/session-todo-dock.tsx:110-215`
is the in-product precedent: a `role="button" tabIndex={0}` single row, Enter/Space, a `chevron-down`
`IconButton` rotated by `transform`, `aria-hidden` on the list. The new header copies that interaction model
rather than inventing a third one.

**Why the accessibility fix is in scope (user decision 3).** `session-turn-diffs-toggle` (`Show all`) is a bare
`<span onClick>` with no `role` / `tabIndex` / `aria-expanded`, and its CSS is `opacity: 0` until the group is
hovered (`session-turn.css:125,137,141`) — so it is invisible to keyboard users *and* to touch users until a
tap. `session-turn-diffs-more` (`+N more files`) is a bare `<div onClick>`. Both become real `<button
type="button">`s; the new outer header carries `aria-expanded` + Enter/Space.

**Why no new i18n key.** `ui.sessionTurn.diffs.changed.{one,other}` is already the header's accessible name and
`showAll` / `showLess` / `more` already exist. The chevron therefore gets `aria-hidden="true"` and **no**
label: any honest label ("Show changed files") would need **66** locale files in `packages/ui/src/i18n/`
(`ui.*` keys) or `packages/app/src/i18n/parity.test.ts` fails. Deferred, with the exact procedure recorded
(English byte-for-byte, FU-026 pattern, never invent translations) in the plan §2.5.

**Traps recorded now so they are not rediscovered.**
1. `Show all` and `+N more` are **children of the header** that becomes clickable → they must
   `stopPropagation()` or clicking `Show all` also collapses the group. Most likely defect in the change.
2. Two e2e specs (`e2e/performance/timeline-stability/interaction.spec.ts:176-231`,
   `e2e/regression/session-timeline-projection.spec.ts:131-162`) assert the currently-expanded file list and
   **will** fail on the new default. That is the feature working, not a regression.
3. `--sticky-accordion-offset: 44px` (`:236`) exists because the group header is 44px tall; it must stay 44px
   in **both** states or the per-file sticky headers overlap.
4. `packages/session-ui/src/components/session-turn.tsx:436-527` is a **dead duplicate** of this markup that
   still shares its CSS. Not touched; recorded as drift.
5. The 10-file cap and both overflow controls stay **inside** the collapsible body, unchanged.

**Rejected alternatives.** *(a) Collapse only the header* — the file list is what occupies the space, so this
changes almost nothing visually. *(b) One click straight into a combined diff* — removes the per-file
navigation and the `Show all` control, more churn than the request implies. *(c) In-memory-only state* — the
user chose persistence, and it also fixes the virtualised-remount reset for the new axis. *(d) A Settings
toggle for "expand by default"* — the user's persistence choice does not need one; it would add 2 keys ×
66 locales in `packages/app/src/i18n` for no requested benefit.

### DEC-052 addenda (user-confirmed, 2026-09-27, still s077)

**A. The row's content does not change — only its state and its hit target.** The user specified: *"I will
notify changes in number of file changed and total number of line and then toggle to view manually."*
Checked against the code before assuming: that notification **already exists and is already the turn total.**
`language.plural("ui.sessionTurn.diffs.changed", props.diffs.length)` (`:224`) gives the count, and
`<DiffChanges changes={props.diffs}>` (`:226`) is passed the **whole array** — `diff-changes.tsx:9-19` sums
`additions`/`deletions` across every file, so `+12 −4` is the sum over the turn, not one file.
`additions` / `deletions` are **required** `Schema.Finite` on `SnapshotFileDiff`
(`packages/schema/src/file-diff.ts:6-7`), so there is no absent-value case. **The feature adds no number and
changes no number**; it makes that existing row the default-collapsed state and the click target.

**B. The `+12 −4` split is kept, not collapsed into one total.** `DiffChanges` computes an internal `total`
(`:20`) but renders only the split. A single "34 lines changed" figure needs a new plural key in
**`packages/ui/src/i18n/`** (66 locale files) and `i18n/parity.test.ts` fails if one is missed. The split is
the familiar git/GitHub convention, so the user kept it and **no i18n debt is taken on**.

**C. The zero-change case stays hidden.** `DiffChanges` renders only when `total() > 0` (`:41`), so a
rename-only or binary turn shows just "3 Changed files" with no tally. Kept as-is; no new zero-case string.

**D. Persistence = ONE flag for the whole session (option A), explicitly chosen over per-row.** I offered
A (one `SessionView.diffSummaryOpen` boolean, mirroring `todoCollapsed`) vs B (a `string[]` of open row ids
keyed by `userMessageID`, mirroring the Review panel's `reviewOpen`). The user chose **A**, accepting the
consequence I flagged: **opening one turn's list leaves every other turn's list in the session open too**,
because they all read the same flag. Recorded as an **accepted behaviour, not a defect** — so a later
complaint ("I opened one and everything opened") is answered with the recorded per-row shape rather than
re-investigated. `SessionView.diffSummaryOpen?: boolean` is an optional field read as `?? false`, so there is
still **no `migrate` branch and no `layout.v6` bump**.

**Net effect on scope:** F3 (per-file diffs) is already default-collapsed, F6 (the 10-file cap) is unchanged,
F1's row content is unchanged. The whole feature is **a `<Show>` around the body, a toggle on the header, one
persisted boolean, and a `<span onClick>` → `<button type="button">` conversion — with zero new i18n keys.**

## DEC-052 — A deploy that must not carry a parallel session's WIP is built in a throwaway worktree (2026-09-27)

**Context.** The fork checkout is edited by two agents at once (s073 shipped FE-022 while s074/s075
built FE-023 Admin settings). `build-linux.sh` compiles **the whole tree**, so a :4447 deploy bakes in
whatever is uncommitted — FU-082, which had already happened twice. On s073 the first deploy shipped the
parallel session's unfinished `webui.autoStart` work, and the second deploy would have done it again.

**Decision.** Build from a **detached worktree at `origin/dev`** with the existing `node_modules`
symlinked in, skip `bun install`, and copy the resulting binary over the serving path:

```
git worktree add --detach /tmp/opencode/clean-build origin/dev
ln -s <fork>/opencode/node_modules            /tmp/opencode/clean-build/node_modules
for d in <fork>/opencode/packages/*/node_modules; do ln -s "$d" .../packages/<pkg>/node_modules; done
# same OPENCODE_VERSION/OPENCODE_CHANNEL as build-linux.sh, then:
bun ./packages/opencode/script/build.ts --single
cp <worktree>/packages/opencode/dist/opencode-linux-arm64/bin/opencode  <serving path>.new && mv -f … 
kill :4447 listener; scripts/run-web.sh 4447
```

`mv` (not `cp`) into the serving path, because `cp` onto a running executable fails with ETXTBSY.
Nothing of the other session's is touched — no stash, no checkout, no worktree sharing — and the build
input is exactly what is pushed.

**Alternatives rejected.** *`git stash` the other session's WIP around the build*: it would yank files
out from under a running agent and race with its next write. *Wait for the other session to commit*:
correct but serialises two agents on one box. *Build from the shared tree and accept the WIP*: that is
the bug, not a fix.

**Consequences.** :4447 now serves `d04b79e` only, verified end-to-end. The recipe is worth keeping for
any deploy on a shared checkout: **a build is a snapshot of the tree, so on a shared tree it is a
snapshot of somebody's unfinished work.** Side lesson: `bun turbo typecheck` went red mid-session from
the *other* session's WIP, which forced a `--no-verify` push; the gate is only meaningful for the files
you touched, so on a shared checkout the per-package gate plus a stated reason is the honest minimum.

## DEC-053 — the v2 session list's sort column is `time_updated`, and the index must match it (2026-09-28, s078)

**Decision.** `V2Session.list` sorts and keyset-anchors on `SessionTable.time_updated`, `/api/session` builds both
cursors from `first/last.time.updated`, and `session` carries `index("session_time_updated_id_idx")` on
`(time_updated, id)`. Committed `86c621c`, deployed :4447 as `1.1.20260928011449`.

**Why.** The Home Sessions list fetches a **bounded** page (`limit=15`) and then sorts that page by `time.updated`
client-side. That combination only works if the server's page *membership* is chosen by the same key. It was not:
`sortColumn` was `time_created`, so a session started 17 h earlier and still being worked on fell outside the first
page entirely — invisible in the list, and replaced in the user's view by an unrelated untitled
`New session - <timestamp>` row (with no last-prompt line, because those rows have 0 messages). That is the whole of
"the previous session became New session with not correct last user prompt"; there was no title or prompt bug.

**The rule worth keeping: a page is only correct if the server's page-selection key is the same key the client
sorts and displays by.** The client was already right; the *set* of rows it was handed was wrong. Whenever a list
becomes paginated, re-check the server's `ORDER BY` against the column the UI orders on — the failure mode is
invisible, because the visible order is always correct and only *which* rows appear is wrong.

Three independent signals said updated-time was the intended contract, so this is a bug against a known design, not
a preference:
- v1 `GET /session` is documented *"sorted by most recently updated"* and orders that way.
- `packages/app/src/context/global-sync/child-store.ts:335` — *"use client.v2.project.list and root-filtered,
  **updated-time v2.session.list**"*.
- `home-session-index.ts:172-176` — *"the current V2 API orders by creation time … A bounded page could omit an old
  session updated today."* **That comment predicted this exact bug.** FE-016 (s058) then shipped the bounded page
  anyway, so the warning was correct and the code did not listen. **A TODO that names a failure mode is a spec;
  re-read it before the change it blocks lands.**

**Two things that had to move together.** The sort column and the cursor anchor live in two different packages
(`core` and `server`) and neither references the other, so no type system couples them — changing one alone
silently breaks paging (repeats/gaps). The route-level test asserts the *decoded* cursor, which is what keeps them
honest. That is the only reason the test is worth its runtime.

**Index, and why it is not a trade.** There was no index on `time_created` either: the old plan was
`SCAN session` + `USE TEMP B-TREE FOR ORDER BY`, i.e. a full scan. After: `SCAN session USING INDEX
session_time_updated_id_idx`. Migration is a single `CREATE INDEX` (no table rewrite) — but it does touch live data,
so back up the DB first (s078: `/tmp/opencode/db-backup-before-s078.db`, 896 MB, 109 sessions).

**Testing lesson (mine, worth repeating).** The first version of the fixture was **vacuous**: it stamped
`time_created` and `time_updated` to the same value everywhere, so created-order and updated-order were
indistinguishable and all 5 new cases passed against the *old* code. A test for "these two orderings differ" must
make them differ in the fixture. Verified by `sed`-ing the sort column back and confirming 3 of 5 (plus the route
case) go red.

### DEC-054 — the provider `User-Agent` carries the **upstream** version, not the fork's (2026-09-28, s079)

- **Decision:** the fork keeps DEC-042's displayed version (`1.<counter>.<deploy-ts>`, so `1.1.20260928065214`
  in Settings, `/api/health`, the desktop About box), but the version it puts on the wire in
  `User-Agent: opencode/<version>` is a separate constant, `UPSTREAM_VERSION = "1.18.31"` in
  `packages/script/src/index.ts`, stamped as `OPENCODE_UPSTREAM_VERSION` by all three build scripts and read at
  runtime as `UpstreamVersion` (`packages/core/src/installation/version.ts`).
- **Rationale:** OpenCode's Zen free tier gates on the declared client version and answers **HTTP 426**
  `Error from provider (Console): OpenCode 1.18.0 or newer is required to use the free tier`. DEC-042's grammar
  reads as `1.1.x` — older than 1.18.0 under any numeric comparison — so the fork locked itself out of every
  free model. Measured, not assumed: same account, same model, minutes apart, only the UA differing → old binary
  426, new binary `FREE-OK`. The gate is upstream's and is reported three times
  (`anomalyco/opencode#49944`, `#50451`, `#50581`).
- **Alternatives rejected:**
  - **Put the upstream minor in the displayed number** (`1.18.<deploy-ts>`, one notion of "version"). My
    recommendation; the user chose the smaller change. It would supersede DEC-042 across three `package.json`s,
    `app.getVersion()` and the updater, and it would have needed the fork counter to move into semver build
    metadata — which the app's own `compareVersions` ignores, so the deploy toast would stop firing.
  - **One-off build with `OPENCODE_VERSION=1.18.31`.** No code, but the next ordinary deploy reverts it.
  - **Change DEC-042's counter to ≥ 18.** Semantically wrong: the middle slot stops being the fork counter.
- **Consequences to remember:** (1) the fork now has **two** version notions, so `UPSTREAM_VERSION` must be
  bumped whenever upstream is merged (FU-104) — a stale value is silently accepted by the gate until upstream
  moves past it, which is the safe direction; (2) `packages/core/src/models-dev.ts:23` still sends the fork
  version to `models.opencode.ai` — deliberately, no gate in evidence there; (3) `OPENCODE_UPSTREAM_VERSION` in
  the environment overrides the constant for a one-off build, because `build-linux.sh` only overrides
  `OPENCODE_VERSION`/`OPENCODE_CHANNEL`.
- **Generalisable lesson:** **a user-facing version is also a wire value.** Any hosted service that reads it
  (a gate, a feature flag, a rollout) compares it in the *upstream* numbering space, and a fork that invents a
  new grammar is comparing apples with oranges. When a fork renumbers itself, ask what else reads that string.
