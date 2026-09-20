# Session s059 — Compact-and-new-session tab behavior

**Date:** 2026-09-20 (UTC)
**Slug:** slim-session-tabs
**Scope:** When user clicks "Compact and start a new session with this summary" button in an agentic chat session: (1) place new tab next to original, (2) rename original with `[ended]` suffix, (3) close original tab.

**Target:** `50-projects/p003-opencode-fork/opencode`

## Results
Implemented all 3 requested behaviors on the "Compact and start a new session" button
(`session.slim` flow, `slimSession()` in `message-timeline.tsx`):

1. **New tab next to original** — added module-level `rearrangeTabsAfterSlim()` that registers the
   fresh session tab (idempotent with titlebar's route-change add) then `tabs.reorder` so it sits
   directly after the original.
2. **Original renamed `[ended]`** — original session is renamed server-side to `<title> [ended]` via
   `sdk.api.session.rename` (guarded against double-suffix). Renaming the *session* (not just the tab
   info) is required because the tab title renders from `TabNavItem`'s `session().title ?? fallback`.
3. **Original tab closed** — after reorder, `tabs.closeTab` removes the original so the fresh tab lands
   in its exact slot.

Timing: `addSessionTab` uses Solid `startTransition`, so the helper polls (≤2s) until the new tab is
committed to the store before reordering/closing.

## Evidence
- `fork/packages/app/src/pages/session/timeline/message-timeline.tsx`: helper (L104-161), call site (L1082).
- `fork/packages/app/src/context/tabs.tsx`: unchanged (used existing `addSessionTab`/`reorder`/`closeTab`).
- Checks: `bun turbo typecheck` 30/30 ✅, `oxlint` 0 errors ✅, `vite build` ✅.
- NOT deployed / NOT committed (user did not request commit/deploy).

## Next steps / follow-ups
- (optional) deploy to :4447 + commit if user wants this live.
