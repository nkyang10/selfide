# s083 — FU-111: the Commentary panel on a phone (plan)

- **Opened (UTC):** 2026-09-29
- **Status:** PLANNED — no feature code written. Plan doc only.
- **Fork:** `50-projects/p003-opencode-fork/opencode` (`dev`, HEAD `4218986`, pushed; live build
  `1.1.20260929072355` pid 1005463 on :4447)
- **Plan:** `50-projects/p003-opencode-fork/notes/plan-commentary-mobile.md`
- **Closes:** FU-111. Decision record: to be numbered on implementation. Sibling: FU-115 (narration latency).

## Request

> plan

Following s082's closing offer to plan the mobile surface for the commentary panel.

## Scope questions, and the answers

1. **Placement** → a **third tab in the existing mobile strip** (not a bottom sheet, not a ticker).
2. **Lease** → **keep narrating once you have opened it**, for the life of the page visit.

The second answer is the one with teeth: it is not a placement change, it is an **architectural move**.

## What the code says

| Need | Reality |
|---|---|
| A third tab | `mobileTabs()` (`session.tsx:2033-2066`) is **one shared function** called from three places — new-layout top `:2080`, new-layout bottom `:2261`, legacy `:2275`. One edit covers every mobile layout. |
| Reuse the panel | `CommentaryPanel` is defined once and rendered by exactly one call site (`session.tsx:1367`). Mobile becomes a second `<Match>` around the same JSX — no duplicate component, no duplicated rendering logic. |
| A label | `session.commentary.title` already exists in all 62 locales → **no new i18n key**. |
| The lease | **Tied to the panel being mounted** (`commentary-panel.tsx` takes it in a `createEffect`, releases in `onCleanup`). On mobile the panel unmounts when you tap back to the chat, which would stop the narration — exactly what the user asked to avoid. This is the only real work item. |
| `mobileTab` storage | `sessionViewState()` (`session.tsx:116-119`) is a **local, non-persisted** `createStore`. That is where the latch belongs, and it is what keeps this from becoming the rejected "any open page narrates" option. |
| A mobile header button | Not added — **Files Changed** has none either; the review toggle lives in `hidden md:flex` (`session-header.tsx:464`). |
| A sheet primitive | `packages/ui` has **no** sheet/drawer, only Dialog — one more reason the tab was the right pick. |

## Two traps this shape invites (both called out in the plan)

1. **The `<Switch>` fallback at `:2147`** is `!mobileChanges()`. Adding a `<Match>` without narrowing that
   fallback renders the timeline and composer **underneath** the commentary.
2. **`wantsReview()`** (`:675-680`) gates the **git-diff query** (`vcsQuery` `:688-691`). A third tab must
   not widen it, or reading commentary starts fetching VCS diffs nobody asked for.

## Measured baseline (live :4447, before any change)

Chromium, real login, real session, both locales — `packages/app/AGENTS.md` requires a baseline before
touching session code.

| Viewport | Locale | `tabs-list` | Tabs | Truncated |
|---|---|---|---|---|
| 390 | en-US | **372px** | `Session` **185px**, `Changes` **186px** | no |
| 390 | zh-Hant | 372px | `工作階段` 185px, `變更` 186px | no |
| 360 | en-US | 342px | `Session` **170px**, `Changes` **171px** | no |

After: 372 / 3 = **124px per tab** at 390px (114px at 360px), exact arithmetic from the measured number.

**What I could not measure, and did not pretend to:** the worst case. Both sessions probed had no changed
files, so English showed the short `Changes` rather than `Files Changed 12` (~40% wider). I could not
produce a session with a non-empty review diff on demand, so that measurement is an explicit P1 task with
the exact method recorded. The tab CSS already ellipsizes (`tabs.css:74-75`), so the failure mode is a
shortened label, not a broken strip; the fallback is a one-line label change.

**Probe traps worth recording** (three attempts): the UI route is `/:dir/session/:id` with `:dir` =
base64 of the directory — `/session/:id` is the **API** path and returns raw JSON in a browser; login needs
`input[type=text]` + `input[type="password]` because the first `input:visible` is the router's hidden
`name=next` field and the third is a `remember` checkbox; and `import { chromium } from "playwright"` does
**not** resolve from `packages/app` — the module lives at `node_modules/.bun/playwright@1.59.1/…`.

## What the plan changes

**5 files, 2 new, ~+120/−40, no new i18n, no server change, no new event, no new route.**

1. `commentary-watch.ts` (new) — the pure `commentaryShouldWatch` policy (desktop → `panelOpened`,
   mobile → `latched`) plus a small controller owning take/release, the 15 s heartbeat and `pagehide`.
2. `commentary-watch.test.ts` (new) — the policy, which is the whole test surface.
3. `commentary-panel.tsx` — becomes presentational; loses the lease effect (net −25 lines).
4. `session.tsx` — `mobileTab` union, `mobileCommentary()`, the third trigger, `!w-1/2` → `!w-1/3`, the new
   `<Match>`, the narrowed fallback, and the controller mounted once per session view.
5. i18n — **nothing**; `session.commentary.title` is reused.

## The cost, stated plainly

Holding the lease for the whole visit means a session left open on a phone narrates while you read the
chat. That is the choice, and it is bounded by `maxEntriesPerTurn` 20, `minGap` 10 s, `minActivityChars`
120, released on unmount/`pagehide`. With FU-115's measured 43–99 s per line, a 10-minute unattended turn
is roughly **6–14 lines, not 60** — the model is the cost driver, not the cadence.

## Close-out

Plan written, records updated, no feature code touched. The fork is unchanged from `4218986`.
