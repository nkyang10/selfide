# s017 — Add close (X) button to chat header next to the "more options" (3-dots) trigger (2026-09-12)

## Scope
Restore a close-tab affordance inside the agent/chat view (the tab body), since s014 removed the
titlebar tab X. Add a close button in the session chat header, immediately right of the 3-dots
"more options" trigger icon that opens the menu containing Archive.

## Changes
- `packages/app/src/pages/session/timeline/message-timeline.tsx`
  - Added imports: `useTabs` (`@/context/tabs`), `useServer` (`@/context/server`),
    `TooltipV2` (`@opencode-ai/ui/v2/tooltip-v2`).
  - Added `serverCtx = useServer()` and `tabsStore = useTabs()`.
  - Added `closeSessionTab()` handler: locates the current session tab
    (`type === "session"`, `server === serverCtx.key`, `sessionId === params.id`) in the top-level
    tabs store and calls `closeTab(index)` so it records for reopen (mirrors titlebar `tab.close`).
  - Added an `IconButtonV2` (`xmark-small`, `variant="ghost-muted"`, `size="large"]`), wrapped in a
    `TooltipV2` ("common.closeTab"), placed after the `Show when={!parentID()}` menu block so it
    renders in both the v2 and legacy layouts and also on child agent sessions.

## Not touched
- Titlebar tab X stays removed per s014. Context menu ("Close tab"), middle-click, and `tab.close`
  keybind remain available.

## Verification
- `bun x tsgo -b packages/app` → clean.
- `bun x oxlint packages/app/src/pages/session/timeline/message-timeline.tsx` → no new warnings
  (only pre-existing `consistent-return` notices).

## Status
Code + typecheck done. Not yet built/deployed (pending user instruction).
