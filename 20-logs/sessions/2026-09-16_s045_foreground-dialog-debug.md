# Session s045 — Debug: foreground choice dialog not appearing (server-side debug logs)

**Date:** 2026-09-16 UTC
**Session:** s045
**Trigger:** User reported the FU-050/FE-003 resume chat + choice dialog enhancement "is not working": returning to foreground syncs chat history fine, but the pending question/choice dialog never appears. User asked to add debug logs ("previously u suggest the debug log submit to server side directly").

## Context
- The s039 `syncQuestions` fix was reverted in s042, then effectively re-introduced in later work (s043 wrap). `git log` in the fork shows `e64131e` (syncQuestions) plus later commits; `grep` confirms `syncQuestions` present in source and in the live bundle.
- Server-side debug sink already existed but was **gated behind `localStorage["foreground-debug"] === "1"`** (never set) → `.catch(debugLog(...))` swallowed every sync error silently.

## Verification performed (before edits)
- `curl` the running :4447 (login cookie): `/__debug?m=probe` → **204** (works, auth-gated).
- Served bundle `assets/index-f5wVUSxu.js` contained `syncQuestions`, `lyt:foreground`, `__debug` → feature WAS live.
- `GET /api/question/request` → `{"data":[]}` (no pending question at that moment — the API itself works).
- Root cause of invisibility: `debugLog` gate in `utils/foreground-debug.ts`; failures in `directory-sync.ts:syncQuestions` were caught and logged only via the gated util → invisible.

## Changes (fork working tree)
- `packages/app/src/utils/foreground-debug.ts`: **removed the localStorage gate** — `debugLog` now always posts `GET /__debug?m=<payload>` to the server sink (run-web.sh redirects server stdout → `testing/web-4447.log`). Old 8-line gate replaced.
- `packages/app/src/context/directory-sync.ts` (`syncQuestions`): added try/catch around the v1/v2 fetch; now logs protocol, total question count, matched pending count, first owned question id, and up to 5 other sessionIDs present.
- `packages/app/src/pages/directory-layout.tsx` (foreground): added `lyt:state` log right after each sync resolves — reports the current `data.question[sessionID]` store length + first id, so we can see if the store ever gets populated.
- `packages/app/src/pages/session/composer/session-composer-state.ts`: added `composer:questionRequest` log on the `questionRequest()` memo — reports `shown id=…` or `hidden` for the current session.
- `packages/app/src/pages/session/composer/session-question-dock.tsx`: added `dock:mounted` log on mount with request id + total question count.

## Build + deploy
- `bun run typecheck` (pinned tsgo): clean.
- `bash scripts/build-linux.sh` → `0.0.0-mark-dev-202609161500` then a second detach deploy produced `0.0.0-mark-dev-202609161501` (PID 3466112 on :4447).
- Verified live bundle `assets/index-BL0wOlIl.js`: `composer:questionRequest` ✓, `dock:mounted` ✓, `dir:syncQuestions` ✓, `foreground-debug` gate string **absent** ✓.
- Verified sink end-to-end: `curl /__debug?m=deploy_verify_23:02` → 204 and the line **appeared in `testing/web-4447.log`**.

## Next step for user
1. On the phone: open a session, let the agent ask a decision question, background the app for >20s, come back foreground (chat must appear).
2. We read `testing/web-4447.log` for the sequence:
   - `lyt:foreground begin id=…` → `dir:syncQuestions all=N pending=M …` → `composer:questionRequest shown/hidden` → `dock:mounted`.
   - This will pinpoint whether the fetch returns nothing (`all=0`), the session doesn't match (`pending=0`), the store isn't set, or the dialog refuses to render despite the store being set.

## ROOT CAUSE (from phone test log, t≈1789571291)
Sequence: `composer:questionRequest shown id=que_0aac23c2d001T9uQLBjnTwEsG0 q="What's your main goal?"` + `dock:mounted`
→ phone backgrounded (`visibilitychange hidden`) → on foreground:
```
lyt:foreground begin
dir:syncQuestions sessionID=… protocol=v1 all=0 pending=0 firstOwn=- otherSessions=
lyt:state questionStore=0 entries first=-
```
**The dialog was NOT missing — syncQuestions actively destroyed it.** Steps:
1. Protocol detected as **v1** (`/global/health` returns `healthy:true`; `detectServerProtocol` returns v1 on the legacy probe — see `utils/server-protocol.ts:28-29`). The v1 path runs `serverSDK.client.question.list()`.
2. That call was made **without any directory scope**. `serverSDK.client` is the v2 SDK (server-sdk.tsx builds it via `createSdkForServer`), which calls `GET /question` -> WorkspaceRoutingMiddleware routes on `directory`/`location` query → **missing scope → falls back to the server's default workspace = `testing/`** (the cwd run-web.sh starts in) which has no pending questions → returns `[]` (`all=0`).
3. `set("question", sessionID, reconcile(pending=[], {key:"id"}))` **reconcile([]) wiped** the store entry that the live SSE `question.asked` had already populated while backgrounded → `lyt:state questionStore=0` → `composer:questionRequest hidden` → dock unmounted.

Why chat syncs but dialog didn't: `session.sync()` v1 path uses `sdkFor(directory)` (directory-scoped), so messages preserved; only the question-path fetch lacked the scope.

## FIX (s045, deployed as 0.0.0-mark-dev-202609161521)
`context/directory-sync.ts` `syncQuestions`:
- **Always pass the directory scope**: v1 branch now calls `serverSDK.client.question.list({ directory })` (v2 SDK client accepts `{directory}`, which WorkspaceRoutingMiddleware uses to route to the right workspace); v2 branch unchanged (`{ location: { directory } }`).
- **Never wipe on failure**: introduced `fetched` flag; on a fetch error we keep `pending = undefined` and **skip the reconcile entirely** instead of `reconcile([])` killing a live dialog.
- Debug log now also reports `fetched=` so the retest triage stays easy.

Other logs added during triage: `lyt:state` store-length snapshot after each sync (`directory-layout.tsx`), `composer:questionRequest shown/hidden` (`session-composer-state.ts`), `dock:mounted` (`session-question-dock.tsx`). `foreground-debug.ts` gate removed (always posts to `/__debug`, server sink logs to `testing/web-4447.log`).

## Follow-ups
- FU-050: **retest after the s045 fix** — dialog must now survive foreground (phone test: lock >20 s with an unanswered question → unlock → dialog still visible).
