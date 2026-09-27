# p003 — opencode fork: local clone, modifications, own Linux build

**Project:** Vendor the **opencode** source (`github.com/anomalyco/opencode`, MIT), modify it, and build our own
Linux binary instead of relying on prebuilt releases.
**Status:** 🟢 MODIFIED + SELF-BUILT + SERVING — **FE-001** cookie-auth login, **FE-002** project
selector fix, **FE-003** foreground re-sync, **FE-004** folder explorer on mobile, **FE-006** session-list
last-prompt subtitle, **FE-007** home Sessions-tab row → mobile-first multi-line card.
**FE-014 deployed s044:** top-left **DEV** button → dropdown menu with
**Home page** / **Refresh** / **Debug tools** (dropdown now renders in prod builds too, not just DEV).
**FE-015 deployed s044/updated:** server-update **Refresh toast** — `/api/health` returns `{healthy,version}`;
on health-version change (new deploy) a persistent toast with a **Refresh** button is shown. **Updated
(s073):** now also fires when a previously-seen healthy server drops and recovers (deploy restart), even
if the version string is unchanged — so an AJAX update / SSE reconnect after a redeploy always prompts a
refresh. Dev-channel versions are now **globally unique per build** (`1.0.YYYYMMDD-N-HHHH`, time+entropy
suffix) so the version always changes even when the per-day counter resets on another build machine.
**FE-016 deployed s058 (done):** Home **Sessions AJAX cursor pagination** — both Home lists
(Projects-tab + Sessions-tab) fetch page 1 (limit **15**) on refresh and **Load more** fetches the next
cursor page via `createPagedHomeSessions`/`fetchHomeSessionPage`; SSE events re-fetch page 1. The
**search full-scan is lazy** (runs only when search focused) so refresh no longer scans the whole table.
**Committed `2b6c3a2` + pushed** to `origin/dev` (FE-016), plus s056 rebrand `f2fe4cd` (FU-061).
**FE-017 (s059/s060, committed `4b21d04`):** — Compact-and-new-session tab behavior — slim now
 re-places the fresh tab directly after the ended session, renames that session `<title> [ended]`, and
 closes its tab (see `## FE-017`).
**FE-018 (s060, committed `4b21d04`):** — Mobile touch-device detection: on `coarse`-pointer/`maxTouchPoints>0`
 devices, plain Enter in the prompt inserts a newline instead of submitting; Shift+Enter/IME unchanged (see `## FE-018`).
**FE-019 (s064, committed `89f2cf0` + follow-up `ab47c38`, deployed):** — per-user **RSS feed** of finished
sessions (`rss/rss.ts` + `/rss/:token` public-by-token, `/api/rss/url` auth-gated); the URL shows in
Settings › Notifications with a copyable row/dialog; feed `<link>` honors the request Host (RFC-relative).
Also fixed 3 typecheck errors in the WIP (`Effect.gen`+`yield*` for the on-disk feed, `Global.Path.state`
instead of an unsatisfied `Global.Service`, `ServerAuth.Config.layer` on the route).
**FE-020 (s069, DEC-045 — committed `c1f1b58` + pushed, DEPLOYED in the s071 build):** — **every folder you
open is a project.** Engine records every opened directory in `project_directory` (including the shared
`global` project, which is where a directory without a git repository lands) and emits
`project.directories.updated`; the app loads those directories as a query and merges them into the
server-truth Home list, so a non-git folder picked in the selector now appears and is selectable on **every**
server section. Home `add` no longer runs `git init` on empty folders. Picker: absolute path in the text box,
suggestions driven by typing only, and confirming with nothing selected is no longer possible (it used to hand
the tree root `/` to the caller). See `## FE-020` + DEC-045.
**FE-021 (s070, DEC-047 — COMMITTED `5d6b47a` + PUSHED, NOT DEPLOYED):** — the "Thinking" row's elapsed
number becomes a **pair**: `· A / B` = *seconds since the last model output* / *seconds since the user prompt*, with
a localized tooltip that also prints the **absolute clock time** of the last output. New
`packages/app/src/pages/session/timeline/turn-activity.ts` (+9 unit tests): `at` = max of the server's own stamps
(assistant `created`/`completed`, tool `state.time.end ?? start`, `text`/`reasoning` `time.end ?? start`) and a
**client-observed** arrival time, because the server stamps a part when it is created and a streaming part keeps
its original `time.start` — so the old counter kept climbing during a healthy stream. The observation is a
fingerprint of the turn's parts (`part.text.length` included) compared against the previous value; a first version
using `on(…, { defer: true })` was an **infinite reactive loop** and was replaced (DEC-047 has the full trap list).
Rendering reuses the already-translated `ui.message.duration.seconds` / `.minutesSeconds`; the row is gated on
`B > 0` because `A` is legitimately `0` while the model streams. See `## FE-021` + DEC-047.
**Deployed** s071: `1.1.20260927065342` (pid 3613950) — **FE-020** (`c1f1b58`) **plus** the **DEV-menu utility
items** (DEC-046: the top-left DEV dropdown also offers Log out / Settings / Help, reusing the project page's
handlers + i18n keys). **Correction (s070):** the earlier note here claimed this binary also carries the parallel s070 WIP
(`turn-activity.ts` + timeline changes + all locales). It does **not** — the build started ~06:53 UTC and those
edits landed from ~07:00 UTC. Verified by grepping the binary and the served bundle: `session-turn-thinking-elapsed`
present, `session.thinking.elapsed` / `since the last model output` **absent**. See ide FU-082 / FU-085.
Previous: s068: `1.1.20260926102413` (pid 2999326) — the reviewed Settings v2 responsive nav
(`71c73a0`, see the s068 session record). Previous: s044 (0.0.0-mark-dev-202609161421, pid 3434396) —
FE-014/FE-015 (see above).
Previous: s029 (0.0.0-mark-dev-202609140012, pid 1557456) — **FE-013 picker rebuilt onto Zag.js
TreeView**: the buggy `@pierre/trees` web-component browse tree is replaced by a Solid-native
**Zag TreeView** (`@zag-js/solid`+`@zag-js/tree-view` 1.43.3, new `directory-tree-zag.tsx`, DEC-028).
Keeps the **path text-input** + autocomplete and the domain-layer **mid-level folder reveal**
(`C:\infrasys\java\jre\` → selects the middle `java` folder). Removed `@pierre/trees` + its test.
Previous: s028 (0.0.0-dev-202609130745) — **FE-011 slim live-reply fix**: the new
`<title> (N)` session now **registers client-side** (passes `location:{directory}` on create +
`serverSync().session.remember` + child store insert, mirroring the normal new-session `seed`) so the
seeded summary and fresh messages get a **live** assistant reply instead of only after a reload.
Previous: s027 (0.0.0-dev-202609130611) fixed the compact-summary-seeds-into-new-tab race
(poll-for-summary + loading/success toasts); s026 added **FE-012** right-click context menu
(Rename + Close Tab) on new/draft (unstarted) session tabs (0.0.0-dev-202609130518).
**FE-008** (fullscreen chat-height) and **FE-009** (drag-down action menu) are **code-complete but not yet
deployed** (FU-033/FU-034 — plan a single rebuild+deploy).
Web UI on http://192.168.1.249:4447/ (cwd `p003-opencode-fork`).
**Source:** `opencode/` — vendored clone (git-ignored as a nested repo; never commit it to the ide repo).

## Mission

A sandbox where we can patch opencode itself. Upstream build toolchain is **Bun 1.3+** (never assume it's
installed — bootstrapping the toolchain is part of this project).

## Deliverables map

- `config/` — build/env templates, configs for the fork
- `notes/` — design notes for planned modifications
- `scripts/` — build/bootstrap scripts (source-of-truth)
- `sessions/` — per-modification working notes

## FE-001 — Login landing page + persistent cookie auth (DONE, s004)

Replaces the raw Basic-auth prompt with a real login page served by the server:

- **Landing page** at `/login` (auto-shown when an unauthenticated browser hits **any** path — the 401
  "global failure path" renders the page, not the browser's Basic dialog).
- **Credentials** = the same server credentials (`OPENCODE_SERVER_USERNAME`/`OPENCODE_SERVER_PASSWORD`).
  Prompts only when a password is configured; no password → server stays open (unchanged).
- **Save auth forever** checkbox → long-lived cookie `oc_creds` (base64 `user:pass`, `Max-Age=1y`,
  `HttpOnly`, `SameSite=Lax`). Unchecked → session cookie. **Cookie carries into iOS *Add to Home Screen***
  shortcuts (WKWebView keeps cookies for the origin).
- **Redirect-back**: the requested path is preserved (`next`), and after a successful login the browser
  returns to it (open-redirect sanitized).
- **Log out** at `/logout` clears the cookie.
- Cookie → Basic header bridging on **both** gates: the web/UI router middleware *and* the JSON API layer.
- Files touched (in `opencode/`): `packages/opencode/src/server/shared/login.ts` (new), the auth middleware
  `packages/opencode/src/server/routes/instance/httpapi/middleware/authorization.ts`, routes
  `packages/opencode/src/server/routes/instance/httpapi/server.ts`, shared
  `packages/server/src/middleware/authorization.ts`.
- Designs + verification: `20-logs/sessions/2026-09-08_s004_login-landing-page.md`, DEC-011.

## FE-002 — Fix project-selector crash: `/file` + `/find/file` 500 (DONE, s004)

**Symptom:** clicking the project selector (next to the branch pill) did nothing — the DevTools console
showed `GET /find/file ... 500` and `GET /file?path=... 500`.
**Root cause:** pre-existing **dev-branch** bug (NOT the login work): `FileHttpApi.list`/`find` build a
per-location Effect layer (`LocationServiceMap.Service.get(Location.Ref.make(...))`) at request time and
the layer compile throws `TypeError: undefined is not an object (evaluating 'a.name')` → 500. The stock
stable build (:4445) proves the endpoints work there. Touches `packages/opencode/.../httpapi/handlers/file.ts`.
**Fix (in our fork, `file.ts`):** `Effect.catchCause` guard on both `list` and `findFile`; `list` falls
back to a **plain FSUtil listing** (real entries, no `.gitignore` filtering) so the picker still works
end-to-end. Typecheck + rebuild clean; endpoints return 200 with real data now.

## FE-003 — Foreground re-sync: mobile app auto-refreshes the open session when it returns to front (DONE, s006)

**Problem:** on the phone, OS power-saving suspends the backgrounded page; SSE updates emitted during
the gap are never replayed, so re-opening the app shows missing LLM responses until the user switches
tabs and back (tab switch remounts the session page → stale check → forced re-fetch).
**Fix (client-only, `packages/app`):**
- `context/server-sdk.tsx` — the SSE stream is now foreground-aware. It tracks `lastEventAt` (updated on
  every received event; both v1/v2 streams send `server.heartbeat` every 10 s, so silence > 20 s = dead
  stream). New `resume()`: healthy stream → no-op; dead/never-started → `stop()`+`start()`. Wired to
  `document.visibilitychange`→visible and `pageshow`(persisted). A fresh connection re-emits
  `server.connected`, which drives the **existing** connected-time refresh (session lists, statuses,
  bootstrap) — so the session list also self-heals on foreground.
- `pages/directory-layout.tsx` — `DirectoryDataProvider` force-syncs the open session on foreground:
  `session.sync(params.id, { force: true })` (same merge-safe path the tab switch uses; older history
  preserved by the existing `preserveUnfetched` logic).
- **Net effect:** lock phone → unlock → the current tab's content re-fetches once automatically; no tab
  switching. Desktop is unaffected (healthy streams are left alone; heartbeats keep them fresh).
- Files: `packages/app/src/context/server-sdk.tsx`, `packages/app/src/pages/directory-layout.tsx`,
  `packages/app/src/context/server-sdk.test.ts`. Design: DEC-013.
- Verified: typecheck clean; 726 unit + 41 browser tests pass; rebuilt binary `0.0.0-dev-202609081414`
  (app bundle `index-DRf549dE.js` confirmed live on :4447); SSE connected+heartbeat observed.
- **iOS field test still pending** (FU-022/FU-020): lock phone >30 s during a run, unlock, confirm missing
  messages appear without tab switching.

## FE-004 — Open-project uses the @pierre/trees folder explorer on mobile too (DONE, s007)

**Problem:** on the phone the open-project dialog was the v1 search-list (type-to-find); no folder
explorer. Desktop had the richer v2 dialog built on `@pierre/trees` (click folder to expand/drill down,
selection highlight); mobile fell back to v1 because the picker gated v2 on `platform === "desktop"`.
**Fix (client-only, `packages/app`):**
- `directory-picker.tsx` — v2 dialog used on **every** platform when the new layout is enabled.
- `dialog-select-directory-v2.tsx`:
  - Tree now **starts at the last opened project's folder** (`projects.forServer(key).last()`, the
    per-server `lastProject` store updated on navigation) — falls back to server dir / home.
  - **Tap-to-unhighlight:** capture-phase click on the tree container; tapping the highlighted row calls
    `item.deselect()` (+ stopPropagation) — gives the touch-only toggle the lib only supports via Ctrl/⌘-click.
  - "Select folder" button keeps its Windows-style logic (`selected || currentFolder`).
- `dialog-select-directory-v2.css` — ≤680px media query makes the picker dialog full-viewport (100dvh)
  via `:has(.directory-picker-v2)` so the 640×480 fixed size can't overflow a phone.
- **Net effect:** on the phone, open-project = a Windows-style folder explorer rooted at your last project;
  tap to drill down, tap again to un-highlight, "Select folder" opens the highlighted or the current folder.
- Files: `components/directory-picker.tsx`, `components/dialog-select-directory-v2.tsx` (+`.css`).
  Design: DEC-014. Component research: `@pierre/trees` (pierrecomputer/pierre, Apache-2.0) already in deps.
- Verified: typecheck clean; 726 unit + 41 browser tests pass; binary `0.0.0-dev-202609081709`
  (bundle `index-CYFDBbly.js`) live on :4447 (pid 2229139); auth+SSE intact.
- **iPhone field test still pending** (FU-023).

## Build recipe (VALIDATED — host is aarch64)

```bash
cd opencode && export PATH="$HOME/.bun/bin:$PATH"
bun install                         # OK — 2346 packages
bun ./packages/opencode/script/build.ts --single   # OK — smoke test passes
# binary: packages/opencode/dist/opencode-linux-arm64/bin/opencode
```

## Running the local build (web)

```bash
cd testing
# With OPENCODE_SERVER_PASSWORD set (recommended) -> login landing page active.
OPENCODE_SERVER_PASSWORD=<pw> setsid nohup ../opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode web --port 4447 --hostname 0.0.0.0 > web-4447.log 2>&1 < /dev/null &
# or: ../scripts/run-web.sh   (keeps whatever OPENCODE_SERVER_PASSWORD is in env)
```

- **URL:** host http://0.0.0.0:4447/, LAN http://192.168.1.249:4447/ (`hostname -I`).
- **Running instance (s004):** pid rec in `20-logs/command-log.md`, password = the one already exported in
  the login shell (`hahahaha`? verify), i.e. **the same credentials as the old :4445 instance**.
- **Security note:** `oc_creds` is the base64-encoded credential (readable if stolen, effective only when
  copied — http LAN). Same trust model as the Basic auth it replaces. Do not expose LAN ports to the internet.

## FE-006 — Session-list subtitle: last user prompt in the sidebar (DONE, s016–s017; deployed 0.0.0-dev-202609120259)

**Problem:** in the workspace sidebar, each session row shows only its title — no hint of what it was
about / where it left off.

**Fix (client-only, `packages/app`):** each session row now shows a one-line **last prompt** preview
under the title:
- `utils/session-last-prompt.ts` (new) — walks the session's messages newest-first, takes the newest
  **user** message with a real (non-synthetic/non-ignored) text part, normalizes whitespace.
- `pages/layout/sidebar-items.tsx` — `SessionItem` computes the preview via a reactive memo off the
  existing message store; `SessionRow` renders the subtitle (hidden for `dense` rows) and enriches the
  row tooltip with `title\nprompt`.
- `pages/layout.tsx` — **bulk async prefetch**: when the session list renders, ALL visible sessions are
  queued for a small prefetch (20 messages each, ≤25/folder, 2 concurrent), so every listed row gets a
  subtitle shortly after open; hover still upgrades a session to full (200) history. Queue items now
  carry `{ id, limit, keep }`.
- **Home Sessions tab (FU-031):** same `sessionLastPrompt` extraction now backs the starting screen's
  session table — each row shows the real last user prompt under the title (per-row preview prefetch,
  20 msgs, 3 concurrent, in `home-sessions-table-controller.tsx`). No more `session.title` proxy.
- No server/DB/API change: relies on the existing session **prefetch** path already filling the message
  store for listed sessions.

**Verify:** `bun run typecheck` ✅, `bun run test:unit` ✅ (737 pass). **Deployed:** 0.0.0-dev-202609120259
(pid 248812), served entry `index-DhhfqPa8.js` contains `home-session-row-prompt` + `lastPrompt`.

**Notes:** `sessions/fe-006-session-list-last-prompt.md`

## FE-007 — Home Sessions-tab row: mobile-first multi-line card (DONE, s018; deployed 0.0.0-dev-202609120534)

**Problem:** the starting screen's session row was a one-line strip — fixed project column (112–160px)
ate half a phone's width, and title/prompt were single-line truncated so long prompts vanished.

**Fix (client-only, `packages/app`):** `pages/home/home-sessions-table.tsx` `HomeSessionTableRow`
redesigned as a 3-line stacked card (`items-start`):
1. **Title** `flex-1` clamped to **2 lines** + **relative time top-right** (no fixed 64px reserved).
2. **Project name** (was fixed-width column) → small muted line under the title with the v2 **folder**
   icon; single-line truncate.
3. **Last prompt** (FE-006) → third line, **2-line clamp**, only when present.
Multi-line via inline `-webkit-line-clamp:2` / `-webkit-box-orient:vertical` (pattern already used in
the question dock).

**Verify:** `bun run typecheck` ✅, `bun x oxlint` ✅ (0/0), `bun run test:unit` ✅ (737 pass). Built
with pinned bun **1.3.14** (DEC-015) → `0.0.0-dev-202609120534` (pid 305738). Binary grep confirms new
markup shipped.

**Notes:** `sessions/fe-007-home-sessions-row.md`

## FE-009 — Drag-down action menu on the agent chat tab bar (DONE, s020; not yet deployed — FU-034)

**Problem:** on mobile there was no quick, thumb-reachable way to reload the app or log out from the chat
view — you had to leave the session flow.

**Fix (client-only, `packages/app`):** drag **down** from the top agent-chat tab-bar background to open a
small action menu.
1. **Reload** — `window.location.reload()`; new `common.reload` i18n key added to all 62 dict files.
2. **Logout** — reuses `sidebar.logout`/`sidebar.logoutConfirm` (FE-001 flow): `window.confirm` → `/logout`.

Extensible by design: `DragDownMenu` takes a `DragDownAction[]` (`id`, `labelKey`, `icon` (IconV2),
`onSelect`, optional `confirmKey`) — adding an action is one array entry in `titlebar-tab-strip.tsx`.

Key engineering:

- **Gesture safety:** pure pull state machine (`drag-down-gesture.ts`) arms only on **downward dominance**
  (`dy>10 && dy>1.5×|dx|`) from **strip background** (skips tabs/buttons/links), so it never fights the
  @dnd-kit horizontal tab drag/reorder.
- **Styling reuse:** v2 menu CSS via `data-component="menu-v2-content"` / `"menu-v2-item"` /
  `data-slot="menu-v2-item-content"` (no Kobalte anchor).
- **CSS traps solved:** icons in `item-content` (indicator slot hides `svg` unless `[data-checked]`); outer
  positioning div keeps the `-translate-x-1/2` off the `menu-v2-content` surface so it can't clash with the
  `menu-v2-in` scale animation; menu flips above on low viewports.

**Verify:** `tsgo -b` clean; unit 11+11+11 green; `bun run build` (production vite) ✅. Deploy pending FU-034.
**Notes:** `sessions/fe-009-drag-down-action-menu.md`

## FE-012 — Right-click context menu on new/draft session tabs (DONE, s026)

**Problem:** the native right-click context menu (**Rename** + **Close Tab**) existed only on started
chat-session tabs (`TabNavItem`); new/draft tabs (`DraftTabItem`, session not yet started) had no
menu at all.

**Fix (client-only, `packages/app`):** give `DraftTabItem` the same `MenuV2.Context` (Kobalte
ContextMenu) with the two items.
- **Close Tab** → existing `onClose` (flush through the s021 close-confirm dialog).
- **Rename** → inline contenteditable title editing (Enter saves, Esc/blur cancels, mirrored from
  `TabNavItem`); persisted per-draft via the new `tabs.rememberDraftTitle` →
  `TabInfo[tabKey].title`. The tab shows the custom name instead of the "New session" fallback;
  clearing it restores the fallback.

**Key engineering:**
- Draft title read from `tabs.info[id]?.title` in `titlebar-tab-strip.tsx` (fallback
  `command.session.new`); `onRename` threaded `DraftTabSlot → DraftTabItem`.
- `data-editing` + `select-none`/`select-text` gating mirrors `TabNavItem` so drag/reorder/preview
  never start while renaming; Kobalte ContextMenu trigger keeps the `div[role=link]` fix from s025
  (no `href` → iOS long-press stays JS-driven).
- Draft rename keys off `draft:<draftID>` — the same key `removeInfo`/promote cleanup already use.

**Verify:** `tsgo -b` clean; `tabs.test.ts` 12/12 green; full build
`0.0.0-dev-202609130518`.
**Notes:** `sessions/fe-012-draft-tab-context-menu.md` (FU-041 = on-device check)

## FE-014 — DEV titlebar button → dropdown menu (DONE code, not yet deployed)

**Problem:** the top-left **DEV** pill (blue bg, dev channel only) previously toggled debug tools on
click with no discoverable path back to Home or a refresh action.

**Fix (client-only, `packages/app`, `components/titlebar.tsx`):** `ChannelIndicator`'s DEV button is now a
`DropdownMenu` trigger (`@opencode-ai/ui/dropdown-menu`, Kobalte) with three items:
1. **Home page** — `navigate("/")` (home route).
2. **Refresh** — `window.location.reload()`.
3. **Debug tools** — preserves the previous `props.debugTools.toggle` behaviour.

Existing menu styling/tokens reused via the shared `DropdownMenu` component; typecheck (`bunx turbo
typecheck --filter=@opencode-ai/app`) clean.

**Verify:** manual — click DEV in the titlebar, confirm the menu opens and each item behaves (Home
navigates, Refresh reloads, Debug tools toggles).

## FE-017 — Compact-and-new-session tab lifecycle (DONE, s059/s060; committed `4b21d04`)

When using "Compact and start a new session with this summary" in an agentic chat
(`session.slim`, `slimSession()` in `packages/app/src/pages/session/timeline/message-timeline.tsx`),
the fresh session tab now:
1. **sits directly after the original tab** (reordered next to it),
2. the **original session is renamed to `<title> [ended]`** (server-side, guarded vs. double suffix),
3. the **original tab is closed** so the new tab occupies its exact slot.

Impl: module-level `rearrangeTabsAfterSlim()` — registers the new tab (idempotent with the titlebar's
route-change add), polls ≤2s for the Solid `startTransition` commit, uses existing `tabs.reorder` /
`tabs.closeTab`, and renames the session via `sdk.api.session.rename`. The session (not just the tab
info) is renamed because the tab title renders from `TabNavItem`'s `session().title ?? fallback`.

**Verify:** typecheck (`bun turbo typecheck` 30/30) ✅, `oxlint` 0 err ✅, `vite build` ✅. Manual: slim a
session, confirm the new tab appears immediately after and the previous one disappears renamed `[ended]`.

## FE-018 — Mobile touch: Enter = newline, not submit (DONE, s060; committed `4b21d04`)

In `packages/app/src/components/prompt-input.tsx`:

- Added SSR-safe `isTouchDevice()` helper: true when `window.matchMedia("(pointer: coarse)").matches` OR
  `navigator.maxTouchPoints > 0`.
- In `handleKeyDown`, the plain-Enter submit branch now short-circuits on touch devices: inserts `"\n"`
  via the existing `addPart` helper (same path as Shift+Enter) and returns, so the message is **not**
  submitted. Shift+Enter and IME behavior unchanged. Submit on mobile is done via the send button.

**Verify:** typecheck (`tsgo -b`) ✅, app unit tests 750/750 ✅. Manual: on a phone/tablet, plain Enter inserts
a newline + keeps the keyboard open; desktop Enter still submits.

## FE-020 — Every folder you open is a project (CODE COMPLETE + REVIEWED, NOT BUILT — s069, DEC-045)

**Bug:** Home ▸ Projects ▸ *Add project* + a folder **without a git repository** → the dialog closes and
nothing changes. Measured on :4447: only `file.list` + `project/current?directory=X` fire, `project/current`
returns `id: "global"`, the project list is unchanged, the session list goes empty. A *git* folder works
(a prepared folder was registered instantly).

**Why:** a project is a **git identity** — remote-url hash → id cached in `<git>/opencode` → first root commit
sha (a prepared folder's id was literally its commit sha). A directory with no repo resolves to the shared
`global` project, and `Project.saveProjectDirectory` returned early for it, so the folder was recorded
nowhere. Since s043 the Home list is server truth, so there was no row to render. `git init` does not help: a
repo with no commits still resolves to `global`, and `initGit` even repoints the global project's own
`worktree`. Details in `40-knowledge/opencode-server-api.md` → "Projects, directories and plain folders".

**Change (11 files + 1 test file, 2 new):**
- `opencode/src/project/project.ts` — `saveProjectDirectory` records the global project too and reports
  whether a row was created; `fromDirectory` emits `project.directories.updated` on the global bus when so,
  and records **the directory that was opened**, not `ProjectV2.resolve`'s output: a repository-less directory
  resolves to `directory: "/"`, so passing the resolved value would remember the filesystem root instead of
  the folder (caught in review — the first version of this change had exactly that bug, and the new test in
  `opencode/test/project/project.test.ts` fails against it).
- `core/src/project/directories.ts` — re-exports the schema's directories `Event` on the module namespace
  (publishing from core with an `EventV2.node` dep is a module-init cycle — do not retry).
- `app/.../global-sync/bootstrap.ts` — `loadProjectFoldersQuery` (`GET /project/global/directories`); a
  failure degrades to an empty list so an older server still boots (the `catch` sits **outside** `retry`, so
  a transient failure is actually retried).
- `app/.../context/server-sync.tsx` — `folder` is a **getter over the `[scope, "project-folder"]` query**
  (same shape as `path`/`provider`/`config`), so every refetch — reconnect, the directories event, an
  explicit fetch after `add` — updates it without a separate store write.
- `app/.../pages/home/home-project-folders.ts` (new) — `mergeProjectFolders()` / `isPlainFolder()`, deduped
  against project worktrees *and* sandboxes by `pathKey`.
- `app/.../pages/home/home-controller.ts` — one `projectsFor(data)` feeds both the focused list and
  **every** server section (`forServer` used to return the per-device store, so a remote server's plain
  folders were missing); `select` accepts a plain folder; `add` drops `initGit` and refetches the folder list.
- `app/.../pages/home/home-projects-view.tsx` — "Edit project" hidden for id-less folder rows.
- Picker: `dialog-select-directory-v2.tsx` + `directory-picker-domain.ts` — absolute path in the text box,
  suggestions driven by a `searchInput` signal (typing only), directory-mode `result()` with no implicit root
  fallback, `pickerRootSelection()` so a suggestion click is confirmable.

**Verify:** root `bun typecheck` (the pre-push gate) 30/30 ✅ · app unit 755/1 (the 1 = pre-existing i18n
parity, FU-076) ✅ · `test/project/` 89/0 (the new plain-folder test fails against the pre-fix line) ✅ ·
`test/server/` 2 fails, both pre-existing (re-proven with the change stashed) ✅ · core 1 pre-existing fail ✅ ·
oxlint 0 on the changed files ✅. **Review pass (third, same day) fixed 5 more findings:** the recorded directory is now validated with
`fs.isDir` (a stale tab / typo / deleted path used to leave a permanent, unopenable row in the list), the
recently-closed filter also accepts plain folders, `pickerMode().result` lost its unread `root`
parameter, `isPlainFolder` is now the guard the view actually uses, and `pickerRootSelection` moved next
to `pickerMode`. **Committed + pushed to `origin/dev`; still not built/deployed (FU-079)** — build + live
verification come next.

## FE-021 — "Thinking" shows last-model-output / since-your-prompt (COMMITTED `5d6b47a`, NOT DEPLOYED — s070, DEC-047)

**Ask:** the Thinking row already showed an elapsed time (s048 / FU-055), but it answered the wrong
question. Make it a pair so the user can tell **when the model last produced something** and **how long
the prompt has been running**:

```
🌀 Thinking · 12s / 1m 45s
             │    └── B: since your prompt
             └─────── A: since the last model output
```

Hover the pair for `12s since the last model output (14:32:05) · 1m 45s since your prompt` (the absolute
clock time is the "when" the mobile numbers cannot give you).

**Why the old number was wrong:** its base was `lastAssistantMessage.time.created` — *the start of the
current LLM step*, not the last output. Worse, a streaming `text`/`reasoning` part keeps its original
`time.start` while tokens keep arriving, so the counter climbed steadily through a perfectly healthy
stream. The server can only stamp a part when it is *created*; the client is the one that sees each
`message.part.delta` grow `part.text` in the store (`context/server-session.ts:1190`).

**What was built**

| File | Change |
|---|---|
| `pages/session/timeline/turn-activity.ts` | **new.** `latestTurnActivity({ messages, parts, observed })` → `{ at, key }`. `at` = max(server stamps ∪ client-observed arrival). `key` = turn fingerprint including each part's `text.length`, so an in-flight update is detectable. |
| `pages/session/timeline/turn-activity.test.ts` | **new.** 9 cases: empty turn, message-only, tool end > start, running tool start, pending tool (no `time`), latest part wins, key changes while streaming / on tool start+finish, observed wins over a stale stamp but not a newer one. |
| `pages/session/timeline/message-timeline.tsx` | `TimelineThinkingRow` takes `activityAt` + `promptAt` (was one `baseTime`) and renders `· A / B` + the tooltip; the `Thinking` case owns the fingerprint-vs-previous `createEffect` that stamps arrivals. |
| `i18n/en.ts` + all 61 locales | one new key `session.thinking.elapsed`; the two duration formats reuse the **already-translated** `ui.message.duration.seconds` / `.minutesSeconds`. |

**Three traps, all in DEC-047:** `on()` does not dedupe the single-dependency form, so the first version
looped forever; the row must be gated on `B > 0` (gating on `A > 0` makes it flicker out on every delta
while the model streams, because `A = 0` is the healthy case); and `ToolStatePending` carries no `time`.

**Side effect — FU-076 closed:** the 6 `settings.general.notifications.rss.*` keys that existed only in
`en.ts` + `tk.ts` were added to the other 60 locales with the English source copy (the FU-026 pattern), so
`src/i18n` parity is now **13/13 green** and the app unit suite is **765/765**.

**Gates:** root `bun turbo typecheck` 30/30 ✅ · app unit 765/765 (was 755/1) ✅ · `e2e/performance/unit`
43/43 ✅ · oxlint `packages/app/src` 822 warnings / **0 errors**, identical to the pre-change baseline ✅ ·
`vite build` ✅ (bundle contains `session.thinking.elapsed` + `session-turn-thinking-elapsed`) · prettier
`--check` clean on every touched file ✅ (this also fixed one pre-existing formatting violation in
`message-timeline.tsx`, the `session.compact` member chain).

**Committed `5d6b47a` + pushed `origin/dev`** (pre-push typecheck 30/30), staged alone so the parallel
s071 DEV-menu WIP stayed out. **Deployed** 07:28 UTC by the user: build `1.1.20260927072837`, **pid 3654762**, bundle
`assets/index-BFF1n-Mg.js` — probed and confirmed to contain `session.thinking.elapsed` +
`since the last model output`; health OK, FE-001 auth intact. Awaiting the user's visual check of the two
numbers (FU-085).

## Vendored clone state

- Cloned: 2026-09-08 (s003) from `https://github.com/anomalyco/opencode.git`
- HEAD at clone: `ecbc6ccac85b3e8087b6445e584318419b9e2b34` (branch `dev`, shallow, 2026-09-08)
- **Forked (s003):** `nkyang10/opencode` (fork of anomalyco/opencode, public). Remotes on the vendored clone:
  - `origin`  → https://github.com/nkyang10/opencode.git (our fork — push here)
  - `upstream` → https://github.com/anomalyco/opencode.git (original — pull latest from here)
- Note: shallow clone (`--depth 1`); consider `git fetch --unshallow` before first push/PR.

## References

- Decisions: DEC-010 (fork project), DEC-011 (FE-001 login/cookie design), 2026-09-08
- Follow-ups: FU-018 (first modification) ✅ done via FE-001; FU-020 (user verify on iOS + iterate);
  FU-033/FU-034 (FE-008 + FE-009 deploy, single rebuild)
- Runtime notes: `notes/build-runtime.md`
