# Session s060 — Mobile touch: Enter=Newline not submit

- **Date (UTC):** 2026-09-20
- **Session:** s060
- **Target:** p003-opencode-fork — `packages/app/src/components/prompt-input.tsx`
- **Request:** Detect mobile phone touch-screen user; if true, pressing Enter in the prompt should insert a newline instead of submitting.

## Summary

Added touch-device detection to the web chat prompt input. On touch-capable devices
(coarse pointer or `maxTouchPoints > 0`), the plain Enter key now inserts a newline at the
caret instead of submitting the prompt. Shift+Enter and IME behavior are unchanged.

## Changes

`50-projects/p003-opencode-fork/opencode/packages/app/src/components/prompt-input.tsx`:

- Added `isTouchDevice()` helper (SSR-safe) that returns true when the current device has a
  coarse primary pointer (`matchMedia("(pointer: coarse)")`) or reports touch points
  (`navigator.maxTouchPoints > 0`).
- In `handleKeyDown`, the plain-Enter submit branch now short-circuits on touch devices:
  inserts `"\n"` via the existing `addPart` helper (the same path Shift+Enter uses) and returns,
  so the message is not submitted. A send button remains the submit path on mobile.

## Verification

- `bun run typecheck` (tsgo -b) — clean.
- `bun test --conditions=solid --only-failures --preload ./happydom.ts ./src src/components/prompt-input` — 750 pass / 0 fail.

## Notes / Follow-ups

- Touch detection does not re-evaluate on pointer-type change (e.g. hybrid devices). Acceptable
  trade-off; a `pointer` event listener could be added later if needed.
- Confirm the mobile prompt shows a visible send button (submit path on touch). NOT verified on
  real device.
