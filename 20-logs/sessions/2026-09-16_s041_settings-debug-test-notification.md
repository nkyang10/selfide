# Session s041 — Settings › General: add "Debug" section + "Test notification" button

- **Date:** 2026-09-16 (UTC)
- **Session:** s041 (s040 id was already used in command-log during the s039 close-out; reserved to avoid collision)
- **Focus:** p003 fork — desktop settings › General: new **Debug** section with a **Test notification**
  row whose button fires a system notification 5 s after click.

## Task
1. Settings › desktop › General: add a new section titled **Debug**.
2. In it, add row **Test notification** — the trailing control is a **button**, not a settings value
   (switch/select). Clicking it triggers a system notification after **5 seconds**.

## Implementation (`packages/app`)
- `components/settings-v2/general.tsx`:
  - Added `DebugSection` (desktop-only via `<Show when={desktop()}>`, matching Updates/Display sections),
    rendered after `AdvancedSection`.
  - `SettingsRowV2` titled "Test notification" with `ButtonV2` in the control slot that, on click,
    schedules `platform.notify(...)` 5 s later (`TEST_NOTIFICATION_DELAY_MS = 5_000`, timeout cleared
    on unmount). Title/description/button-label read from i18n.
- `i18n/en.ts` + all 60 app locales: 4 new keys
  `settings.general.section.debug` / `settings.general.row.testNotification.{title,description,sendLabel}`
  (non-English locales fall back to the English source copy).
- Uses the existing `platform.notify()` channel (`context/platform.tsx`) — the same path turn-complete /
  error notifications use (`context/notification.tsx`).

## Verification
- `bun turbo typecheck --filter=@opencode-ai/app`: pass (tsgo, after fixing `setTimeout`/`Timeout`
  return-type mismatch — use plain global `setTimeout`, not `window.setTimeout`).
- `bun test src/i18n/parity.test.ts`: 5/5 pass, 979 assertions (all 61 locales have the 4 new keys;
  no extra keys).
- `bun test src/components/settings-v2/general-controllers.test.ts src/context/settings.test.ts`: 17/17 pass.
- `bunx oxlint packages/app/src/components/settings-v2/general.tsx`: 0 warnings, 0 errors.

## Evidence
- Files changed (working tree, **uncommitted**):
  - `packages/app/src/components/settings-v2/general.tsx`
  - `packages/app/src/i18n/en.ts` + `packages/app/src/i18n/{ar..uz}.ts` (61 locale files, English copy)
- Follow-up: FU-051 (commit/build/deploy + desktop visual retest).

## Caveats
- The desktop `platform.notify` implementation early-returns when the window is focused
  (`packages/desktop/src/renderer/index.tsx`). For an end-to-end visual test, blur the app window
  within the 5 s window (or rely on the OS notification center for the latency part).
