# s022 — Session "Slim" button (compact + hand off to a fresh session)

**Date:** 2026-09-12 (UTC)
**Scope:** `packages/app` (client-only) + one new v2 icon in `packages/ui`.
**Feature:** In the agent chat session header (next to the 3-dot "more options" and the close tab icon),
add a **slim** icon button. Clicking it:
1. runs `/compact` (AI summarization of the current session) to produce a compact report,
2. creates a **new** agent session in the same directory, named `<previous title> (N)` (N = 1, 2, …),
3. submits the compact report as the **initial message** of that new session,
4. focuses/navigates the page to the new session.

## Status
- [x] icon — reused existing v2 `collapse` glyph (converging arrows = "slimmer"); no new icon added
- [x] i18n key `session.slim.title` + en.ts + 61 locales (parity 5/5)
- [x] `slimSession` handler
- [x] button in header (between 3-dot menu and close)
- [x] typecheck / parity / unit (743) / build / lint — all green

## Notes / decisions
- "slimmer" meaning → compact + hand off to a fresh session (not in-place compaction).
- Compact report is read from the *original* session's newest assistant text part (the compaction
  summary message; `message.summary === true`), via `extractPromptFromParts`.
- New-session initial message sent via `sendFollowupDraft` (same path the composer uses) so the
  assistant actually replies to the handoff.
- Name collision: pick the lowest free `title (N)` suffix by scanning `sync().data.session` titles;
  new session is renamed via `session.rename`.
- New-session created with `session.create({ agent, model })` (same agent+model as the source session),
  focused via `navigate(sessionHref(...))` + `requestAnimationFrame` focus on the composer editor.
- `session.compact(...)` + `session.wait(...)` from v2 protocol (also used by the existing `/compact`
  slash command); `.catch(noop)` on wait guards v1-compat edge cases.

## Result
Protocol close-out complete. Client-only feature (FE-011) — no server change required.

## Files changed
- `packages/app/src/pages/session/timeline/message-timeline.tsx` — slim handler + button + imports
- `packages/app/src/i18n/en.ts` + 61 locale files — `session.slim.title`

## Commands
(see command-log)
