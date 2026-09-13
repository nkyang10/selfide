# s021 — Long-press on agent chat tab → confirm dialog to close the tab

**Date:** 2026-09-12 (UTC)
**Project:** p003-opencode-fork (web/app)
**Scope:** New enhancement FE-010 — a long touch / long press on an agent chat tab prompts a
confirmation dialog before the tab is closed. All close paths (long-press, right-click menu
"Close Tab", middle-click) now route through the confirm dialog.

## Goal
Make closing an agent chat tab a deliberate, confirmed action from the touch-friendly titlebar:
```
long press (touch or mouse, ~500 ms) on a tab
   -> "Close tab" confirm dialog (title + tab name)
      -> Cancel  : dismiss, keep tab
      -> Confirm : close the tab (existing onClose flow)
```

## Approach
`TabNavItem` (`packages/app/src/components/titlebar-tab-nav.tsx`) owns the close flow. All three
close entry points (`closeTab()` from middle-click + right-click menu item, and a new long-press
timer) now set a `confirmCloseOpen` signal instead of closing immediately. The signal drives a
`DialogV2` (Kobalte `DialogRoot open=… onOpenChange=…`) with Cancel / Confirm buttons; Confirm calls
the existing `props.onClose()`.

- **Long-press:** `onPointerDown` records origin + starts a 500 ms `setTimeout`; `onPointerUp`,
  `onPointerCancel`, `onPointerLeave` clear it; `onPointerMove` cancels if the pointer moves > 10 px.
  Mouse long-press works too (helper only skips non-left mouse buttons); dragging/editing are guarded.
- **Native touch context menu:** a touch long-press fires the browser `contextmenu` (~500 ms) which
  would otherwise clash with the dialog — `onContextMenu` suppresses it while `touchActive` and the
  dialog is opening or the timer is pending.
- **No new i18n keys:** reuse existing, parity-guaranteed keys — title `common.closeTab`, header
  close `common.close`, cancel `common.cancel`, confirm `ui.common.confirm`. Body shows the tab's
  session title for context. No locale-file changes needed.

## Files
- M `packages/app/src/components/titlebar-tab-nav.tsx` (only file changed for this feature)

## Verified
- `tsgo -b` (packages/app) — clean.
- `bun run lint` on the file — 0 errors (6 pre-existing consistent-return warnings, none mine).
- `bun test` titlebar-tab-gesture + titlebar-tab-order — 7 pass.
- Fork binary rebuilt (`bun 1.3.14`, pinned) → `0.0.0-dev-202609120946`; smoke test passed.
- Deployed to :4447 (new pid 456022, `OPENCODE_SERVER_PASSWORD=hahahaha`); `/login` 200, `/` 401,
  `/sw.js` 200.

## Status
Complete + deployed. Binary `0.0.0-dev-202609120946` on :4447 also ships the not-yet-deployed
predecessor work from s019 (FE-008 fullscreen height) and s020 (FE-009 drag-down menu), so FU-033
and FU-034 are resolved by this deploy.

## Incident log
Stale e2e `e2e/regression/cross-server-tab-close.spec.ts` references a removed
`[data-slot="tab-close"] button` (from earlier close-button removal, s017-era). Not exercised by this
change; flagged for cleanup in open-followups (FU-036).
