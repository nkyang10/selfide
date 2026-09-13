# s020 — Drag-down action menu on agent chat tab area

**Date:** 2026-09-12 (UTC)
**Project:** p003-opencode-fork (web/app)
**Scope:** New enhancement FE-009 — drag down from the top agent-chat tab bar to reveal an action menu (Reload, Logout). Extensible to add more actions later.

## Goal
Attach a drag-down gesture to the session/chat tab bar (top of the app). Triggering it opens a small action menu. Start with two actions:
1. **Reload** — full page reload.
2. **Logout** — go to `/logout` (with confirm).

Design must be clean and extensible so future actions are trivial to add (one entry per menu item).

## Approach
See findings + implementation in `40-knowledge/` notes / session body.

## Status
Complete — code verified, production build passes. Not yet deployed to :4447.

## s020 addendum (FE-009 — drag-down action menu, 2026-09-12)
- **FE-009 code complete** (client-only, `packages/app`). Drag down from the top agent-chat tab bar
  (`titlebar-tab-strip.tsx`) opens a small action menu — **Reload** and **Logout** — reusing the
  v2 menu styling (`menu-v2-content`/`menu-v2-item`/`menu-v2-item-content` data attributes).
- **New files:**
  - `drag-down-gesture.ts` — pure pull state machine (`startPull`/`movePull`/`shouldOpenPull`/`RESET`,
    `PULL_THRESHOLD=56`, `ARM_DISTANCE=10`, `AXIS_FACTOR=1.5`). Arm requires downward dominance
    (`dy>10 && dy>1.5·|dx|`) so it never fights the horizontal dnd-kit tab drag. 6 unit tests pass.
  - `drag-down-menu.tsx` — `DragDownMenu` (extensible `DragDownAction[]`; `labelKey`/`confirmKey` typed
    via `TKey` from the i18n `t` union; `icon` via `IconV2` `outline-reset`/`log-out`). Gesture via pointer
    capture; outside-click + Escape dismissal via `makeEventListener`. Icons render inside
    `menu-v2-item-content` (NOT the indicator slot — `menu-v2.css` hides svg there unless `[data-checked]`).
    Outer positioning div keeps `-translate-x-1/2` off the `menu-v2-content` surface, avoiding transform
    clash with the `menu-v2-in` scale animation.
  - `drag-down-gesture.test.ts` — 6 tests covering arm/reset/threshold/axis dominance.
- **Gesture conflict avoidance:** pull arms only from strip background (skips
  `button, a, [role="button"], [contenteditable], [data-titlebar-tab-slot]`); `touch-action: pan-x` on the
  wrapper so vertical pulls reach pointer events while horizontal tab-strip scroll still works.
- **Actions:**
  - **Reload** — `window.location.reload()`; `common.reload` key added to all 62 dict files.
  - **Logout** — reuses `sidebar.logout`/`sidebar.logoutConfirm`, mirrors `home-projects-view.tsx`:
    `window.confirm` → `window.location.href = "/logout"`.
- **i18n parity:** `common.reload` inserted after `common.open` in en + 61 locales; `parity.test.ts`
  5/5 green. `desktop-native.ts`/`parity.test`/`desktop-native.test` excluded.
- **Verified:** typecheck clean (`tsgo -b` via bun shim), unit tests green (gesture 6 + parity 5 +
  titlebar-history/session-events/session suites), production `vite build` (`bun run build`) succeeds; bundle
  `index-D9tRSA9c.js` contains `drag-down` + `common.reload`. Not deployed (FU-034).

