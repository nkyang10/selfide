# p003 — opencode fork: local clone, modifications, own Linux build

**Project:** Vendor the **opencode** source (`github.com/anomalyco/opencode`, MIT), modify it, and build our own
Linux binary instead of relying on prebuilt releases.
**Status:** 🟢 MODIFIED + SELF-BUILT + SERVING — **FE-001** cookie-auth login, **FE-002** project
selector fix, **FE-003** foreground re-sync, **FE-004** folder explorer on mobile, **FE-006** session-list
last-prompt subtitle, **FE-007** home Sessions-tab row → mobile-first multi-line card.
**Deployed** s029: 0.0.0-mark-dev-202609140012 (pid 1557456) — **FE-013 picker rebuilt onto Zag.js
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
