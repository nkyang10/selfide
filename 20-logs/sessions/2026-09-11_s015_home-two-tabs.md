# s015 — Home page: 2-tab layout (Projects | Sessions)

**Date:** 2026-09-11 (UTC)
**Status:** DONE — DEPLOYED as `0.0.0-dev-202609111028` (v3); earlier `0.0.0-dev-202609111011` (v2), `0.0.0-dev-202609110943` (v1)
**Project:** p003-opencode-fork (WebUI)
**Request:** Restructure the `/home` landing into 2 tabs, and make the session list cross-folder —

- **Tab 1 "Projects"**: original folder-selection + project-select flow (keep original functionality).
- **Tab 2 "Sessions"**: a table of **all project sessions gathered across ALL folders/projects, sorted by
  last prompt** (most recent first). Each row = project avatar (with unread dot) + project name + session
  title (the last prompt, **bold when unread**) + relative last-access time.

> Note: an earlier draft of tab 2 listed *projects* (`home-projects-list.tsx`); the user clarified they
> want *sessions*. The project list was removed/replaced by the sessions table.

### v2 change (which-folder step removed)
The user's follow-up: list **all folders'** sessions in one list and drop the need to pre-select a
folder before picking a recent session. Deployed as `0.0.0-dev-202609111011`:

### v3 change (decouple the two tabs — PROJECTS TAB PRESERVED)
User: "make sure they are not using the same element and function — I want to preserve everything in the
Projects tab." v2 had mutated the SHARED `createHomeSessionsController` (used by BOTH the Projects sidebar and
the Sessions table), so the Projects tab changed too. v3 fully decouples:

- **Reverted** the shared controller to original: `projectDirectories` filtered by the selected project,
  `showProjectName: () => !home.project.selected()`. The Projects tab is behavior-identical to pre-s015.
- **New dedicated `createHomeSessionsTableController`** (`home-sessions-table-controller.tsx`): its own
  query (cross-folder, all projects' worktrees+sandboxes), its own `records` build, its own `open`
  (auto-resolves project by directory + `ctx.projects.open` + `tabs.addSessionTab`), its own `isOpenTab`
  and `server`. It shares no controller instance/state with the sidebar.
- `home.tsx`: Sessions tab renders `HomeSessionsTable` from `tableSessions` only.
  Deployed as `0.0.0-dev-202609111028`.

## Design decisions (DEC-018, revised)
- **Placement:** top `SegmentedControlV2` on the home page (`pages/home.tsx`). Reuses existing
  `@opencode-ai/ui/v2/segmented-control-v2`.
- **No new i18n keys:** reuse `home.projects` ("Projects") and `home.sessions.search.sessions` ("Sessions")
  to avoid touching 66 locale files (i18n parity test).
- **Default tab = "Projects"** (the original view) so existing users see no change on first load. **v2: default tab
  = "Sessions"** — the cross-folder recent-sessions list is the primary surface now (folder selection was the
  friction the user wanted gone).
- **Tab-2 data source (v3):** the table uses its own controller `createHomeSessionsTableController`
  (`home-sessions-table-controller.tsx`) — **not** the sidebar's `sessions` controller. It has its own query
  (`loadHomeSessionIndex` across ALL projects' worktrees+sandboxes), its own `records` build
  (`HomeSessionRecord[]` up to 64), and its own `open`/`isOpenTab`/`server`. Sorted by
  `session.time.updated ?? created` descending. v2 had instead mutated the shared controller, which changed the
  Projects sidebar too; v3 reverted the shared controller to original so the Projects tab is preserved exactly.
- **Unread / bold:** stateless `HomeSessionStatusController` (render-prop over the global avatar store) +
  `SessionTabAvatarView` (the `ProjectAvatar` `unread` prop draws the dot). Session title and project name go
  bold when unread. These are stateless presentational pieces (no tab logic), so sharing them doesn't affect the
  Projects tab.
- **Row click (v3):** `tableSessions.session.open(record.session, options)` — the table controller's own open:
  resolves the project from `session.directory`, `ctx.projects.open(directory)` (auto-selects the folder), then
  `tabs.addSessionTab` + `tabs.select`.

## Deliverables
- [x] Modify `pages/home.tsx`: SegmentedControlV2 tab bar + conditional render (Projects grid | Sessions table)
- [x] New `pages/home/home-sessions-table.tsx`: tab-2 sessions table (avatar+dot, project name, last prompt/bold, relative last access)
- [x] Remove obsolete `home-projects-list.tsx` (superseded by sessions table)
- [x] **v2:** cross-folder sessions list; default tab = Sessions (this was reverted-partially by v3)
- [x] **v3:** new dedicated `home-sessions-table-controller.tsx` (own query/records/open/isOpenTab); shared controller restored to original → Projects tab fully preserved
- [x] Typecheck (pass), i18n parity (5 pass), full unit suite (730 pass), vite build (clean)
- [x] Full single-binary build (`build-linux.sh`, bun 1.3.14) → `0.0.0-dev-202609111028`
- [x] Redeploy :4447 (pid 3967592); login 200; unauth `/` 401 (FE-001 intact); served entry
  `index-CAzbSeqL.js` contains `home-session-table-row`; log clean

## Evidence
- Served entry JS (v3): `/assets/index-CAzbSeqL.js` — `grep -c home-session-table-row` = 1
- Live: `http://192.168.1.249:4447/` (pid 3967592), binary `0.0.0-dev-202609111028` (v3).
  v2 was pid 3965756 `0.0.0-dev-202609111011`; v1 was pid 3936444 `0.0.0-dev-202609110943`

## Follow-ups
- FU-028: visual check on iPhone (tabs + unread dot + bold + column truncation) — user to confirm on device.
- FU-029: exact last-prompt text currently = `session.title` proxy; raw last user message needs per-session message sync.
