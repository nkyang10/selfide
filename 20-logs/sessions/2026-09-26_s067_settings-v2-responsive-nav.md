# s067 — Settings v2: responsive category nav (narrow screens)

- **Date:** 2026-09-26 (UTC)
- **Owner:** agent (user: mark)
- **Scope:** `packages/app/src/components/settings-v2/dialog-settings-v2.tsx` + `settings-v2.css` only. `packages/ui` read-only study. Small, contained change — no redesign.

## Task (user)

On desktop, Settings v2 shows the left category column (General/Shortcuts + Servers/Providers/Models) beside the
key/value content. On narrow screens the browser keeps a side column (240px desktop → 144px <640px), so key/value
rows get squeezed. Goal: give key/value the important width on narrow screens — e.g. categories as a horizontal tab
strip. Constraints: no large-scale redesign; **study whether plain JS+CSS responsiveness can do it**.

## Study findings — is it JS+CSS only?

**Yes, essentially — one small markup flatten is the only extra needed.** Mechanism:

| Layer | Fact | Consequence |
|---|---|---|
| Dialog | `DialogV2 size="x-large"` → `width: min(100vw - 32px, 980px)`, `height: min(100vh - 92px, 600px)` (`ui/v2/dialog-v2.css:173-176`) | on a 390px phone the dialog is only 358px wide — every px matters |
| Root | `[data-orientation="horizontal"] {flex-direction:column}` / `vertical {row}` (`ui/v2/tabs-v2.css:14-20`) | flipping the attribute reflows the whole shell |
| List | vertical settings variant: `width:240px; min-width:200px; height:100%; border-inline-end` (tabs-v2.css:178-187); horizontal generic: `width:100%; overflow-x:auto` (31-36) | vertical is a fixed side column, horizontal is already a top strip |
| Content | `flex:1; overflow:auto` (tabs-v2.css:22-25) | takes whatever width is left → content wins automatically |
| Kobalte | orientation flows through `TabsContext` as an **accessor**; root + list render `data-orientation`, list also `aria-orientation`; `TabsKeyboardDelegate` calls `this.orientation()` at event time (tabs-root.tsx:177/193, tabs-list.tsx:107-108, tabs-keyboard-delegate.ts:39-66) | **runtime orientation switching is fully reactive & safe** — arrow keys and a11y semantics follow, no remount/state loss |

**Why pure CSS alone was rejected:** the nav's inner markup was 7 nested Tailwind `flex flex-col` divs. Turning it
into a row with CSS alone needs `display:contents` on every wrapper level (brittle, breaks on any markup tweak) and
still can't remove the section titles / version footer. Instead the list content was flattened to two semantic group
divs (`.settings-v2-nav` > 2× `.settings-v2-nav-group` + footer) — same line count, far simpler, and CSS then does
`display: contents` in narrow mode so the 5 triggers become one row.

**Second squeeze found (unasked, in scope of the goal):** `.settings-v2-tab-header`/`.settings-v2-tab-body` use a
fixed `40px` inline padding at every width. At 358px dialog width that ate 80px of the ~214px content column. Added a
`max-width: 639px` override → 16px, worth ~48px more for key/value.

## Changes (uncommitted; deployed to :4447)

**`dialog-settings-v2.tsx`** (4 small edits)
1. import `onCleanup, onMount`.
2. `const [narrow, setNarrow] = createSignal(false)` + `onMount` with `matchMedia("(max-width: 639px)")` (initial
   value + `change` listener, cleaned up via `onCleanup`).
3. `orientation={narrow() ? "horizontal" : "vertical"}` (was hardcoded `"vertical"`).
4. List content flattened: `.settings-v2-nav` > 2× `.settings-v2-nav-group` (SectionTitle + its triggers) +
   `.settings-v2-nav-footer`. Trigger values/icons/labels untouched.

**`settings-v2.css`**
- Added `.settings-v2-nav` (column, space-between, gap 12) + `.settings-v2-nav-group` (column, gap 6) for desktop.
- Added a `[data-orientation="horizontal"]` block: list becomes a non-shrinking, `overflow-x:auto` strip with a
  `border-bottom`; nav becomes a `row` (`width: max-content; min-width: 100%`); groups `display: contents`; section
  titles + version footer hidden; triggers get 32px height, `padding-inline: 8px`, radius 4 and the **same**
  hover/selected tokens as desktop (`bg-layer-03` / `text-base` / `text-muted`).
- **Deleted** the now-dead `@media (max-width:639px) { list: width 144px }` block (orientation is never `vertical`
  below 640px any more).
- Added `@media (max-width: 639px)` header/body padding 40px→16px.

Breakpoint 640px = the file's existing mobile breakpoint (row-wrap + control-stacking rules).

## Verification (live :4447, build `1.1.20260926074652`, pid 2922029)

| | DESKTOP 1280×800 | NARROW 390×844 |
|---|---|---|
| `data-orientation` / `aria-orientation` | vertical / vertical | horizontal / horizontal |
| list | 240×600, left (x=150) | 358×45, top strip (y=122) |
| content panel | 740 (x=390) | **358 (full width)** |
| 5 triggers | stacked (y 142/176/394/428/462) | one row (same y=134; x 32/106/193/280/367) |
| section titles / footer | visible / visible | hidden / hidden |
| nav groups `display` | flex | contents |
| key/value row width | 620 | **286** (was ~134 before this change) |

- ArrowRight in narrow mode moves the selection (horizontal keyboard nav correct); clicking Models renders its panel.
- `bun typecheck` (packages/app) clean · `oxlint` 0 errors (7 pre-existing warnings in `general.tsx`) ·
  `test:unit` 749 pass / 1 fail = **pre-existing** i18n-parity failure from the uncommitted RSS WIP (proved by
  git-stash A/B: fails identically with my 2 files removed).
- Bundle proof: served settings chunk `index-C88LRohd.js` contains `max-width: 639px` and `settings-v2-nav-group`;
  `orientation:"vertical"` is gone.

## Pitfalls hit (worth remembering)

- **The Read tool served stale/deduped content for `dialog-settings-v2.tsx`** (showed a different, newer-looking file
  with `Icons.Settings`/`versionText`/`Show` import). Bash `cat -n` / `sed` was the only reliable ground truth; two
  edits failed with "oldString not found" before I switched to bash-verified strings.
- **The `git stash push/pop` A/B test reverted my TSX edits** and the first rebuild shipped a stale bundle. Verified
  via bundle grep, re-applied, redeployed. Lesson: A/B-test with `git stash` only on files you have not hand-edited in
  the same session, or copy the file aside first.

## Evidence

- Live server: `50-projects/p003-opencode-fork/testing/web-4447.log`, deploy log `testing/deploy-4447.log`
- Bundle: `opencode/packages/app/dist/assets/index-C88LRohd.js` (settings chunk) + `index-ly103vOg.css`
- Measurement scripts: `/tmp/opencode/verify-settings-responsive.mjs`, `/tmp/opencode/shots.mjs`
- Screenshots (not visually reviewed by the agent — no image input): `/tmp/opencode/shot-desktop-1280.png`,
  `/tmp/opencode/shot-narrow-390.png`

## Status / follow-ups

- **SHIPPED:** committed `fa41da0` "feat(app): make v2 settings tabs horizontal on narrow screens" (exactly the 2
  files, 74+/42-) and pushed `origin/dev` (`ab47c38..fa41da0`). **Caveat:** the commit + push were executed by a
  **parallel workspace process**, not by this agent — the user asked to commit/push while s067 was closing out, and a
  concurrent session in the same working tree did it. The split came out correct: `ab47c38` carries the earlier RSS
  WIP (7 files, incl. its own AGENTS.md notes), `fa41da0` only the settings change. Verified after the fact:
  `origin/dev == local dev == fa41da0`, the pushed tree contains the matchMedia signal + orientation ternary +
  `.settings-v2-nav` markup, and the pre-push gate `bun turbo typecheck` is **30/30 green** on that commit. → FU-075 closed.
- Pre-existing i18n-parity failure (RSS WIP added keys to `en.ts` + `tk.ts` only; now committed as `ab47c38`) → FU-076.
- User should eyeball it on the phone (the whole point is the narrow-screen feel).
