# s026 — Right-click context menu on new/draft (unstarted) session tabs

**Date:** 2026-09-13 (UTC)
**Project:** p003-opencode-fork (web/app)
**Scope:** FE — the native right-click context menu (Rename + Close Tab) that exists on
`TabNavItem` (started chat session tabs) is missing on `DraftTabItem` (new tabs that have not yet
started a session). Add the same menu to ALL tabs, including drafts.

## Goal

```
right-click on ANY titlebar tab (session OR new/draft)
   -> context menu with [Rename] [Close Tab]
      Session tabs:  Rename -> server session rename  (existing, unchanged)
      Draft tabs:    Rename -> persist a custom title via TabInfo    (NEW)
```

## Observations

- `TabNavItem` (`packages/app/src/components/titlebar-tab-nav.tsx`) wraps its tab in a
  `MenuV2.Context` (Kobalte ContextMenu) with Trigger / Portal / Content and two `MenuV2.Item`s:
  `common.rename` + `common.closeTab`.
- `DraftTabItem` (same file) has **no** context menu at all.
- Draft tab titles are currently a hard-coded `language.t("command.session.new")` label passed via
  `titlebar-tab-strip.tsx` (`DraftTabSlot`), with no way to persist a custom name.
- `tabs.tsx` persists per-tab `TabInfo` (`{title?, directory?}`) keyed by `tabKey`; `setInfo` is
  internal, session titles are written through `rememberSessionInfo`.

## Changes

1. `context/tabs.tsx` — add `rememberDraftTitle(draftID, title)` action to persist a custom draft
   title through `setInfo` (`TabInfo.title`).
2. `components/titlebar-tab-strip.tsx` — `DraftTabSlot` reads the custom draft title from
   `tabs.info[id]` (fallback "New session") and threads an `onRename` down to `DraftTabItem`.
3. `components/titlebar-tab-nav.tsx` `DraftTabItem` — add the `MenuV2.Context` wrapper with
   **Rename** + **Close Tab** items and inline rename editing, mirroring `TabNavItem`.

## Result

Implemented. `DraftTabItem` now wraps its tab in the same `MenuV2.Context` (Kobalte ContextMenu)
that `TabNavItem` uses, with **Rename** + **Close Tab**. Rename persists a custom title via
`tabs.info`, so the name survives a reload and is shown in place of the "New session" fallback.

- **Close Tab**: routes through the existing `onClose` (middle-click, right-click menu, long-press
  all standardised from s021).
- **Rename**: inline contenteditable editing on the title (mirrors `TabNavItem`'s rename UX),
  Enter saves, Escape/blur cancels; empty name resets to the "New session" fallback.
- No double-click/drag interaction regressions: dnd + navigate handlers untouched on the draft
  trigger; `data-editing` gating applied so drag/preview don't start while renaming.

## Changes (3 files)

1. `packages/app/src/context/tabs.tsx` — added `rememberDraftTitle(draftID, title)` action
   (persists `TabInfo.title` keyed `draft:<draftID>` via `setInfo`).
2. `packages/app/src/components/titlebar-tab-strip.tsx` — `DraftTabSlot` reads the custom title
   from `tabs.info[id]` (fallback `command.session.new`) and threads `onRename` down to
   `DraftTabItem`.
3. `packages/app/src/components/titlebar-tab-nav.tsx` — `DraftTabItem` gained the
   `MenuV2.Context` (Trigger / Portal / Content) + inline rename, mirroring `TabNavItem`.

## Verification

- `bun run typecheck` (app, tsgo -b, pinned bun 1.3.14): **clean**.
- `bun test --conditions=solid ./src/context/tabs.test.ts`: **12 pass / 0 fail**.
- Full binary build (pinned bun 1.3.14): `0.0.0-dev-202609130518`.
- Deployed to :4447 (kill 1005873 → `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447`
  → pid 1009078). Auth sane: unauth `/`=401, `/login`=200.
- Awaiting on-device right-click / touch long-press field check (UI tab).

## Evidence
- `git diff --stat`: `titlebar-tab-nav.tsx` (+/- DraftTabItem context menu + rename),
  `titlebar-tab-strip.tsx`, `context/tabs.tsx`. (`dialog*.tsx` diffs are uncommitted leftovers from
  s024, not this session.)
- Deployed binary md5 = freshly-built dist at
  `packages/opencode/dist/opencode-linux-arm64/bin/opencode`.
