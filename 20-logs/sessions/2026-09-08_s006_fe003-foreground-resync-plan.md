# s006 — FE-003 (proposed): foreground re-sync for mobile web UI

- **Date:** 2026-09-08 (UTC)
- **Project:** p003-opencode-fork (app = `packages/app`, served by `opencode web` on :4447)
- **Type:** research + plan + **implementation (DONE)**
- **Status:** implemented, tested, built, **live on :4447** (pid 1949123); iOS field test pending (user)

## Request (user, verbatim intent)

When viewing the web UI normally, LLM results stream in fine. On the phone, the OS power-saving
freezes the backgrounded page so SSE updates are missed. Re-opening the app does **not** show the
missing responses; the user must switch between two tabs and back, which re-fetches. Request: when the
page returns to foreground, automatically re-fetch the current tab's content once. Investigate the code
first, then plan.

## Code findings (where things live)

| Area | File | Fact |
|---|---|---|
| SSE stream lifecycle | `packages/app/src/context/server-sdk.tsx` | One stream per server, started by `server-sync.tsx` `onMount`. `pagehide` → `stop()`; `pageshow` persisted → `start()` (line 325-328). `start()` is a no-op while `started===true` — a dead-but-unaborted connection is never replaced on app-switch foreground. |
| Stream health signal | `packages/opencode/.../handlers/event.ts` + `handlers/global.ts` | **Both v1 and v2 SSE streams send `server.heartbeat` every 10 s.** A healthy stream is therefore never silent >10 s → "no event for 20 s" is a reliable dead-stream test. |
| Connected-time refresh | `packages/app/src/context/server-sync.tsx` (lines 546-571) | On `server.connected` it pushes all active directories into the refresh queue (`bootstrapInstance`: session list, statuses, config) and refetches global bootstrap. **It does NOT re-fetch the open session's messages.** |
| Message store + refresh API | `packages/app/src/context/server-session.ts` | `sync(sessionID, {force:true})` re-fetches session info + latest message page and merges with cached/optimistic state (preserve/touched logic; covered by `server-session.test.ts`). `fresh(id, ttl)` = last-load timestamp check. |
| Why tab-switching "fixes" it | `packages/app/src/pages/session/timeline/model.ts` (lines 19-41) | Timeline model runs on (re)mount: `stale = cached && !fresh(id, 15_000)` → `sync(id, {force:true})`. Tab switch remounts the session page → stale → forced re-fetch. Foreground does not remount, so nothing re-fetches. |
| Open-session owner | `packages/app/src/pages/directory-layout.tsx` (`DirectoryDataProvider`, lines 45-51) | Mounted per session route with `params.id`; already calls `sync().session.sync(id)` on mount. Natural home for a foreground listener. |
| Rebuild | `packages/opencode/script/build.ts` | `bun ./packages/opencode/script/build.ts --single` builds `packages/app` and embeds its `dist/` into the binary. |

## Root cause

1. Mobile suspension freezes JS + network; SSE events emitted during the gap are **not replayed** by the server.
2. On return, the stream may be dead/hung and is never restarted on a plain app-switch (`visibilitychange`
   has no handler; `start()` is a no-op while `started`).
3. Even when the stream reconnects (`server.connected`), only the session *list*/statuses refresh — the
   **open session's messages** are only ever re-fetched on page remount (tab switch) via the stale check.

## Plan (FE-003) — two targeted changes in `packages/app`

### 1. `context/server-sdk.tsx` — foreground-aware stream resume
- Track `lastEventAt` (updated on every received event; heartbeats count).
- Add `resume()`: if stream is healthy (`started` and event within last 20 s) → no-op; else `stop()` +
  `start()`. A fresh connection re-emits `server.connected`, which drives the **existing** refresh path
  (session lists, statuses, bootstrap) for free.
- Wire: `visibilitychange` → visible → `resume()`; `pageshow` persisted → `resume()` (replaces `start()`).
  Keep `pagehide` → `stop()`.
- Update `server-sdk.test.ts` (replace `resumeStreamAfterPageShow` test with `resume` liveness tests).

### 2. `pages/directory-layout.tsx` — re-fetch the open session on foreground
- In `DirectoryDataProvider.onMount`: on `visibilitychange`→visible and `pageshow` persisted, if
  `params.id` is set → `void sync().session.sync(params.id, { force: true }).catch(() => {})`.
- Same mechanism the tab-switch uses; bounded request (latest message page; older history preserved by
  existing `preserveUnfetched` merge).

### Result
- Foreground → dead SSE replaced (heartbeat-based liveness, no needless reconnects while healthy).
- Foreground → current tab's session content re-fetched once (the user's ask).
- Foreground → session list / project / statuses update via existing `server.connected` path.
- Other open session tabs self-heal when switched to (existing stale check).

### Considered & rejected
- Service-worker/push buffering: much larger server + client change; iOS SW limits; overkill for the ask.
- Unconditional `stop()+start()` on every foreground: churns healthy desktop tabs; heartbeat liveness avoids it.
- Freshness-gated session re-fetch: the "always" re-fetch is one bounded request and matches tab-switch semantics; keep it simple (gate can be added later if it proves wasteful).

## Verification plan
1. `bun typecheck` in `packages/app`.
2. App unit tests: `bun test --conditions=solid --preload ./happydom.ts ./src/context/server-sdk.test.ts ./src/context/server-session.test.ts` (then broader `bun run test:unit` in package).
3. Rebuild binary: `bun ./packages/opencode/script/build.ts --single --skip-install`.
4. **Swap the running :4447 instance — requires explicit user confirmation** (live instance used by user's phone; vendored-repo AGENTS.md forbids the agent restarting server processes unilaterally).
5. iOS field test (ties into FU-020): open a session → prompt agent → lock phone → wait >30 s → unlock → missing messages appear **without** tab switching; busy→idle pill updates.

## Conventions / rules checked
- No new user-visible strings → no i18n keys needed.
- No session/timeline code modified (only calls existing `sync` API) → app AGENTS.md benchmark rule not triggered (noted anyway).
- SolidJS: no new state; plain listeners via existing `makeEventListener` pattern used elsewhere (`pages/layout.tsx:225`, `context/layout.tsx:424`).

## Implementation (DONE, user GO "開工")

### Code (2 files + 1 test)
- `context/server-sdk.tsx`:
  - Added `STREAM_STALE_MS = 20_000` + exported `shouldRestartStream(running, lastEventAt, now)`.
  - Track `lastEventAt = Date.now()` on every received SSE event (heartbeats count).
  - New `resume()`: no-op when stream healthy (`started` && event within 20 s); else `stop()`+`start()`.
  - `onMount` now wires `pageshow` (persisted) → `resume()` and `document.visibilitychange`→visible → `resume()`; `pagehide`→`stop()` kept.
- `pages/directory-layout.tsx` (`DirectoryDataProvider`): on `onMount`, `visibilitychange`→visible + `pageshow`(persisted) → if `params.id` set → `sync().session.sync(id, { force: true })` (catch-swallowed). Imports `onMount` + `makeEventListener`.
- `context/server-sdk.test.ts`: replaced `resumeStreamAfterPageShow` describe with `shouldRestartStream` (never-started / healthy / stale cases).

### Verification (all green)
- `bun typecheck` (packages/app) → clean.
- `bun test --conditions=solid --preload ./happydom.ts ./src/context/server-sdk.test.ts` → 12 pass.
- `bun test ... ./src/context/server-session.test.ts` → 74 pass.
- Full unit suite `./src` → **726 pass / 0 fail** (103 files).
- Browser suite `./test-browser` → **41 pass / 0 fail** (14 files).
- Rebuild: `bun ./packages/opencode/script/build.ts --single --skip-install` → smoke OK, `0.0.0-dev-202609081414`.
- Confirmed shipped bundle contains the change: `shouldRestartStream` + "Returning from background" present in `dist/assets/index-DRf549dE.js.map`; served `GET /` HTML references `index-DRf549dE.js`.

### Live instance swap (user confirmed "Yes, swap now")
- Killed old pid 1858134; started new binary (cwd `p003-opencode-fork`, `OPENCODE_SERVER_PASSWORD` preserved, port 4447, `--hostname 0.0.0.0`) → **new pid 1949123**.
- `GET /` with `opencode:hahahaha` → 200; body = new bundle. `/login` 200; `POST /logout` 200.
- SSE `GET /event` → `server.connected` then `server.heartbeat` (confirms the 10 s heartbeat liveness assumption).

### Pending (user)
- iOS field test: open a session → prompt agent → lock phone >30 s → unlock → missing messages appear **without** tab switching; busy→idle pill updates. Ties into FU-020 (pick permanent password).
