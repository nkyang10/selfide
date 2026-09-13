# Session s024 — Empty dialog shell blocking the view after login

**Date:** 2026-09-13 (UTC)
**Project:** p003-opencode-fork (web UI on :4447)
**Type:** bug investigation (Playwright repro) + **deployed fix**
**Status:** ✅ FIXED + DEPLOYED — binary `0.0.0-dev-202609121825`, pid 702293, :4447

## Report

User: content-less dialog at the middle of the screen blocks the view after login.
They pasted `data-component="session-tab-popover-trigger"` (a normal titlebar tab), and later
clarified the blocking item sits "under data-titlebar-tab-slot".

## Real root cause (found by Playwright repro, not static guess)

A `dialog-v2` shell — `position:fixed; inset:0` (z:50, `pointer-events:none`) containing a
centered opaque box `dialog-container` (`pointer-events:auto`, bg `layer-01`) — was rendered in
the DOM **even when closed**. `elementFromPoint` at screen-center returned this empty box → it
genuinely blocked the middle of the view.

- `Dialog`/`DialogV2` (`packages/ui/src/v2/components/dialog-v2.tsx`) always emitted its shell
  divs (`dialog-v2` full-screen + `dialog-container` center box) regardless of the Kobalte
  `Root` state; only the inner `Kobalte.Content` (the actual title/body/footer) was gated by
  open-state. So a **closed** dialog rendered an empty-opaque centered box.
- The only place an always-mounted `Dialog` exists is the per-tab **close-tab confirm dialog** at
  `titlebar-tab-nav.tsx:394` (`DialogRoot` + `DialogV2`), nested under `data-titlebar-tab-slot`.
  Every other dialog mounts via the portal DialogContext only when opened, so they never showed
  the empty shell. Legacy `Dialog` (`components/dialog.tsx`) shared the same always-shell pattern.

## Fix (source)

Gate both dialog components' shells on the Kobalte open state so nothing renders while closed:

- `packages/ui/src/v2/components/dialog-v2.tsx` — `Dialog`: wrap shell in
  `<Show when={useDialogContext().isOpen()}>`.
- `packages/ui/src/components/dialog.tsx` — legacy `Dialog`: same `Show when={isOpen()}` gate.

`useDialogContext` is Kobalte 0.13.11 (hoisted core); both `Dialog` usages (local `Root` and
`dialog.show` context) are always inside a Kobalte `Root`, so the hook is safe. During the closing
transition Kobalte keeps `isOpen` true, so the shell persists for the exit animation.

## Verification (Playwright, :4447)

- Before: `dialog-v2` empty box at `0,238 390x368`, `elementFromPoint` = the empty container.
- After fix + redeploy: **no** `dialog-v2`, no fixed overlays after login (fresh + direct session).
- Long-press on the tab opens the close-tab confirm dialog correctly with content
  ("關閉分頁 / <title> / 取消 確認"), centered box — dialog still works.

## Notes

- Also kept the earlier (s024) `previewData` guard in `titlebar-tab-nav.tsx` (prevents the hover
  preview opening empty) — independent, defensive, harmless.
- Repro scripts were placed in `packages/app/e2e/repro/` then removed after verification.

## Evidence

- `packages/ui/src/v2/components/dialog-v2.tsx` `Dialog` (gate applied).
- `packages/ui/src/components/dialog.tsx` `Dialog` (gate applied).
- `titlebar-tab-nav.tsx:394` close-tab per-tab dialog source of the always-mounted shell.
- Deploy: build `0.0.0-dev-202609121825`, pid 702293, :4447.
