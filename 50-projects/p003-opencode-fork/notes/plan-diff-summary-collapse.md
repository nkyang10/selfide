# Plan — FE-025 the timeline "Changed files" group collapses to one row by default

> **Status:** PLAN ONLY — no feature code written. Prepared 2026-09-27 (UTC), session **s077**.
> **User request:** *"opencode fork project webui plan do modified file default collapse like todo list.
> default collapse, toggle on user manual click."*
> **User's three decisions** (asked before planning):
> 1. **Scope** = the *whole group* collapses to one row (two levels: group → file list → diff), not just the header.
> 2. **State persists per session** (survives reload + tab switch), not in-memory only.
> 3. **Fix the accessibility** of the existing `Show all` / `+N more files` controls while in there.
> **Feature id:** FE-025 (FE-024 was taken by s076). Decision record: **DEC-052**. Follow-up: FU-095.
> **Revision 2 (user-confirmed requirements):** the row's **content is unchanged** — the file count and the
> `+added −deleted` split already ship and are already the *turn total*, so the feature is **only** "make that
> row the default state and make it the click target". Persistence is **option A: one flag for the whole
> session** (the user chose this over a per-row flag, accepting that opening one turn's list leaves the other
> turns' lists open). The `+12 −4` split is kept (not collapsed into one number) and the zero-change case
> (rename-only / binary) keeps hiding the tally. **No new i18n key anywhere.**
> **Revision 1:** re-organised into a **functional view** (§3) — the same content, now grouped by *behaviour
> the user gets* rather than by file/phase. The derived build order is §4.

---

## 0. Executive summary

The component already exists and already *has* two collapse axes. The change is **one new outer axis plus a
store key** — no new component library, no new i18n key, no protocol/engine change.

| What we need | Reality in the fork |
|---|---|
| A collapsed-by-default "N Changed files" row | ✅ `TimelineDiffSummaryRow` (`packages/app/src/pages/session/timeline/message-timeline.tsx:204-284`) already renders a sticky 44px header + a Kobalte `Accordion` of files. Only the *outer* wrapper is missing. |
| "like todo list" | ✅ Exact precedent exists in the same product: the composer **todo dock** is a `role="button" tabIndex={0}` single row with a chevron `IconButton`, a persisted `collapsed` flag, and `aria-hidden` on the list (`packages/app/src/pages/session/composer/session-todo-dock.tsx:110-215`). |
| Persist the open/closed state per session | ✅ `SessionView.todoCollapsed` already does exactly this (`context/layout.tsx:75`, accessor `:865-876`, consumed at `pages/session.tsx:2144-2145`). One new optional boolean + one accessor. |
| Accessible toggle | ⚠️ The existing `Show all` (`:228`, a bare `<span onClick>`) and `+N more files` (`:277`, a bare `<div onClick>`) have **no** `role` / `tabIndex` / `aria-expanded`, and `Show all` is `opacity: 0` until hover → literally invisible to a keyboard user. Fixing this is in scope (user decision 3). |
| New i18n keys | ✅ **None needed.** `ui.sessionTurn.diffs.changed.{one,other}` is the accessible name; `showAll` / `showLess` / `more` already exist. The new chevron is `aria-hidden` — see §3.6. |

**Total: 1 new outer collapse, 1 new persisted boolean, 1 accessibility pass, 1 narrow-viewport fit check.
4 source files, ~+90/−20 lines, no new dependencies, no engine/server change, no build-system change.**

---

## 1. Facts that shape the design (verified in the working tree, not from memory)

### 1.1 What renders today

`packages/app/src/pages/session/timeline/message-timeline.tsx:204-284` — module-local
`function TimelineDiffSummaryRow(props: { diffs: SummaryDiff[] })`. Mounted from
`renderTimelineRow` at `:1356-1365` inside `TimelineRowFrame` (which stamps
`data-timeline-row="DiffSummary"` and `data-message-id`).

```
<div data-slot="session-turn-diffs" data-component="session-turn-diffs-group" data-show-all>
  <div data-slot="session-turn-diffs-header">              ← sticky, 44px, ALWAYS VISIBLE
    <span data-slot="session-turn-diffs-label">3 Changed files</span>
    <DiffChanges/>                                        ← +12 −4 tally
    <span data-slot="session-turn-diffs-toggle">Show all</span>   ← F6 (10-file cap)
  </div>
  <div data-component="session-turn-diffs-content">        ← ALWAYS VISIBLE  ← F1 collapses this
    <Accordion multiple value={expanded()} …>              ← F3, per-file, all collapsed by default
      <For each={visible()}>  … <Accordion.Item value={diff.file}>  ← 1 row per file
    </Accordion>
    <div data-slot="session-turn-diffs-more">+2 more files</div>   ← F6
  </div>
</div>
```

So today: **F3 (per-file diff) is already default-collapsed**; **F6 is a 10-file cap, not a collapse**; and the
**file list itself is always expanded**. The user is asking for **F1** — a new axis around the whole thing,
which is precisely what makes it look like the todo dock (one line, chevron, tap to reveal).

### 1.2 The state today is *local* and therefore lost on virtualised remount

`const [state, setState] = createStore({ showAll: false, expanded: [] as string[] })` (`:207-210`).

The timeline is **virtualised** (`@tanstack/solid-virtual`, `VirtualTimelineRow` at `:1385-1449`). The row is
unmounted when it scrolls out of the window, so `showAll` + `expanded` **reset to defaults on scroll-away and
back**, and on any remount. This is a pre-existing bug, not one we introduce — but it is the strongest
argument for putting the *new* state in the persisted store rather than beside it.

### 1.3 The persisted per-session store already has the exact pattern

`packages/app/src/context/layout.tsx`:

- `type SessionView` (`:68-76`) — `scroll`, `reviewOpen?`, `reviewMode?`, `reviewFile?`, `pendingMessage?`,
  `pendingMessageAt?`, **`todoCollapsed?: boolean`**.
- Accessor (`:865-876`) — `todoCollapsed: { get: () => s().todoCollapsed ?? false, set(collapsed) {…} }`,
  creating the session row on first write (`{ scroll: {}, todoCollapsed: collapsed }`).
- Backing store: `Persist.serverGlobal(serverSdk().scope, "layout", ["layout.v6"])` + `persisted(...)` at
  `:270-308`, with `sessionView: {} as Record<string, SessionView>` (`:300`) and a `MAX_SESSION_KEYS = 50`
  prune (`:314`).

**No migration is required**: `SessionView` is an *optional-field* record and the existing `migrate` (`:183-268`)
only rewrites specific shapes (`sidebar.workspaces`, `fileTree`, `review.panelOpened`, `sessionTabs`). A new
optional boolean simply reads as `undefined` → `?? false` for every existing browser. Do **not** bump
`layout.v6` for this.

### 1.4 The todo-dock precedent (what "like a todo list" means concretely)

`packages/app/src/pages/session/composer/session-todo-dock.tsx:110-215`:

- header `<div role="button" tabIndex={0} onClick onKeyDown>` (Enter/Space, `preventDefault`) — `:111-126`
- a `chevron-down` `IconButton` with `transform: rotate(turn() * 180deg)` + `aria-label` swapped by state — `:181-197`
- the list wrapper carries `aria-hidden={props.collapsed}` — `:201-213`
- the collapsed flag is owned by the parent: `session.tsx:2144-2145` reads
  `view().todoCollapsed.get()` and calls `view().todoCollapsed.set(!…)`

We mirror this. We do **not** invent a third interaction style.

### 1.5 CSS is shared with a dead copy — a real trap

`packages/session-ui/src/components/session-turn.css` styles this component and everything is nested under
`[data-component="session-turn"]`. It is **globally imported** (`packages/app/src/index.css:2` →
`@opencode-ai/session-ui/styles` → `styles/index.css:9`).

The same markup exists a second time in
`packages/session-ui/src/components/session-turn.tsx:436-527` (state at `:242-270`) — **dead in the app**
(only the Storybook playground imports it) but its CSS is live. Editing only the `message-timeline.tsx` copy
leaves the two divergent, which is already true today. The plan touches only the live copy and says so.

Relevant existing rules:

| line | rule | why it matters here |
|---|---|---|
| `session-turn.css:103-114` | `[data-slot="session-turn-diffs-header"]` `display:flex; align-items:center; gap:8px; position:sticky; top: var(--sticky-accordion-top,0); height:44px; z-index:20; background: var(--v2-background-bg-base)` | The header **is** the collapsed row (F1/F2). Sticky behaviour is free — keep it. |
| `:116-124` | `session-turn-diffs-label` tabular-nums, no truncation, no `min-width:0` | Drives the narrow-viewport fit check (F5). |
| `:125-143` | `session-turn-diffs-toggle` `opacity:0` → `:hover` / `[data-show-all]` → `opacity:1` | Keyboard- **and** touch-invisible. F6. |
| `:212-221` | chevron `rotate(-90deg)`, `[data-slot="accordion-item"][data-expanded] … { rotate(0) }` | The **per-file** chevron state hook. The new **outer** chevron needs its own state attribute; it must not be matched by this rule. |
| `message-timeline.tsx:236` | `style={{ "--sticky-accordion-offset": "44px" }}` on the inner `Accordion` | The per-file sticky headers sit 44px below the top because the group header is 44px tall. **Unchanged by this feature** — the group header keeps its 44px height whether collapsed or not. Verify, do not assume. |

### 1.6 What the tests already pin (so we do not silently break them)

- `e2e/performance/timeline-stability/interaction.spec.ts:176-231` — seeds **12** diffs, clicks
  `getByText(/show all/i)`, then clicks `[data-slot="session-turn-diff-trigger"]` first, and asserts a
  visual-stability plan (no overlap, `label-stability`, ≤2 motion reversals). With the group now collapsed by
  default this spec **will fail at line 211** unless it first opens the group.
- `e2e/regression/session-timeline-projection.spec.ts:131-162` — seeds **11** diffs, asserts the `DiffSummary`
  row is visible and `getByText(/show all/i)` is visible. `showAll` only renders when `overflow() > 0`; it
  lives **inside the group body**, so once the body is collapsed this assertion is wrong too.
- `e2e/regression/session-timeline-lifecycle-state.spec.ts:74-107` — asserts the row is **absent** while the
  turn is busy/retrying and appears at `idle`. Unaffected (row still renders; only its body is hidden).
- `e2e/regression/session-timeline-shell-outline.spec.ts:123-159` — asserts every non-`TurnGap` framed row has
  `overflow-clip-margin: 0.5px`. Unaffected.
- `e2e/regression/session-timeline-collapse-state.spec.ts:255-268,374-386` — seeds
  `localStorage["settings.v3"]` and resolves expansion via `aria-expanded` /
  `[data-component="collapsible"][data-expanded|data-closed]`. Its `expectExpanded` helper will **not** work
  verbatim on a Kobalte `Accordion`; we need our own small reader (see §3.7).
- Unit: **there is no `*.test.tsx` anywhere in `packages/app/src`** — zero component-render unit tests. So the
  pure-logic part (below) is the only thing unit-testable, and it is the part worth extracting.

### 1.7 The row's usable width

`renderTimelineRow` mounts the row in `<div class="w-full px-4 md:px-5">` (`:1360`), so at a 390px phone the
content box is **358px** and the header must fit its label + tally + `Show all` + a new chevron into it (§3.5).

---

## 2. Why this is one new axis and not a change to an existing one

| axis | today | request | verdict |
|---|---|---|---|
| per-file diff (`expanded`) | collapsed by default | "default collapse" | already satisfied — **F3, unchanged** |
| 10-file cap (`showAll`) | a truncation control | "toggle" | not a collapse — **F6, unchanged** |
| the file list itself | always expanded | "default collapse" | **← the gap; F1 is the new work** |

---

## 3. Functional view — the behaviours this delivers

Each item is a **function the user gets**, with its current behaviour, the new behaviour, where it lands, and
how to accept it. Read this section as the feature; §4 is only the ordering.

### F1 — The group is one row until you ask for more

| | |
|---|---|
| **Now** | the "3 Changed files" header is followed by a permanently visible list of up to 10 file rows |
| **New** | collapsed, the whole group is the **44px header and nothing else**; the file list does not exist in the DOM until you open it |
| **Lands in** | `message-timeline.tsx:216-283` — `<Show when={open()}>` around the existing `data-component="session-turn-diffs-content"` block |
| **Why `<Show>` and not `display:none`** | the row must **shrink** so the virtualiser re-measures it; a hidden-but-present body would keep reserving ~400px |
| **Row content is NOT changed** | the user asked for the row to *notify* the file count and the line changes, then toggle. It already does: `language.plural("ui.sessionTurn.diffs.changed", props.diffs.length)` gives the count (correct for 1 file too), and `<DiffChanges changes={props.diffs}>` at `:226` is handed the **whole array** and **sums** `additions`/`deletions` across every file (`packages/ui/src/components/diff-changes.tsx:9-19`) → `+12 −4` is the **turn total**. `additions` / `deletions` are **required** `Schema.Finite` on `SnapshotFileDiff` (`packages/schema/src/file-diff.ts:6-7`), so there is no missing-value case. **This feature adds no number and changes no number** |
| **Split, not a single total** | the `+12 −4` split is **kept** (user-confirmed). `DiffChanges` computes an internal `total` (`:20`) but only renders the split; a single "34 lines changed" figure would need a new plural key in `packages/ui/src/i18n/` → **66 locale files** → `i18n/parity.test.ts` fails |
| **Zero-change case stays hidden** | `DiffChanges` renders only when `total() > 0` (`:41`), so a rename-only or binary turn shows just "3 Changed files" with no tally. **Kept as-is** (user-confirmed) — no new zero-case string |
| **Accept** | a 12-file turn measures **≤ 60px** collapsed (44px header + the row frame's own padding) vs ~440px today, and still reads `12 Changed files  +57 −19  ›` |

### F2 — Click anywhere on the row to open or close it

| | |
|---|---|
| **Now** | the header is inert; the only things you can click are `Show all` and `+N more files` |
| **New** | the header is a toggle: click, or focus + <kbd>Enter</kbd> / <kbd>Space</kbd> |
| **Lands in** | `role="button" tabIndex={0} aria-expanded={open()}` + `onClick` + `onKeyDown` on `session-turn-diffs-header`, copied from the todo dock (`session-todo-dock.tsx:111-126`); a `session-turn-diffs-chevron` at the trailing edge with `margin-left:auto`, rotated by CSS on `[data-component="session-turn-diffs-group"][data-expanded]` |
| **Uniform for 1 file** | a single changed file still shows the chevron. The count plural (`diffs.changed.one`) already says "1 Changed file"; hiding the chevron there would be a special case with no benefit |
| **Accept** | mouse, touch, and keyboard each open/close; `aria-expanded` flips; the chevron rotates |

### F3 — Per-file diffs keep working exactly as they do

| | |
|---|---|
| **Now** | each file row is a Kobalte `Accordion.Item`, collapsed until clicked; `opened()` gates the body so a diff is only mounted while open |
| **New** | **unchanged** — the user explicitly asked for a *group* collapse, and F3 already defaults collapsed |
| **Lands in** | nothing |
| **Consequence to verify** | `--sticky-accordion-offset: 44px` (`:236`) exists because the group header is 44px. It must still be 44px in **both** states or the per-file sticky headers will overlap when expanded. Measure, do not assume |
| **Accept** | expanding the group then clicking a file shows the diff with the file's sticky header sitting exactly 44px below the top |

### F4 — "I opened it" survives a reload, a tab switch, and a scroll-away

| | |
|---|---|
| **Now** | the row's `createStore` (`:207-210`) is component-local, and the row is **unmounted** by the virtualiser, so `showAll` and `expanded` already **reset on scroll-away-and-back** — a pre-existing bug |
| **New** | the new open/closed flag lives in the per-session layout store, so it survives reload, a tab switch, and a virtualised remount |
| **One flag for the whole session (option A — the user's call)** | the flag is `SessionView.diffSummaryOpen`, a single boolean, **not** a list of open row ids. The accepted consequence: opening turn 1's list also leaves turn 2's and turn 3's lists open, because they all read the same flag. Chosen over a per-row flag (keyed by `userMessageID`, persisted as a `string[]` like the Review panel's `reviewOpen`) for simplicity, and it matches the single `todoCollapsed` precedent. The alternative is still a small change if the user later wants per-row independence |
| **Lands in** | `SessionView.diffSummaryOpen?: boolean` (`layout.tsx:68-76`) + a `diffSummaryOpen` accessor beside `todoCollapsed` (`:865-876`); read from `TimelineDiffSummaryRow` via `useLayout().view(sessionKey)` |
| **No migration** | "default collapse" is the **absence** of state (`?? false`), not a written `false`, so no `migrate` branch and **no `layout.v6` bump** (§1.3) |
| **No new prop** | `MessageTimeline` already holds `const { params, sessionKey } = useSessionKey()` (`:332`) and the layout provider sits above it, so the `session.tsx:2089` call site does not change |
| **Scope discipline** | only F4's flag is persisted. F6's `showAll` and F3's `expanded` stay local — mixing two durability stories in one change is how the existing reset bug becomes permanent debt |
| **Accept** | open a file to review → reload → the group is still open; scroll a 12-file group out of view and back → still open; a second turn's group in the same session is open too (the accepted consequence) |

### F5 — It has to fit a phone

| | |
|---|---|
| **Now** | at 390px the 358px content box holds the label + tally + `Show all`, and the label has no truncation or `min-width: 0` (`session-turn.css:116-124`) |
| **New** | a chevron is added, so the row has one more element. It must not push the tally off the edge |
| **Lands in** | `session-turn.css` — `margin-left:auto` on the chevron, and a `min-width: 0` + `truncate` on the label **only if** the measurement below shows a problem |
| **Accept** | at **390×844**: label, `+N −M` tally and chevron all fit with no horizontal scroll and no clipped text, in both states |

### F6 — The 10-file cap and its two controls survive, and become reachable

| | |
|---|---|
| **Now** | `Show all` (`:228`) is a bare `<span onClick>` with no `role` / `tabIndex` / `aria-expanded`, and CSS `opacity: 0` until the group is hovered (`session-turn.css:125,137,141`); `+N more files` (`:277`) is a bare `<div onClick>`. On **touch** the `Show all` control is effectively invisible until the user happens to tap it |
| **New** | both become real `<button type="button">`s; the cap and the exact `showAll` / `overflow` semantics are **unchanged**; both stay **inside** the collapsible body (a collapsed "3 Changed files" is the whole truth; the cap only applies once you are looking at the list) |
| **Lands in** | `message-timeline.tsx:228` and `:277`; `session-turn.css:125-143` (`opacity` also lifted by `:focus-visible` / `:focus-within`) plus a button reset so the new `<button>`s look identical to the `<span>`/`<div>` they replace |
| **The likeliest defect in this whole change** | both controls are **children of the header that F2 just made clickable** → they must `event.stopPropagation()`, or clicking `Show all` also collapses the group |
| **Accept** | `Show all` and `+N more` are tab-reachable, visible on focus, and neither toggles the group |

### F7 — A screen reader describes the control correctly, with no translation debt

| | |
|---|---|
| **Now** | the header text `ui.sessionTurn.diffs.changed.{one,other}` is the only description |
| **New** | the header carries `aria-expanded` and is the accessible name. The chevron is **`aria-hidden="true"`** and gets **no** label |
| **Why no label** | an honest label ("Show changed files") does not exist, and `ui.*` keys live in **`packages/ui/src/i18n/`** — **66 locale files** — with `packages/app/src/i18n/parity.test.ts` failing if one is missed. The chevron is decorative; the header text plus `aria-expanded` already describe the control fully |
| **If a tooltip is ever wanted** | add `ui.sessionTurn.diffs.expand` / `.collapse` in `packages/ui/src/i18n/en.ts` + all **66** files, English text **byte-for-byte** (the FU-026 pattern; never invent translations). Note this is the `packages/ui` locale set, **not** `packages/app/src/i18n` |
| **Rejected wording** | `ui.sessionReview.expandAll` / `collapseAll` ("Expand all" / "Collapse all") mean "every file at once" — the opposite of this toggle |
| **Accept** | parity stays 5/5; the control announces its state and its name; no locale file changes |

### F8 — One pure function extracted, because the app has no component tests

| | |
|---|---|
| **Now** | `visible()` / `overflow()` are inline memos (`:213-214`) inside a `.tsx` file, and `packages/app/src` contains **zero** `*.test.tsx` — so they cannot be asserted |
| **New** | `timeline/diff-summary-state.ts` exporting the one non-trivial boolean this change touches — which files are visible given `overflow` and `showAll` — plus `diff-summary-state.test.ts` |
| **Why bother** | it keeps F6's `Show all` / `+N more` rules from silently drifting when the body becomes conditional, and it is the only part of this feature a unit test can reach |
| **Accept** | `bun run test:unit` gains a new test file; the suite does not drop below its current 774 pass / 0 fail |

### F9 — The tests that assert today's behaviour get updated, on purpose

| | |
|---|---|
| **Now** | 2 specs assert the file list is visible and `show all` is clickable (`interaction.spec.ts:176-231`, `session-timeline-projection.spec.ts:131-162`) |
| **New** | each **opens the group first**, then asserts the old things. A second new case in `session-timeline-collapse-state.spec.ts` proves F4's persistence. Both seeded at 11–12 diffs so F6's cap is still exercised |
| **New helper** | a small attribute-based `readDiffGroupOpen(page)` — the existing `expectExpanded` (`collapse-state.spec.ts:374-386`) targets `Collapsible`, not Kobalte `Accordion`, so it cannot be reused verbatim |
| **Accept** | a red run of those 2 specs **before** the edit is the proof the new default took effect; green after. A red run after the edit is a regression |
| **Unaffected, deliberately** | `session-timeline-lifecycle-state.spec.ts` (row absent while busy) and `session-timeline-shell-outline.spec.ts` (clip margin) — the row still renders, only its body is hidden |

### F10 — The whole group must stay sticky and the offsets must still line up

| | |
|---|---|
| **Now** | the group header is `position: sticky; top: var(--sticky-accordion-top,0); height:44px; z-index:20` (`session-turn.css:103-114`), and each file's own sticky header is offset by `--sticky-accordion-offset: 44px` (`:236`) |
| **New** | unchanged — the header *is* the collapsed row, so stickiness is free. What must be **verified** is that the 44px is 44px in both states, and that the new chevron's z-index does not fight the per-file headers |
| **Accept** | scrolling a 12-file group: the group row sticks to the top in both states; expanded, file headers sit below it, not on top of it |

---

## 4. Build order (derived from §3, not the point of the plan)

Only the ordering lives here. Each step is independently gate-able and leaves the app working.

| step | delivers | files | gate |
|---|---|---|---|
| 1 | **F4** store | `packages/app/src/context/layout.tsx` | `bun typecheck` clean (from `packages/app`) |
| 2 | **F8** pure logic | new `timeline/diff-summary-state.ts` + `.test.ts` | `bun run test:unit` — parity 5/5, suite ≥ current 774 pass / 0 fail |
| 3 | **F1 F2 F3 F6 F7** the behaviour | `timeline/message-timeline.tsx`, `packages/session-ui/src/components/session-turn.css` | `bun typecheck` · `oxlint` 0 errors on both files · **`vite build`** · **benchmark baseline compared** (`packages/app/AGENTS.md`: record a production timeline baseline *before* changing timeline code, then compare; the metric is the 12-file row's measured height) |
| 4 | **F9** tests | `e2e/performance/timeline-stability/interaction.spec.ts`, `e2e/regression/session-timeline-projection.spec.ts`, `e2e/regression/session-timeline-collapse-state.spec.ts` | both edited specs green after the new default |
| 5 | **F5 F10** live checks | no source | 390×844 fit in both states; sticky offsets line up expanded |

Step 5 needs the app running, which on this fork means a rebuild: any change under `packages/app` **requires**
`scripts/deploy-web-4447.sh --detach` (fork `AGENTS.md` "Linux deploy" gate — the embedded app must be rebuilt
into the binary). That **kills the :4447 listener**, which is this session's own host, so it needs the user's
go-ahead. It also ships whatever else is in the tree, so `git status` first: **the tree currently holds s076's
uncommitted FE-023/024 WIP (12 code + 62 locale files)**. FE-025 must be committed **alone** (the FU-081
precedent).

---

## 5. Risks and traps

1. **`Show all` bubbling into the header toggle** (F6) — the header becomes clickable and both controls live
   inside it. Must `stopPropagation()`. Highest-probability defect.
2. **Two e2e specs break on the new default** (F9) — they are *supposed* to change; a red run is not a
   regression, it is the plan working. Do not "fix" it by re-defaulting to expanded.
3. **The `44px` sticky offset chain** (F3/F10) — measure both states; do not assume.
4. **Virtualiser re-measurement** — `<Show>` changes the row's height by ~400px. `measure` /
   `observe-element-offset` (both unit-tested) drive the virtualizer's snapshot into `timelineCache` (`:99`,
   `:617`). A collapsed row that is unmounted and remounted must still read as collapsed — which it will,
   because the state is in the store, not the component (§1.2 vs F4). This is the payoff of the user's
   persistence decision.
5. **`Accordion.Item value={diff.file}`** — duplicate paths would collide, but `uniqueSummaryDiffs`
   (`timeline/summary-diffs.ts:4-16`) guarantees uniqueness upstream. No change needed; recorded so a future
   reader does not "fix" it.
6. **66-locale parity** (F7) — any new `ui.*` key breaks `i18n/parity.test.ts`. Avoided; if bypassed, the key
   belongs in `packages/ui/src/i18n/`, **not** `packages/app/src/i18n`.
7. **The dead copy in `session-ui/session-turn.tsx`** shares every `data-slot`, so any new CSS rule also
   applies to it. Harmless (unmounted), but do not be surprised by a selector match in the Storybook.
8. **Two durability stories in one commit** (F4) — persisting F3/F6 alongside F1 is not requested and would
   make the existing reset bug look intentional.
9. **One flag = all rows move together** (F4) — this is the user's chosen option A, **not** a bug. If a
   reviewer's complaint is "I opened one and everything else opened too", the fix is a per-row key, and the
   plan records the shape (`string[]` of open `userMessageID`s, mirroring `reviewOpen` at `layout.tsx:929-991`).

---

## 6. Effort estimate

| function | work | change size |
|---|---|---|
| F4 store | 1 optional field + 1 accessor | ~20 lines, 1 file |
| F1 F2 F3 F6 F7 behaviour + CSS | outer collapse, header toggle, 2 button conversions, chevron, `:focus-within` | ~+70/−20, 2 files |
| F8 logic | 1 extracted function + 1 test | ~+30, 2 files |
| F9 tests | 2 e2e edits + 1 new e2e case + 1 small reader helper | ~+60, 3 files |
| F5 F10 live checks | rebuild + measure | no source |

Small and well-bounded. The only thing that could grow is F7's optional tooltip labels (66 locale files) —
deliberately deferred.

---

## 7. Housekeeping found along the way (not part of this feature)

- F3/F6 state is **lost on virtualised remount** today (§1.2). A follow-up could move both into the same
  per-session store now that the pattern exists.
- `packages/session-ui/src/components/session-turn.tsx:436-527` is a **dead duplicate** of the live markup,
  still sharing its CSS. Deleting it (and its Storybook story) would remove a permanent divergence trap.
- `data-slot="session-turn-diffs-toggle"` being `opacity: 0` until hover also makes it invisible to anyone
  using a **touch** device until they tap the group — a mobile-specific reason F6 is not optional polish.
