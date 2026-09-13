# FE-009 — Drag-down action menu on the agent chat tab bar (s020)

2026-09-12 — implemented, typechecked, unit-tested, built. **Not deployed** (see FU-034; bundle with FE-008 in one binary).

## Goal
Attach a **drag-down gesture** to the top agent-chat tab bar. Pulling down from the strip background opens a
small **action menu**, initially with **Reload** and **Logout**. The menu is designed to be **extensible** so
future actions are trivial: one entry per item in a `DragDownAction[]`.

## Gesture
- Pure state machine in `drag-down-gesture.ts`: `startPull` / `movePull` / `shouldOpenPull` / `RESET`.
  - `ARM_DISTANCE = 10`, `AXIS_FACTOR = 1.5`, `PULL_THRESHOLD = 56`.
  - Arms (locks onto vertical pull) only when `dy > 10 && dy > 1.5 × |dx|` — **downward dominance** — so it
    never fights the horizontal **@dnd-kit tab drag** (PointerSensor `Distance(4)` any-direction).
  - Opening: `dy >= 56` on release → open menu.
- The pull only arms from the **strip background**, skipping
  `button, a, [role="button"], [contenteditable], [data-titlebar-tab-slot]` — so grabbing a tab still reorders it,
  not the menu.
- `touch-action: pan-x` on the wrapper: vertical pulls reach JS pointer events while horizontal tab-strip scroll
  keeps working on touch.

## Menu (`drag-down-menu.tsx`)
- Extensible contract:
  ```ts
  interface DragDownAction {
    id: string
    labelKey: TKey                 // i18n key, typed from the t() union
    icon: string                   // IconV2 name: "outline-reset" | "log-out" | ...
    onSelect: () => void
    confirmKey?: TKey              // optional window.confirm copy
  }
  ```
- Gesture via **pointer capture**; dismissal via **outside-click + Escape** (`makeEventListener`).
- Styling reuses the v2 menu CSS via data attributes (no Kobalte anchor):
  `data-component="menu-v2-content"`, `data-component="menu-v2-item"`, `data-slot="menu-v2-item-content"`.
- **CSS gotchas handled:**
  1. `menu-v2.css` hides `svg` inside `[data-slot="menu-v2-item-indicator"]` unless `[data-checked]` → icons are
     placed directly in `menu-v2-item-content`, not the indicator slot.
  2. `menu-v2-in` animation uses `transform` (scale) which would clash with a `-translate-x-1/2` positioning → an
     **outer positioning div** (centered) wraps the inner `menu-v2-content` surface, keeping the transform off it.
  3. Menu flips above the bar when it would overflow the bottom edge.

## Actions wired (titlebar-tab-strip.tsx)
- **Reload** — `window.location.reload()`; label from new `common.reload` key (added to all 62 dict files).
- **Logout** — reuses `sidebar.logout` + `sidebar.logoutConfirm`, mirrors `home-projects-view.tsx`:
  `window.confirm` → `window.location.href = "/logout"`.

## i18n
- `common.reload` inserted after `common.open` in **en + 61 locale files** (62 app dicts). Excluded dicts
  (`desktop-native.ts`/`parity.test.ts`/`desktop-native.test.ts`) not touched. English value `"Reload"`.

## Files
- `opencode/packages/app/src/components/drag-down-gesture.ts` — new pure pull state machine.
- `opencode/packages/app/src/components/drag-down-gesture.test.ts` — new, 6 tests (arm/reset/threshold/axis).
- `opencode/packages/app/src/components/drag-down-menu.tsx` — new `DragDownMenu` + `DragDownAction`.
- `opencode/packages/app/src/components/titlebar-tab-strip.tsx` — import; `dragActions`; tabs wrapped in
  `<DragDownMenu actions class="relative min-w-0">`.
- `opencode/packages/app/src/i18n/*.ts` — `common.reload` added (en + 61).

## Verification
- `tsgo -b` (via bun shim) — typecheck clean, no output.
- Unit: `drag-down-gesture.test.ts` (6) + `i18n/parity.test.ts` (5) — all green.
- `~/.bun/bin/bun run build` (packages/app) — production vite build succeeds; bundle `index-D9tRSA9c.js`
  contains `drag-down` + `common.reload`.

## Visual/deploy check on a phone (pending)
Not deployed this session — see **FU-034**. When deployed, verify: pull down from tab-bar background opens the
menu; Reload reloads; Logout confirms then hits `/logout`; horizontal tab drag still reorders; menu flips above on
low viewport.
