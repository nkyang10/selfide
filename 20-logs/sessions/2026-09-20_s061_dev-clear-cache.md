# Session s061 — DEV menu "Clear cache" option

**Date:** 2026-09-20 UTC
**Agent:** controller
**Project:** p003-opencode-fork

## Goal
Add a "Clear cache" option to the DEV dropdown menu so a PWA (iOS/Safari
desktop-web-icon / home-screen installed app) can be reset to its basic status by
clearing all cookies, local storage, session storage, and file/CacheStorage caches.

## Actions
- Edited `opencode/packages/app/src/components/titlebar.tsx` — in the
  `ChannelIndicator` DEV `DropdownMenu`, inserted a new `Clear cache` item between
  `Refresh` and `Debug tools`.
- The handler:
  - clears **all** cookies (`document.cookie.split(";")` … expire with path=/)
  - clears `localStorage` and `sessionStorage`
  - deletes every entry v ia the Cache Storage API (`caches.keys()` → `delete`)
  - reloads the window
- Ran `bun run typecheck` (`tsgo -b`) → clean.

## Result
`Clear cache` now performs a full client-side reset and reloads to the basic
state. Verified typecheck passes (`tsgo -b`, 0 errors). No build/lint regressions
observed. No unit tests added (cookies/storage/cache clearing are browser
primitives; not covered by the existing suite).

## Test (user, iOS)
- Pressing **Clear cache** worked: cleared the state.
- Observed side effect: UI style reset from the set **bright** theme back to the
  **default dark** — **expected**, since the theme preference is stored in
  `localStorage`, which the button wipes. Documented so it's not flagged as a bug
  later. (A future enhancement could re-apply theme from cookie, but per current
  requirements the button intentionally resets everything.)

## Evidence
- `opencode/packages/app/src/components/titlebar.tsx:670-683` (new item).

## Follow-ups
- Commit to git (the code change is still uncommitted — see FU-072).
- Clarified with user: server HTTP Basic auth (`opencode`/`hahahaha`) staying enabled after Clear cache is
  **expected** — Basic is the server's per-request guard and JS cannot erase Basic credentials. No change.
