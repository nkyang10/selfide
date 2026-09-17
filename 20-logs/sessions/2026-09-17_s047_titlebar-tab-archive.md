# Session s047 — New feature: Archive icon on open titlebar session tabs

**Date:** 2026-09-17 (UTC)
**Session:** s047
**Trigger:** User request — "new feature: add a archive icon before icon-button-v2; archive = close tab + hide from session list; prompt confirmation when click." User clarified the location: on the **open titlebar session tabs** (NOT the home session-list rows, where an archive button already exists but is gated by `SHOW_HOME_SESSION_ARCHIVE=false`).

## What shipped (p003 fork source, uncommitted)

1. **`packages/app/src/components/titlebar-tab-nav.tsx`** — added an `onArchive?` prop to `TabNavItem`. Rendered an archive `IconButtonV2` (`data-action="titlebar-tab-archive"`, icon `archive`) on the trailing edge of each session tab, revealed on hover via `group-hover`. On click it calls `archiveTab`, which shows a `window.confirm` with the new `common.archiveConfirm` string and, if accepted, fires `props.onArchive`.
2. **`packages/app/src/components/titlebar-tab-strip.tsx`** — threaded `onArchive` through `TitlebarTabStrip → SessionTabEntry → SessionTabSlot → TabNavItem`. Implemented the archive action in `SessionTabEntry` via `archiveHomeSession` (reused): server-side `session.update({ time: { archived: Date.now() } })` marks it archived (hides it from the home session list via the `!s.time?.archived` filter) and `notifySessionTabsRemoved` → the titlebar's `SESSION_TABS_REMOVED_EVENT` listener calls `tabsStoreActions.removeSessions(...)` to close the open tab.
3. **`packages/app/src/i18n/en.ts` + all locale dicts (60 files)** — added `common.archiveConfirm` (confirm text). Manual translations; parity test repass.

## Verification
- `bun run typecheck` clean (tsgo -b).
- `bun test src/i18n/parity.test.ts src/pages/home-session-archive.test.ts` → 7 pass.
- `bun test src/components/titlebar-session-events.test.ts` → 2 pass.

## Notes / decisions
- Titlebar session tabs previously had **no** visible close `icon-button-v2` (close lived in the right-click context menu), so the archive button sits on the tab's trailing edge — the position where a close icon-button-v2 normally sits. Confirmation uses a native `window.confirm`.
- Archive + guard: the pre-existing `common.archive` translation already existed; reused. `common.archiveConfirm` is new across all 60 locales (hand-translated, parity-repass OK).
- Decided to reuse `archiveHomeSession` (already used by the home session-list archive) so both entry points stay consistent.

## Not done (awaiting user)
- **Not committed / not pushed** to the fork `dev` branch.
- **Not built / not deployed** to :4447 (no deployment requested by this request; follows the FU-049 pattern of awaiting user go-ahead → see open-followups).
