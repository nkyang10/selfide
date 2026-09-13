# s019 — Mobile fullscreen chat height fix

**Date:** 2026-09-12 (UTC)
**Project:** p003-opencode-fork (web/app)
**Scope:** Minor bug fix — agent chat page height exceeds the mobile phone screen in
fullscreen / installed-app (`display-mode: standalone`) mode.

## Symptom
On a phone, opening the agent chat page in full screen (installed PWA / standalone
fullscreen) causes the page height to exceed the visible screen height.

## Root cause (reproduced by analysis)
Two competing rules size `#root`:

- `packages/app/index.html:25` sets Tailwind `h-dvh` (`height: 100dvh`) — correct for
  mobile; equals the visible viewport.
- `packages/app/src/index.css:20-25` **overrides** it inside
  `@media (display-mode: standalone)` to `height: 100vh`, with a comment stating it was
  added because *"WebKit excludes safe-area insets from dvh in installed apps"*.

On mobile in fullscreen/standalone, `100vh` resolves against the **large viewport**
(includes the zone behind the collapsed browser/status chrome), i.e. larger than the
actual visible screen. Result: root height overflows past the phone screen — the bug.

**Not** caused by the last enhancement (FE-006 sidebar). Blame shows the block was
introduced wholesale with the fork import (`^ecbc6cc` = repo-root commit).

## Fix
`packages/app/src/index.css` — keep the standalone block (preserves original
edge-to-edge intent), but use the dynamic viewport height so it never exceeds the
visible screen:

```css
@media (display-mode: standalone) {
  #root {
    height: 100svh;
    height: 100dvh;
  }
}
```

In standalone/fullscreen there is no URL bar, so `dvh` equals the physical screen and the
original safe-area workaround is preserved without overflowing.

## Evidence
- `packages/app/src/index.css` lines 20-26 changed (100vh → 100svh/100dvh).
- No build config touched; standard CSS only.

## Verification status
- [ ] Rebuild + deploy binary
- [ ] iPhone field test of fullscreen/installed mode (tracked as FU-033)

## Files changed
- `packages/app/src/index.css` (standalone `#root` height override)

## Open follow-ups
- FU-033: deploy + iPhone field test of the fullscreen height fix.
