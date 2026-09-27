# s068 — Review of fa41da0 (Settings v2 responsive nav): is the added code still earning its keep?

- **Date:** 2026-09-26 (UTC)
- **Owner:** agent (user: mark)
- **Trigger:** user — "review the previous commit about setting v2 and modified code is no longer useful and can be better"
- **Commit reviewed:** `fa41da0 feat(app): make v2 settings tabs horizontal on narrow screens`
- **Outcome:** user's instinct was right. **3 real defects + dead weight** found; fixed in `71c73a0` (pushed `origin/dev`),
  deployed to :4447 (pid 2999326) and confirmed by the user ("it is good now").

## What the review checked (and how)

Not a re-read of my own reasoning — re-measured on the live build with Playwright (`/tmp/opencode/probe-strip*.mjs`,
`review-measure.mjs`), compared the pre-commit CSS at `ab47c38`, and had a subagent sweep the repo for existing
helpers/conventions/collisions.

## Findings

### 1. Dead weight — the repo already had the helper I hand-rolled

`@solid-primitives/media` is a dependency and `createMediaQuery` is used at **8 sites** in `packages/app`
(`titlebar.tsx:76`, `settings-v2/general.tsx:282`, `session-context-usage.tsx:55`, `session-header.tsx:167`,
`session.tsx:448`, `session-side-panel.tsx:95`, `terminal-panel-v2.tsx:39`, `sidebar-workspace.tsx:330`). My commit
was the **only** place that hand-rolled `createSignal` + `onMount` + `matchMedia` + `onCleanup` for a viewport query.

**Fixed:** `const narrow = createMediaQuery("(max-width: 639px)")` — 8 lines → 1, and the `onMount`/`onCleanup`
imports are gone.

### 2. Dead weight — 9 CSS lines re-declared rules the ui package already provides

`ui/src/v2/components/tabs-v2.css:31-40` already gives the horizontal list `width:100%; overflow-x:auto;
scrollbar-width:none; -ms-overflow-style:none` + the `::-webkit-scrollbar` rule. Because Kobalte puts
`data-orientation="horizontal"` on the list itself, those apply to the strip. `border-inline-end: none` was dead
after the vertical rule stopped matching.

**Fixed:** all removed; only the app-specific bits stay (`flex-shrink`, `overflow-y:hidden`, transparent bg,
`border-bottom`).

### 3. Defect — deleting the 144px side-nav rule cost ~96px of row width from 640px to ~1010px

`ab47c38` and `fa41da0` have **identical** row rules (`flex-wrap: wrap` base / `nowrap` at `min-width: 640px`), so
above 640px rows do not wrap while the nav went from 144px back to a fixed 240px. Measured usable key/value row:

| viewport | before (`ab47c38`) | after (`fa41da0`) |
|---|---|---|
| 640px | 344px | **248px** |
| 700px | 404px | **308px** |
| 820px | 524px | **428px** |
| ≥1012px | 620px | 620px (identical, dialog capped at 980) |

A constant **−96px** across the whole 640–1011px band (tablets, split-screen, small windows; iPhone-SE landscape is
667px). The sub-640px win was real (390px: 134 → 286px), but the medium band was collateral damage.

**Fixed:** the vertical nav is now app-scoped `width: clamp(168px, 24vw, 240px); min-width: 0` → 168px at 640,
197px at 820, 240px at ≥1012 (desktop untouched). Row width becomes 320 / 380 / 471 in those three cases.
**Alternative considered:** widening the strip breakpoint to 767px (the repo's mobile value) — rejected, because
767–1011px still has plenty of room for a side nav and a top strip there would be premature.

### 4. Defect — the "hide the icons" rule never matched (this is what the user spotted)

I wrote `[data-slot="icon-svg"] { display: none }`, but `Icon` renders `<div data-component="icon"><svg
data-slot="icon-svg">…</svg></div>` (`ui/src/components/icon.tsx:156-178`) — the 20px box that occupies the space
is the **div**, not the svg. So every label kept an empty icon slot ("padded right like there is an icon in the
left"). The probe showed `span.children = [div 20px, text]`.

**Fixed:** target `[data-component="icon"]`. With the icons actually gone the strip needs ~241px (zh) / ~317px
(English) instead of 413px, so all five tabs fit a 390px dialog.

### 5. Defect — `justify-content: center` clipped the first tab

The user asked for the strip to be centred. With `width: max-content` + `min-width: 100%`, an overflowing strip
centres both ways: the first wrapper measured **x = −7px at 390px** and **x = −22px at 360px** — cut off and, per
spec, unreachable by scrolling (the reason `safe` exists).

**Fixed:** `justify-content: safe center` — centred when the tabs fit, start-aligned + scrollable when they do not.
(Graceful degradation: if `safe` is unsupported the declaration is dropped and the flex default `flex-start` applies.)

### 6. Structure nit — colour was on the trigger, not the wrapper

The vertical variant puts `color: var(--v2-text-text-muted)` on the **wrapper** (`tabs-v2.css:198-204`); my
horizontal block put it on the trigger plus a `gap: 6px`. That meant the wrapper carried no colour of its own, so any
future wrapper-level rule would not have reached the label.

**Fixed:** colour (and the existing `height`/`padding`/`radius`) all live on the wrapper now, exactly like the
vertical variant; the trigger-level rule is gone.

### 7. Checked and found fine (no action)

- **No class collisions.** `settings-v2-nav` / `-nav-group` / `-nav-footer` exist only in this dialog + its CSS;
  the v1 settings dialog renders no `settings-v2-*` class at all. `class="settings-v2"` is unique to this
  `TabsV2`, and `TabsV2` is mounted in exactly one place in the whole app — so the new CSS belongs in the app
  package and cannot leak. (Caveat recorded, pre-existing: `settings-v2.css:8/12/167/172` are selected by
  `[data-component="dialog-v2"][data-variant="settings"]` and also match the manage-models / server dialogs.)
- **`packages/ui` untouched** — the adaptive nav width is an app-level override at higher specificity
  (`.settings-v2[...][data-orientation="vertical"]`, 5 attribute/class units vs the ui rule's 4), no fork patch to
  the shared component.
- **Overflow rule is genuinely needed**: computed `overflow-x` on the list is `auto` while `scrollbar-width` is
  `auto` too, so nothing in the app was hiding the scrollbar for this state before the commit — dropping the
  duplicate would have shown a scrollbar, which is why the ui rule's `scrollbar-width: none` must stay in the ui
  file (it does).
- **Keyboard + ARIA still correct** in the strip (`aria-orientation=horizontal`, ArrowRight moves selection).
- **No visible close button** exists in this dialog in either layout (`dialogHasCloseButton: false`) — so hiding the
  version footer in narrow mode costs nothing; the app's own escape/scrim behaviour is unchanged. Pre-existing, not
  from this commit.

## Net effect of the follow-up (`71c73a0`)

`fa41da0` added 124 lines; the review removed ~14 of them and fixed the three defects — **net smaller than the
original commit** while actually being correct. Gates: `bun typecheck` (app) clean · `oxlint` 0 errors ·
pre-push `bun turbo typecheck` 30/30 · deployed :4447 pid 2999326 · user confirmed.

## Residual, deliberately not changed

- Below 640px the rows still stack the control under the label (`[data-slot="settings-v2-row-control"] { width: 100% }`).
  With the strip that is now defensible (368px of inner width); revisit only if a control feels cramped.
- The nav flips at 640px while `general.tsx`'s `mobile` signal is 767px — two breakpoints in one dialog, both
  pre-existing choices. Aligning them is a judgement call, not a bug.
- Five tabs still overflow in very long locales (e.g. German) even label-only; the strip scrolls, and `safe center`
  keeps the first tab reachable. An edge-fade affordance exists as a precedent in `titlebar-tab-strip.tsx:411-420`
  if discoverability is ever reported as a problem.

## Evidence

- Commit `71c73a0` (pushed `fa41da0..71c73a0`), origin/dev == local dev.
- Probes: `/tmp/opencode/probe-strip.mjs`, `/tmp/opencode/probe-strip2.mjs`, `/tmp/opencode/review-measure.mjs`.
- Deploy log `50-projects/p003-opencode-fork/testing/deploy-4447.log` (pid 2999326), server log `web-4447.log`.
