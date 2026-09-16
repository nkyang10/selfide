# Session s038 — Submit-failure retry row in session chat

- **Date:** 2026-09-16 (UTC)
- **Status:** CANCELLED — user confirmed current flow is good; no enhancement requested.
- **Scope:** opencode fork web UI (`p003-opencode-fork/opencode`), session chat submit-failure UX.

## Request (user words, condensed)

When a prompt is submitted in the session chat it is pushed to history and a "thinking"
indicator shows. On connection / HTTP error, the thinking row vanishes with no sign and no
follow-up. Enhancement:

1. Add a row next to the failed submit message showing the common error message.
2. Add an icon letting the user redo/resubmit the same prompt.
3. When the user starts writing a new prompt, remove that row to avoid polluting context.

## Findings (code trace)

- Submit entry: `createPromptSubmit.handleSubmit` (`packages/app/src/components/prompt-input/submit.ts`).
- `sendFollowupDraft` (submit.ts:58) sets `session_status: busy` (thinking row via
  `timeline/rows.ts` `TimelineRow.Thinking`, only shown while `isActive && status === "busy"`),
  adds the optimistic user message, then calls `api.prompt(...)`.
- On error `sendFollowupDraft` catch (submit.ts:201-207) does `setIdle()` + `remove()` (optimistic
  message removed), then rethrows.
- `handleSubmit` catch (submit.ts:627-638) additionally: sets idle, `showToast`, `removeOptimisticMessage()`,
  `restoreInput()`. Net effect: prompt vanishes from history, only a transient toast remains.
- Timeline rows: `pages/session/timeline/timeline-row.ts` (tags: `Thinking`, `Error`, `Retry`, ...).
  `Error` row currently only comes from server-side assistant-message errors
  (`rows.ts:219-229`); `Retry` row + `SessionRetry` component are driven by server
  `session_status = {type:"retry"}` (rate-limit).
- Error-string formatting already exists: `formatServerError` (`utils/server-errors.ts`),
  `errorMessage` (submit.ts:249-257).
- Optimistic message lifecycle: `context/server-session.ts` `optimistic.add/remove` +
  `confirmedMessage` reconciliation.

## Plan (draft)

1. **Do not strip** the optimistic message on submit failure; instead record a client-side
   "submit failed" entry per session+messageID: `{ error: string, retry: FollowupDraft }`.
2. **Timeline:** new row tag (e.g. `SubmitFailed { userMessageID, text }`) emitted by
   `rows.ts`/projection when the active/last user message has a failure record; rendered as an
   error `Card` with the formatted error text + a retry `IconButton` beside the failed message.
3. **Retry:** button re-invokes `sendFollowupDraft` with the stored draft (same messageID so the
   optimistic message reconciles into a confirmed one on success).
4. **New-prompt clears row:** observe the prompt input; when the user begins editing/typing a new
   prompt, clear that session's failure records (removes the row + stray optimistic message).
5. Wire through `session.tsx` (timeline needs access to a retry callback + failure store).

## Open design decisions (ask user)

- Keep failed message visible while error row shows, or hide message + show only error row?
- Retry reuses the same messageID/draft (clean reconciliation) — OK?
- "Writes a new prompt" = starts typing (input non-empty) — clear row immediately, or only on next

