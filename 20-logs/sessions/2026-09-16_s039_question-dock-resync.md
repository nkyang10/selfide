# Session s039 — FE-003 gap: on-foreground question-dock (decision dialog) re-sync

- **Date:** 2026-09-16 (UTC)
- **Session:** s039
- **Focus:** p003 fork — foreground re-sync (FE-003) did not refresh the session's pending **question/decision dock**.

## Problem
When the web UI resumes from background to foreground, FE-003 force-syncs the open session's
**messages** (`session.sync(id, {force:true})`) and restarts the SSE stream if silent > 20 s. But the
decision dialog (`SessionQuestionDock`) reads from the sync store's `data.question`, which is only
mutated by **live SSE events** (`question.asked/replied/rejected`, `server-session.ts`) or a **full
bootstrap** (which only runs on a fresh `server.connected`). Neither the force-sync path nor a still-alive
stream refreshes it — so if the agent asked a question while the phone was suspended, the decision dock
stayed empty/stale on return.

## Fix (client-only, `packages/app`)
- `context/directory-sync.ts`:
  - Added exported pure helper `sessionPendingQuestions(questions, sessionID)` — filters to the session and
    sorts by id (used by the tab-switch merge-style reconcile).
  - Added `session.syncQuestions(sessionID)` on the dir-sync session object. v1/v2 aware: v1 via
    `serverSDK.client.question.list()` (global, filtered by sessionID); v2 via
    `serverSDK.api.question.request.list({ location: { directory } })` (also filtered). Writes the result
    back into the question store with `set("question", sessionID, reconcile(pending))` — overwriting the
    array so stale entries for the session are dropped, same merge-safe path the tab switch / bootstrap use.
- `pages/directory-layout.tsx`:
  - The `foreground()` handler (visibilitychange→visible / pageshow persisted) now also calls
    `sync().session.syncQuestions(id)` alongside the existing force-sync, so the decision dock self-heals.

## Verification
- New unit test `context/directory-sync.test.ts` (`sessionPendingQuestions`): keeps session's items only,
  sorts by id, drops id-less and undefined input. 2/2 pass.
- `bun turbo typecheck` (@opencode-ai/app): pass.
- `oxlint` on the 3 touched files: 0 errors (8 pre-existing warnings, unchanged).
- Pre-existing test-harness failures (solid-js `use` export from `.../web/dist/server.js`) confirmed
  present on pristine files via git stash — unrelated to this change (16/19 surrounding tests pass).

## Evidence
- Files changed: `packages/app/src/context/directory-sync.ts`, `packages/app/src/context/directory-sync.test.ts`,
  `packages/app/src/pages/directory-layout.tsx`.
- Decision: see `40-knowledge/decisions-log.md` (DEC-041 below / appended row).
- Follow-up: FU-050 (deploy + on-device retest).

## Outcome / follow-up
- Code complete + tested; **not yet built/deployed** (awaiting user go-ahead, consistent with s037/s038 flow).
- FU-050: build via `scripts/build-linux.sh` (bun 1.3.14 only, FU-039) + restart :4447 + iPhone test: lock
  >30 s while the agent has an unanswered question → unlock → decision dock must appear without a tab switch.
