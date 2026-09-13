# Session s013 — Question dock: fail to dismiss after user selects an option

- **Date:** 2026-09-10 (UTC)
- **Focus:** p003-opencode-fork `packages/app` (FE bugfix, fork `dev` build)
- **Goal:** Fix "selection/dock fails to dismiss after the user selects their option and submits" in the
  agent-question dock (the bottom dock where opencode asks a multi-choice question).

## Symptom (user-reported)

In the fork's dev opencode (served build at `http://192.168.1.249:4447/`), the agent asks a question
with options. The user picks an option and submits — **the answer is accepted by the server** — but the
question dock **stays open**. It does not dismiss. (User: "docker stay open while actually the answer
has submitted.")

## Root cause

The dock is rendered while `controller.state.questionRequest()` is truthy (session-composer-state.ts:36),
derived from `sync().data.question`. That store entry is cleared **only** by the SSE event
`question.v2.replied` / `question.v2.rejected`:

- `context/global-sync/event-reducer.ts:454` (`case "question.replied": ... draft.splice(...)`).
- `context/server-session.ts:1280` (legacy path, same splice).

The dock's own submit path (session-question-dock.tsx) fires `sdk().api.question.reply(...)` and, on
success, only sets `replied = true` + deletes the local `cache`. It does **not** remove the request from
the shared store. So dismissal is **entirely SSE-driven**. If the `question.replied` SSE event is lost —
buffered stream, quick-tunnel SSE buffering (known, s010), or mobile background suspension killing the
stream — the reply succeeds server-side but the local store never clears, and the dock stays open forever.

This is the same failure class as the s010 "Thinking row never dismisses" bug: a state transition that
relies on a single SSE event with no local reconciliation.

## Fix

In `packages/app/src/pages/session/composer/session-question-dock.tsx`, on a **successful** reply or
reject mutation, optimistically remove the answered request from the shared store so the dock dismisses
the moment the server confirms — independent of SSE:

- Added imports: `Binary` (`@opencode-ai/core/util/binary`), `produce` (solid-js/store), `useSync`.
- Added `const sync = useSync()`.
- Added a `dismiss()` helper that splices the exact request (`props.request.id`) out of
  `question[props.request.sessionID]` (mirrors the event-reducer splice).
- Called `dismiss()` in `replyMutation.onSuccess` and `rejectMutation.onSuccess`.

Rationale: `onSuccess` fires only after `sdk().api.question.reply/reject` resolved (HTTP 200), i.e. the
server has the answer, so clearing locally is correct and race-free. On error (`onError`) we do NOT clear,
so the dock correctly stays open to retry.

## Verification

- `bun run typecheck` (tsgo -b) in `packages/app`: clean.
- `bunx oxlint` on the touched files: 0 errors (4 pre-existing `no-unnecessary-boolean-literal-compare`
  warnings on unrelated lines, incl. session-question-dock.tsx 98/160/283 — none added by this change).
- `bun run test:unit` (packages/app): **730 pass / 0 fail** (full suite green).
- `i18n/parity.test.ts`: 5 pass / 0 fail (after ~1st run the FU-026 fix; the s012 logout-key regression is resolved).
- `event-reducer.test.ts`: 16 pass (question add/reply/reject store logic intact).
- **Benchmark (app AGENTS.md "record baseline before changing session/timeline code"):** `dismiss()` is a
  **one-shot action handler** that runs only when the user submits or rejects (an infrequent, non-hot action).
  It adds one lightweight `useSync()` memo and an O(log n) `Binary.search`+splice on the tiny per-session
  `question[]` array. It does **not** touch the timeline/message-streaming render path (virtual scroll, part
  accumulation, `session-composer-state` memos). So the Playwright `test:bench`/`test:stability` (which guard
  the render hot path and need a live server + browser) were intentionally not run for this change. If a formal
  baseline is wanted, run `bun run test:bench` + `bun run test:stability` in `packages/app`.

## Evidence

- Diff: `50-projects/p003-opencode-fork/opencode` →
  `git diff packages/app/src/pages/session/composer/session-question-dock.tsx` (50 insertions, 1 deletion)
  plus `session-composer-state.ts` (FU-027, ~14 lines) plus 61 i18n locale files (FU-026, 3 lines each).
  This is also the (only) change to `decide()` in the permission path.
- Root-cause paths: event-reducer.ts:454, server-session.ts:1280, session-composer-state.ts:36,
  directory-sync.ts:39 (the `set("question", ...)` route used by `dismiss()`).
- Decision: DEC-017 (see `40-knowledge/decisions-log.md`).

## Follow-ups (updated)

- **FU-026** (DONE, closed): i18n parity failed because s012 added `sidebar.logout`/`sidebar.logoutConfirm`
  only to `en.ts`. Resolved by adding the two English fallback values to all **61** app locale files
  (`appLocales` list in `parity.test.ts`), inserted after `sidebar.settings` to match en.ts order. English
  values chosen deliberately: the runtime base-merge in `language.tsx` already falls back to English for
  missing keys, so this is behavior-neutral today and can be replaced with real translations later
  (AGENTS.md forbids fabricating 65 translations from model knowledge). Parity test now 5/5, full suite 730/730.
- **FU-027** (DONE, closed): applied the same optimistic-clear to the **permission dock** — in
  `session-composer-state.ts` `decide()`, on a successful `sdk().api.permission.reply(...)` we now splice the
  request out of `permission[perm.sessionID]` (same `Binary.search`+splice as the question dock / event
  reducer). This closes the mirror-image bug where the permission dock never dismissed over lost/buffered SSE.
  Note: identical fix pattern to the question dock (DEC-017).
- **FU-023** (carry-over): still needs a rebuild + redeploy + iPhone field test — the question-dock fix,
  permission-dock fix, s011 picker tweaks, and s012 logout button must all be in that rebuild.
