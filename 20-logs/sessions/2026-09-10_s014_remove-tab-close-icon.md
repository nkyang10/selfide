# s014 — Remove "Close tab" icon from titlebar tabs (2026-09-10 16:53 UTC)

## Scope
Remove the X (close tab) icon button from the titlebar tab items.

## Changes
- `packages/app/src/components/titlebar-tab-nav.tsx`
  - `TabNavItem`: removed the `<div data-slot="tab-close">` IconButtonV2 block.
  - `DraftTabItem`: removed the same block.
  - Dropped now-unused `IconButtonV2` import.
  - Closing still possible via: tab context menu ("Close tab"), middle-click, keyboard `tab.close`.
- `packages/app/src/components/titlebar-tab-nav.css`
  - Removed dead `[data-slot="tab-close"]` positioning/hover/edit rules (3 blocks).

## Not touched
- `isTabCloseTarget()` gesture guard in `titlebar-tab-gesture.ts` and its usage in
  `titlebar-tab-strip.tsx` — harmless (checks for an element that no longer renders); kept to
  avoid churn. Legacy `session-sortable-tab*.tsx` close icons untouched (components unused).

## Verification
- `bun x tsgo -b` → clean.
- `bun test` titlebar-tab-gesture/order/session-events/history → 12 pass / 0 fail.

## Status
Code done; built + deployed per standing instruction (see command-log).
