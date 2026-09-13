# Session s025 — Safari long-press opens native menu instead of close-tab confirm

**Date:** 2026-09-13 (UTC)
**Project:** p003-opencode-fork (web UI on :4447)
**Type:** enhancement bugfix (FE-010 follow-up) + **deployed**
**Status:** ✅ DEPLOYED — binary `0.0.0-dev-202609130228`, pid 922207, :4447

## Report

FE-010 (s021) long-press-to-close-tab built the target inside a trigger rendered as
`as="a"` with `href` (`titlebar-tab-nav.tsx` — both the titlebar tab trigger and the overflow
menu tab link). On iOS Safari, long-pressing an `<a href>` lets Safari show its native
link-preview/context menu, which swallows the gesture **before** the JS `onContextMenu` fires —
so the long-press close-confirm never opens and Safari's menu appears instead. Overriding
`contextmenu`/`-webkit-touch-callout` cannot suppress this; it is a browser-level anchor behavior.

## Fix

Rendered the triggers as non-anchor elements:
- `MenuV2.Context.Trigger as="a"` → `as="div"` + `role="link"` + `tabindex` (+ keyboard `onKeyDown`
  Enter/Space to preserve keyboard activation).
- Overflow `<a href>` → `<div role="link">` + `tabindex` + same key handling.
- Dropped the `href` attribute in both (navigation was already 100% JS-driven via `props.onNavigate()`
  on mousedown/click, both `preventDefault()`-ed — the anchor never actually navigated).
- Since it is no longer an anchor, Safari no longer intercepts long-press; the close-tab confirm fires.
- `href` remains in the component prop types (unused, harmless — remove later if desired).

## Verification
- Typecheck `packages/app` (`bun x tsc --noEmit`) — clean.
- oxlint on changed file — 0 errors (6 pre-existing warnings).
- Build: `p003/scripts/build-linux.sh` (bun 1.3.14, `--single`) → `0.0.0-dev-202609130228`.
- Deploy: kill 702293 → `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447` → pid 922207.
- Served bundle `index-BKD310Bj.js` md5 == freshly-built dist == `3d482ba…` → fix is in the served UI.
- unauth / = 401, /login = 200, authed / = 200 (FE-001 login intact).

## Evidence paths
- File: `packages/app/src/components/titlebar-tab-nav.tsx`
- Follow-up: FU-035 (on-device iOS field test pending)
