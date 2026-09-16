# Session s043 — Home project/session list server-side (fresh-device fix)

**Date:** 2026-09-16 UTC
**Trigger:** User reported that on a *second* device hitting `:4447`, `/api/session` AJAX returns all
sessions but the Home "starting project" session list never renders.
**Scope:** `50-projects/p003-opencode-fork/opencode/packages/app`

## Diagnosis (confirmed by curl against live :4447)

- `GET /api/session` (v2 list) returns `{data: [37 sessions], cursor}` — good data, all devices.
- Home sessions list in the UI is gated by the per-**device** localStorage open-projects store:

  - `pages/home/home-controller.ts` `projects` memo was
    `focusedServerCtx()?.projects.list() ?? layout.projects.list()`
    → `createServerProjects().current()` = `input.store.projects[scope] ?? []`
    (`context/server.ts:85`) — persisted via `Persist.server(...)` = localStorage.
  - `pages/home/home-sessions-controller.tsx` `projectDirectories` derived from that, and
    `buildHomeSessionRecords` filters `directories.has(pathKey(session.directory))`
    (`home-sessions-controller.tsx` old line ~258).
  - Fresh device → localStorage empty → directory set empty → **all 37 sessions filtered out** even
    though the AJAX data was perfect. First device worked only because its localStorage held the
    `/home/mark/Desktop/ide` project.

## Fix

- `home-controller.ts`: `projects` memo now sourced from **server truth**
  `focusedSync().data.project` (`/project`) mapped to `LocalProject` (`expanded:false`). This one seam
  feeds Home sessions list, sessions-table controller, selected/new-session project resolution and the
  left "starting project" panel — all server-side, identical across devices.
- `home-controller.ts` `select`: guard no longer checks the deprecated local open-projects store; it
  accepts any directory present in the server project list (otherwise clicking a project on a fresh
  device was a no-op).
- Extracted pure helpers to `pages/home/home-session-records.ts`
  (`buildHomeSessionRecords`, `projectDirectories`, `homeSessionSearchKey`) so the record builder is
  unit-testable without the session-ui markdown worker import; controller re-exports
  `HomeSessionRecord` + `homeSessionSearchKey` to keep external importers working.

## Tests / checks

- New `pages/home/home-sessions-controller.test.ts` (2 tests): server-fed project list maps sessions to
  records; empty project list (the old fresh-device failure mode) yields zero records.
- `bun run typecheck` (tsgo -b): pass. `oxlint` on changed files: 0 warnings/0 errors.
- `bun test` on `pages/home` + helpers: 29 pass / 0 fail.
- Known pre-existing (NOT this change): `global-sync/bootstrap.test.ts` + `home-session-index.test.ts`
  fail with `Export named 'QueryClient' not found` — bun/`@tanstack/solid-query` module-resolution
  issue under the `solid` test condition. Unrelated to this task.

## Consequences / follow-ups

- **Behavior change:** Home "starting project" panel now lists ALL server-known projects, not the
  per-device "opened" set. Local-store `close` / drag-`move` on the panel are now effectively no-ops
  visually (they still write the deprecated store). This is the intended direction per user:
  *"at the end rip off localStorage for the project folder list; keep only session tabs in localStorage."*
- FU-052: full localStorage rip-out for project folder list (drop `Persist.server("projects")` usage /
  close-move semantics; decide server-side hide/order model). Pending design.

## Deployment (FU-053, same session)
- Built `0.0.0-mark-dev-202609160919` (bun 1.3.14), killed old PID 3251919, relaunched :4447 → **PID 3285617**.
- Served bundle now `index-DhYvOjPz.js` (was `index-CcDN76iX.js`) → new build confirmed live; `/api/session` + `/project` 200; no-cookie request → 401. Client-side render fix cannot be curl-verified — **awaiting user's fresh-browser/device visual confirm**.

## Evidence
- Live curl: `/api/session?limit=5000&order=desc` → 200 `{data:[37],cursor}`; `/project` → ide + global.
- `git -C 50-projects/p003-opencode-fork/opencode diff --stat packages/app/src/pages/home/`
