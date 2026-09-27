# s077 — FE-025 plan: the "Changed files" group collapses to one row by default

- **Date:** 2026-09-27 (UTC) · **Session:** s077
- **Request:** *"opencode fork project webui plan do modified file default collapse like todo list. default collapse, toggle on user manual click."*
- **Outcome:** **PLAN ONLY — zero feature code written.** Plan doc: `50-projects/p003-opencode-fork/notes/plan-diff-summary-collapse.md`; decision **DEC-052**; follow-up **FU-095**.
- **Target:** the fork's web UI (`packages/app`), session timeline.

## What the user decided (asked before planning, 3 questions)

1. **Scope** → the **whole group** collapses to one row (group → file list → diff), not just the header.
2. **Persistence** → **per session**, survives reload and tab switch.
3. **Accessibility** → yes, fix the bare `<span onClick>` / `<div onClick>` controls while in there.

## What I found before writing anything

The component already exists with **two** collapse axes; the one the request is about was missing.

- **Live component:** `TimelineDiffSummaryRow`, `packages/app/src/pages/session/timeline/message-timeline.tsx:204-284`, mounted at `:1356-1365` inside `TimelineRowFrame` (stamps `data-timeline-row="DiffSummary"`).
- **Axis A (existing):** a **10-file cap** (`showAll`, `:208`) driven by the `Show all` / `+N more files` controls. Truncation, not collapse.
- **Axis B (existing):** a Kobalte `Accordion` per file, **already collapsed by default** (`:234-275`).
- **The actual gap:** the **file list itself is always expanded** — up to 10 rows, ~440px of chrome. That is what "default collapse" targets, so the change is a **third axis around the whole group**, not a change to A or B.
- **State today is local** (`createStore`, `:207-210`) and the row is **virtualised** (`@tanstack/solid-virtual`), so A and B **already reset on scroll-away-and-back** — a pre-existing bug. The new state must not inherit it.
- **Dead duplicate:** `packages/session-ui/src/components/session-turn.tsx:436-527` carries the same markup and the same `data-slot`s (Storybook-only) and still shares the live CSS. Not touched; recorded as drift.
- **i18n:** the keys are `ui.*` in **`packages/ui/src/i18n/`** (66 locales, enforced by `packages/app/src/i18n/parity.test.ts`), *not* `packages/app/src/i18n`. Existing: `diffs.changed.{one,other}`, `diffs.showAll`, `diffs.showLess`, `diffs.more`.
- **The "todo list" the user means** is the composer's todo dock — `session-todo-dock.tsx:110-215`: `role="button" tabIndex="0"` + Enter/Space, a `chevron-down` `IconButton` rotated by `transform`, `aria-hidden` on the list, and a **persisted** `collapsed` flag.

## The plan in one paragraph

The existing 44px sticky header becomes a real toggle (`role="button" tabIndex="0" aria-expanded`, Enter/Space,
trailing chevron) and a `<Show when={open()}>` wraps the per-file `Accordion` — so a collapsed row is 44px
instead of ~440px. `open` is a new `SessionView.diffSummaryOpen?: boolean` accessor beside `todoCollapsed`
(`layout.tsx:75`, `:865-876`); **"default collapse" is the absence of state** (`?? false`), so **no `migrate`
branch and no `layout.v6` bump**. `MessageTimeline` already has `useSessionKey()` (`:332`), so **no new prop**
and no change at the `session.tsx:2089` call site. `Show all` and `+N more files` become real
`<button type="button">`s **with `stopPropagation()`** — they live inside the header that just became
clickable, so forgetting this is the single most likely defect. **Zero new i18n keys**: the chevron is
`aria-hidden`, the existing plural is the accessible name.

## Functional view (F1-F10) — the feature, then the order

The plan is organised by **what the user gets**, not by file/phase. Build order is a derived §4.

| # | function | now → new |
|---|---|---|
| **F1** | the group is one row until you ask for more | file list permanently visible → `<Show when={open()}>` so the collapsed row is 44px, not ~440px |
| **F2** | click anywhere on the row to open/close it | header inert → `role="button" tabIndex="0" aria-expanded` + Enter/Space + trailing chevron, copied from the todo dock |
| **F3** | per-file diffs keep working | **unchanged** — already default-collapsed; only verify the 44px sticky offset still lines up |
| **F4** | "I opened it" survives reload, tab switch, scroll-away | new `SessionView.diffSummaryOpen?` beside `todoCollapsed`; today the row's local `createStore` already resets on virtualised unmount |
| **F5** | it has to fit a phone | one more element in a 358px box at 390px → `margin-left:auto` chevron; label truncation only if measurement demands it |
| **F6** | the 10-file cap survives and becomes reachable | `<span onClick>` `opacity:0`-until-hover and `<div onClick>` → real `<button type="button">`s + `:focus-within`; cap semantics unchanged; **both must `stopPropagation()`** |
| **F7** | screen reader describes it, with no translation debt | `aria-expanded` on the header, chevron `aria-hidden`; honest labels would need 66 `packages/ui` locales, so none are added |
| **F8** | one pure function extracted | `diff-summary-state.ts` + test — the app has **zero** `*.test.tsx`, so only pure logic is assertable |
| **F9** | the tests that assert today's behaviour are updated on purpose | 2 specs assert the *expanded* list; each opens the group first, and a new case proves F4's persistence |
| **F10** | the group stays sticky and offsets line up | unchanged by design; **verify** 44px in both states and that the chevron does not fight the per-file headers |

Build order (derived): 1 F4 store · 2 F8 logic · 3 F1/F2/F3/F6/F7 behaviour + CSS · 4 F9 tests · 5 F5/F10 live checks.
Step 5 needs a rebuild (`deploy-web-4447.sh --detach`, **user's OK**, and FE-025 must be committed **alone** —
s076's uncommitted FE-023/024 WIP is still in the tree).

## Traps written down for the implementer

1. `Show all` / `+N more` bubble into the header toggle unless stopped.
2. Two e2e specs assert the *expanded* list (`timeline-stability/interaction.spec.ts:176-231`,
   `session-timeline-projection.spec.ts:131-162`) and **will** red until they open the group — that is the
   feature working, not a regression.
3. `--sticky-accordion-offset: 44px` (`:236`) depends on the header staying 44px **in both states**; measure,
   don't assume.
4. The virtualiser's `timelineCache` (`:99`, `:617`) means a row scrolled away and back must still read as
   collapsed — this is the payoff of persisting.
5. `Accordion.Item value={diff.file}` cannot collide because `uniqueSummaryDiffs` dedupes upstream.
6. `packages/app/AGENTS.md` requires a **production benchmark baseline before** changing timeline code.

## Housekeeping found (not in the feature)

- Axis A/B state is lost on virtualised remount (pre-existing) — a follow-up could move both into the same store.
- The dead `session-ui/session-turn.tsx` duplicate is a permanent divergence trap.
- `session-turn-diffs-toggle` at `opacity: 0` until hover also makes it invisible to **touch** users until they
  tap — a mobile reason the a11y fix is not optional polish.

## Requirements confirmed with the user (s077, after the plan)

1. **Scope** → the whole group collapses; **default collapsed, click toggles.** Confirmed verbatim.
2. **Persistence** → **option A: one flag for the whole session** (chose over a per-row `userMessageID` list),
   accepting that opening one turn's list leaves the session's other turn-lists open. Recorded as an accepted
   behaviour so it is not re-investigated later.
3. **Row content** → *"I will notify changes in number of file changed and total number of line and then toggle
   to view manually."* Verified **already true**: the count comes from
   `language.plural("ui.sessionTurn.diffs.changed", …)` and the line total from `<DiffChanges changes={props.diffs}>`,
   which sums `additions`/`deletions` across the **whole array** (`diff-changes.tsx:9-19`) — both **required**
   fields (`schema/src/file-diff.ts:6-7`). So the feature **adds and changes no number**.
4. **Format** → keep the `+12 −4` split (not one combined total; that would need a plural key × 66 locales).
5. **Zero-change turns** → keep the tally hidden (rename-only / binary, the `total() > 0` gate).

Net: the whole feature is a `<Show>` around the body, a toggle on the header, one persisted boolean, and a
`<span onClick>` → `<button type="button">` conversion. **Zero new i18n keys.**


## IMPLEMENTED (2026-09-27, after the user said "go")

**Status: CODE COMPLETE, every gate green — NOT committed, NOT built into the binary, NOT deployed.**

### Changed (fork `dev` @ `d04b79e`, 5 modified + 3 new, +160/−59 tracked)

| file | change |
|---|---|
| `packages/app/src/context/layout.tsx` | **F4** `SessionView.diffSummaryOpen?: boolean` + accessor beside `todoCollapsed` (+16) |
| `packages/app/src/pages/session/timeline/message-timeline.tsx` | **F1 F2 F6 F7** header toggle, `<Show>` body, chevron, `<button>` conversions |
| `packages/session-ui/src/components/session-turn.css` | **F2 F5 F6 F10** chevron rotation, `:focus-visible` ring + opacity, button resets, label ellipsis |
| `packages/app/src/pages/session/timeline/diff-summary-state.ts` + `.test.ts` | **F8** new, 5 unit cases |
| `packages/app/e2e/regression/session-timeline-diff-summary-collapse.spec.ts` | **F9** new, 8 e2e cases |
| `.../session-timeline-projection.spec.ts`, `.../timeline-stability/interaction.spec.ts` | **F9** open the group before the old assertions; scoped the loose `/show all/i` locator |
| fork `AGENTS.md` | +63 lines so a future agent gets the constraints |

### Gates

- `bun typecheck` (app) clean · `bun typecheck:e2e` clean
- unit **775 → 780** (+5 = exactly the new file), **0 fail**; baseline proven by `git stash push -u` and re-running
- i18n parity **5/5, 979 assertions** — **no new key**, zero translation debt
- `oxlint` on the 7 touched files: **0 errors**, 41 warnings all on pre-existing lines. (Whole-app lint has 1
  pre-existing error — an octal literal in `session-ui/src/v2/components/prompt-input/index.tsx:172`.)
- `bun run build` ✓, and the built bundle + CSS were probed to confirm the new markup and that the new chevron
  rule does not collide with the per-file one
- e2e: new spec **8/8**; `session-timeline-projection` **5/5**; `collapse-state` + `shell-outline` + new spec
  **19 pass**; full `timeline-stability` **43/44**
- **Benchmark** (`packages/app/AGENTS.md` requires one *before* touching timeline code): **44px collapsed vs
  393px expanded** (12 files) = 349px saved per group; header **44px in both states** so
  `--sticky-accordion-offset: 44px` still holds; first file row 50px below the header (no overlap); at
  **390×844** no page-level horizontal scroll and the label is not clipped.

### Two pre-existing failures — proven NOT mine

Both reproduce identically with all my files `git stash push -u`'d away:
- `session-timeline-lifecycle-state.spec.ts:74` — `[data-timeline-row="Thinking"]` expected 0 (FE-022 WIP)
- `timeline-stability/adverse.spec.ts:82` — "preserves an explicit shell state across virtualization"

### Three of my own mistakes the runs caught

1. `as SummaryDiff` in the unit test → oxlint `no-unsafe-type-assertion`; fixed with `satisfies SnapshotFileDiff[]`.
2. Invented the CSS token `--border-focus-base` (does not exist) → corrected to the real v1 `--border-focus`.
3. In the e2e I asserted `getByText(/show all/i)` had count 0 — **red**: the Review panel's `"Show all lines"`
   matches the same regex (a pre-existing loose locator my negative assertion exposed). Scoping it revealed a
   **second** mistake: I had assumed `Show all` lives in the collapsible body, but it lives in the **header**,
   so it is rendered in both states — only `+N more files` and the file list are behind the toggle.

### Still owed (needs the user)

- **Commit** — alone. The tree holds s076's uncommitted FE-023/024 WIP; FE-025's 8 paths are disjoint from it.
- **Build + deploy** — `scripts/deploy-web-4447.sh --detach` kills this session's listener. The live :4447
  therefore does **not** have FE-025 yet.

## Records updated

- `50-projects/p003-opencode-fork/notes/plan-diff-summary-collapse.md` — the plan (new; rewritten on request into the **functional view** F1-F10 with the build order derived in §4)
- `40-knowledge/decisions-log.md` — **DEC-052** (new)
- `10-status/open-followups.md` — **FU-095** (new, open, awaiting go-ahead)
- `10-status/current-state.md` — snapshot
- `20-logs/command-log.md` — 22 rows

**Nothing was built, committed, or deployed.** The fork tree still holds only the parallel **s076 FE-023/024
WIP** (12 code + 62 locale files, uncommitted) — unchanged by this session.
