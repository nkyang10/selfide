# FE-012 — Right-click context menu on new/draft chat session tabs

**Date:** 2026-09-13 (UTC)
**Status:** ✅ DONE + DEPLOYED — binary `0.0.0-dev-202609130518` (pid 1009078 on :4447)

## What

Until now the native right-click context menu (**Rename** + **Close Tab**) existed only on
`TabNavItem` (started chat-session tabs). `DraftTabItem` (new tabs that have not yet started a
session) had **no** context menu. This adds the same menu to **all** tabs, including drafts.

## Implementation (`packages/app/`)

- `components/titlebar-tab-nav.tsx` — `DraftTabItem` now wraps its tab in the same `MenuV2.Context`
  (Kobalte ContextMenu) as `TabNavItem`, with **Rename** + **Close Tab** items.
  - Close Tab → existing `onClose` (which routes through the s021 confirm dialog).
  - Rename → inline contenteditable editing on the title; Enter saves, Escape/blur cancels.
    (Mirrors `TabNavItem`'s rename UX.)
- `context/tabs.tsx` — new `rememberDraftTitle(draftID, title)` action persists `TabInfo.title`
  keyed `draft:<draftID>` via `setInfo`.
- `components/titlebar-tab-strip.tsx` — `DraftTabSlot` reads the custom title from
  `tabs.info[id]?.title` (fallback `command.session.new`) and threads `onRename` down to
  `DraftTabItem`.

## Verification

- App typecheck (`tsgo -b`, pinned bun 1.3.14): clean.
- `tabs.test.ts`: 12 pass / 0 fail.
- Full single-file build + deploy to :4447. Auth sane (unauth `/`=401, `/login`=200).

## Follow-up

- On-device check: right-click / touch long-press on a **new/unstarted tab** → Rename + Close Tab;
  rename persists across reload. See FU-041.
