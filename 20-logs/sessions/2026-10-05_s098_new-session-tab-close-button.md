# Session s098 — New-session tab: close button in session area

- **Date:** 2026-10-05
- **User request:** "markcode webui the new session tab page … there is no top right hand close tab icon button, add it"
- **Clarifications (user, in order):**
  1. "not the tab nav bar. i mean the session area" → not the `TitlebarTabStrip` ✕ on tabs.
  2. "i mean the tab specially for newly created tab. not the usual tab that always in session" → the **new-session draft page** (`/new-session?draftId=…`) — the tab that exists for a freshly created session.

## Understanding

On the new-session (draft) page, the top right of the session area (v2 titlebar right mount
`#opencode-titlebar-right`) currently only shows `NewSessionStatus` (status pill, gated by
`settings.visibility.status`). There is no visible way to close the draft tab from the page —
close options today are: right-click tab → "Close tab" (added 031f8b0), middle-click, Ctrl+W.

## Plan

1. `packages/app/src/pages/new-session/new-session-view.tsx`: add `NewSessionCloseTab` — a
   `Portal` into the titlebar right mount rendering an `IconButtonV2` (`IconV2 name="close"`,
   `variant="ghost-muted"`, `size="large"`, matching neighbors) with `TooltipV2` +
   `KeybindV2` (`tab.close` keybind). Resolves the draft tab from `useTabs().store` via the
   route's `draftId` search param; calls `tabs.closeTab(index)` (same user-initiated close path
   as the tab-strip menu: records for reopen, navigates to next tab or home).
2. `packages/app/src/pages/new-session.tsx`: render `<NewSessionCloseTab mount={rightMount} />`
   after `<NewSessionStatus …/>` so the ✕ sits at the far top-right.
3. i18n: reuse existing `common.closeTab` ("Close tab") — no new strings.
4. Verify: typecheck app package.

## Results

- **Shipped (uncommitted, working tree):**
  - `packages/app/src/pages/new-session/new-session-view.tsx` — new exported `NewSessionCloseTab`:
    Portals an `IconButtonV2` (`IconV2 name="close"`, `ghost-muted`, `size="large"`) into the v2
    titlebar right mount. Resolves the draft tab via the route's `draftId` search param against
    `useTabs().store`; click → `tabs.closeTab(index)` (same user-initiated path as the tab-strip
    context menu: records for reopen `mod+shift+t`, navigates to next tab or home). Tooltip =
    reuse `common.closeTab` + `KeybindV2` for `tab.close` (mod+w). Hidden if the draft tab is not
    in the store (e.g. direct URL with no tab). i18n: no new strings.
  - `packages/app/src/pages/new-session.tsx` — renders `<NewSessionCloseTab mount={rightMount} />`
    after `<NewSessionStatus …/>`, so the ✕ sits at the far top right of the new-session page.
- **Verification:** `bun run typecheck` (tsgo -b) clean; `bun run test:unit` **852 pass / 0 fail**
  (116 files). No tests exist for this component; behavior verified by typecheck + existing suite.
- **Not committed** — fork working tree also holds unrelated pre-existing changes (websearch /
  serper, config) from earlier sessions; left untouched. Commit decision left to user.

## Evidence

- Diff: `git -C 50-projects/p003-opencode-fork/opencode diff -- packages/app/src/pages/new-session.tsx packages/app/src/pages/new-session/new-session-view.tsx`
- Scope confirmation: only the 2 app files changed by this session (see `git status --short`).

## Deploy addendum (RB-003)

- Commit `bd63e52` → push rejected (parallel origin commit `fc5caae`, a Windows version stamp,
  no file overlap) → `git pull --rebase --autostash` (serper tree stashed+restored untouched) →
  **`4938605`** pushed `fc5caae..4938605`. Pre-push hook typecheck 30/30 both times.
- Deploy via `scripts/deploy-web-4447.sh --detach`: the tool call died the moment the old
  listener (this session's own server, pid 3037933) was killed — expected per the runbook; the
  setsid re-exec survived. Build **`1.1.20261005030342`** (smoke test passed), new pid
  **3110424** on 0.0.0.0:4447, pidfile updated.
- Verification: ss listener = pidfile; `/`, `/health`, `/api/health` all **401** — the FE-001
  login gate (runbook's anonymous `{"healthy":true}` check predates the gate; the deploy
  script's own "login page active" probe passed). `testing/web-4447.log` shows live session
  sync traffic on the new pid. `packages/app/dist` mtime 11:03 > commit 11:02:34.
- **Not DOM-verified** (s091 lesson): the ✕ button has never been seen in a browser — next
  time the UI is open, create a new session tab and confirm the top-right ✕ closes it.
- The uncommitted s093 serper tree shipped in this build too, as it did in s095/s097.

## Placement correction (user, after the first deploy)

The first version put the ✕ in the **titlebar right mount** (next to the status pill). The user
redirected: *"i suppose to add inside session-new-design similar to the parent of session-title-child"*.

- `data-component="session-new-design"` (`new-session-view.tsx:42`) is the page's rounded inner
  box — the `NewSessionView` content area, **not** the titlebar.
- `session-title-child` is the `<h1>` in the session page's title row
  (`message-timeline.tsx:1621`); its parent is `<div class="flex items-center min-w-0 flex-1 w-full">`
  (`:1598`), the row itself `h-12 … justify-between gap-2` (`:1591`), and that row's right-hand
  cluster is `IconButtonV2 variant="ghost-muted" size="large"` (`:1674+`). `ProviderTip` is the
  existing precedent for an absolutely positioned control inside the box (bottom-4).
- **Change:** `NewSessionCloseTab` lost its `mount` prop and the `Portal`; it is now rendered
  inline inside the box as `<div class="absolute right-2 top-0 flex h-12 items-center">`, so the
  control sits at the box's top-right, vertically centred on the same 48px row the session title
  uses, with the same button variant/size as that row's action cluster. Logic (draft tab lookup by
  `draftId`, `tabs.closeTab`, tooltip + `tab.close` keybind, i18n reuse) unchanged.
- `pages/new-session.tsx` no longer references it — the page diff is back to only the import
  line being reverted.
- **Gates:** typecheck clean · app unit **852/0** (116 files).
- **Redeployed:** `d05959e` pushed (`4938605..d05959e`, pre-push typecheck 30/30) → build
  **`1.1.20261005052148`**, pid **3188312** on :4447 (prev 3110424), smoke test passed, `/` → 401
  (login gate), live traffic in `testing/web-4447.log`.
- **Still not DOM-verified** (s091 lesson) — the user should reload and confirm the ✕ appears at
  the box's top-right and closes the tab.
