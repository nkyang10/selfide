# Plan — FU-111: the Commentary panel on a phone (a third mobile tab)

> **Status:** PLAN ONLY — no feature code written. Prepared 2026-09-29 (UTC), session **s083**.
> **Closes:** FU-111 (raised by s082 when the desktop-only cut shipped).
> **Builds on:** FE-028 / DEC-057, which is **live on :4447** (`1.1.20260929072355`, pid 1005463).
> **User's two decisions** (asked before planning):
> 1. **Placement** = a **third tab in the existing mobile strip**, not a bottom sheet and not a ticker.
> 2. **Lease** = **keep narrating once you have opened it**, so you can flip back to the chat and still
>    get lines.
>
> **The scope is much smaller than FU-111 looked.** The panel component, the service, the event, the
> routes, the store slice, the reducer case and the 65-locale copy all already exist and are already
> live. This is a placement change plus **one architectural move** (§2), because the lease currently
> lives inside the panel and that is the one thing the mobile placement breaks.

---

## 0. Executive summary

| What we need | Reality in the fork |
|---|---|
| A third tab | ✅ `mobileTabs()` (`session.tsx:2033-2066`) is **one shared function** called from three places — new-layout top (`:2080`), new-layout bottom (`:2261`), legacy (`:2275`). **One edit covers every mobile layout.** |
| Reuse the panel, no duplicate | ✅ `CommentaryPanel` is rendered by exactly one call site (`session.tsx:1367`) and imported once. Mobile becomes a second `<Match>` around the same JSX. |
| A label | ✅ `session.commentary.title` ("Commentary") already exists in all 62 locales. **No new i18n key, no fabricated translations.** |
| Keep narrating after leaving the tab | ⚠️ **The lease is tied to the panel being mounted** (`commentary-panel.tsx`: `createEffect` takes it, `onCleanup` releases it). On mobile the panel unmounts when you tap back to the chat, so the lease dies. This is the one real work item — §2. |
| A mobile header button | ❌ Deliberately not added: the **Files Changed** tab has no header button either (the review toggle lives in `hidden md:flex`, `session-header.tsx:464`). Adding one for commentary alone would be inconsistent. |

**5 files, 2 of them new, ~+120/−40. No new i18n, no new server code, no new event, no new route.**

---

## 1. Measured baseline (live :4447, before any change)

`packages/app/AGENTS.md` requires a baseline before touching session code, so this was measured rather
than assumed. Chromium, real login, real session, both locales.

| Viewport | Locale | `tabs-list` width | Tabs | Truncated |
|---|---|---|---|---|
| 390 × 844 | en-US | **372px** | `Session` **185px**, `Changes` **186px** | no |
| 390 × 844 | zh-Hant | 372px | `工作階段` 185px, `變更` 186px | no |
| 360 × 844 | en-US | 342px | `Session` **170px**, `Changes` **171px** | no |

**After the change the arithmetic is exact, not a guess:** 372 / 3 = **124px per tab at 390px** (342 / 3 =
114px at 360px), down from 186px.

**The one thing I could not measure:** the worst case. Both sessions I probed had **no changed files**, so
English showed the short `Changes` rather than `Files Changed 12` — and `Files Changed 12` is ~40% wider.
I tried to find a session with a non-empty review diff and could not produce one on demand. So:

> **P1 task, with the exact method:** re-run this probe against a session whose review tab label is
> `Files Changed N`, at 390px and 360px, in English, and record whether it ellipsizes. The tab CSS
> already truncates (`packages/ui/src/components/tabs.css:74-75` — `overflow: hidden; text-overflow:
> ellipsis`), so the **failure mode is a shortened label, not a broken strip**. If it truncates, the
> fallback is one line: drop the count from the mobile label and show it as a badge, so the label reads
> `Changes` with a `12` badge — which also matches what the desktop sidebar already does.

**How to reproduce the probe** (it took three attempts to get right; the traps are worth recording):
- the UI route is **`/:dir/session/:id`** with `:dir` = base64 of the directory — *not* `/session/:id`,
  which is the **API** path and returns raw JSON in a browser;
- login with `input[type=text]` + `input[type="password"]`; the first `input:visible` is the router's
  hidden `name=next` field, and the third is a `remember` checkbox, so index-based selectors fill the
  wrong things;
- the app lives at `node_modules/.bun/playwright@1.59.1/…`, and `import { chromium } from "playwright"`
  does **not** resolve from `packages/app`.

---

## 2. The one real work item: move the lease out of the panel

`CommentaryPanel` currently *is* the lease holder:

```ts
// commentary-panel.tsx — today
createEffect(() => {
  const id = sessionID(); if (!id) return
  watch(true)                                   // takes the lease
  heartbeat = window.setInterval(() => watch(true), 15_000)
  onCleanup(() => { clearInterval(heartbeat); watch(false) })
})
```

On desktop that is exactly right: the column is visible ⟺ the panel is mounted ⟺ someone is watching. On
mobile it is wrong in the user's chosen direction — switching to the chat tab unmounts the panel and
**stops the narration**, which is the case they explicitly asked to avoid.

**Fix: one lease policy for both platforms, owned by the session page, not the panel.**

New `packages/app/src/pages/session/commentary-watch.ts`:

```ts
// Pure, and the only thing in this file worth a unit test.
export function commentaryShouldWatch(input: {
  isDesktop: boolean
  panelOpened: boolean
  latched: boolean
}): boolean {
  return input.isDesktop ? input.panelOpened : input.latched
}
```

plus a small controller that owns the effect (take/release, 15 s heartbeat, `pagehide` release). Desktop
behaviour is **unchanged**; mobile gains the latch.

**The latch is per page visit and is not persisted.** It lives in `sessionViewState()` (`session.tsx:116-119`),
which is a **local, non-persisted** `createStore` already holding `mobileTab`. That is the boundary that
keeps this from becoming the rejected option 3 ("any open session page narrates"): open the commentary tab
once in this visit and it keeps running while you read the chat; close the tab and the latch is gone.

`CommentaryPanel` then becomes **presentational** — it keeps its initial paint (`fetchCommentary`) and
loses the watch effect. That is the no-duplication payoff: the panel is shared verbatim across two
placements, and there is exactly **one** lease policy in **one** file.

---

## 3. Placement: the third tab

All of it is in `packages/app/src/pages/session.tsx`.

| Change | Where | Note |
|---|---|---|
| `mobileTab` union gains `"commentary"` | `:118` | `createStore` is local, so nothing migrates |
| new `mobileCommentary()` memo | beside `mobileChanges()` `:674` | same shape: `!isDesktop() && store.mobileTab === "commentary"` |
| third `Tabs.Trigger` | in `mobileTabs()` `:2033-2066` | label reuses `session.commentary.title`; on select also latches |
| `!w-1/2` → `!w-1/3` | the three triggers | measured: 186px → 124px per tab at 390px |
| new `<Match when={params.id && mobileCommentary()}>` | in the `<Switch>` at `:2084` | renders the same `{commentaryPanel()}` |
| **fallback condition must also exclude it** | `:2147` | `!mobileChanges()` → `!mobileChanges() && !mobileCommentary()` |
| `wantsReview()` **unchanged** | `:675-680` | see trap 2 |
| mount the watch controller | beside the composer in the session page | once per session view |

### The two traps this shape invites

1. **The `<Switch>` fallback.** Line 2147 is `<Show when={(params.id || !newSessionDesign()) && !mobileChanges()}>`
   — the *else* branch, i.e. the chat. If the new `<Match>` is added and the fallback is not narrowed, the
   timeline and composer render **underneath** the commentary. This is the single most likely defect in
   the whole change and it is why the condition is called out in its own row.
2. **`wantsReview()`** gates the **git-diff query** (`vcsQuery` `:688-691`, `enabled: wantsReview() && …`).
   It reads `store.mobileTab === "changes"` directly. A third tab must **not** widen it — otherwise
   reading commentary starts fetching a VCS diff nobody asked for.

---

## 4. What the lease now costs, honestly

Holding the lease for the whole page visit means a session left open on a phone narrates while you read
the chat. That is what the user chose, and it is bounded:

- `maxEntriesPerTurn` = **20 per user turn**, reset on each user message (`entriesInCurrentTurn`);
- `minGap` = **10 s** between lines, from the newest stored entry, so it survives a restart;
- `minActivityChars` = **120** — a tick with almost nothing new never calls the model;
- released on unmount and on `pagehide`.

With **FU-115's measured latency** (43–99 s per line on `dgx/general`), a 10-minute unattended turn
produces roughly **6–14 lines, not 60**. The real cost driver is the model, not the cadence.

---

## 5. Tests, benchmark, gates

**Unit (`commentary-watch.test.ts`)** — the policy is pure, so this is the whole test surface:
desktop opened → watch; desktop closed → no watch even if latched; mobile latched → watch; mobile
not latched → no watch even if `panelOpened`; mobile ignores `panelOpened` and desktop ignores `latched`
(the two platforms do not leak into each other).

**Not unit tested, and said so rather than faked:** releasing on unmount is component behaviour, and
`packages/app` has **no `*.test.tsx`** (the same reason `session-panel-width` was kept pure in s082).
The release path is covered by the live check in §6 instead.

**Benchmark (the numbers to record, before and after):**
1. `tabs-list` width, per-tab width and `truncated` at **390px and 360px**, en-US and zh-Hant — the §1
   table is the "before" column;
2. the **worst case** — a session labelled `Files Changed N` in English;
3. that the composer is not pushed off-screen: three triggers in one row, so the strip's height is
   unchanged;
4. the closed-state cost is unchanged — the panel mounts only in its own `<Match>`, and the timeline
   isolation measured in s082 (flat ~1.3–3.0 µs per line from a 10- to a 5000-message timeline) must not
   regress.

**Gates:** `bun turbo typecheck` 30/30 · app `bun run test:unit` (not bare `bun test` — FU-109) ·
i18n parity 5/5 (trivially unchanged: no new key) · oxlint 0 errors · the §6 live check.

---

## 6. Live verification plan (on :4447, after deploying)

1. 390px and 360px, English: open a session, confirm three tabs render and none breaks the layout.
2. Tap **Commentary** → lines appear (or the "Watching the agent" state, per FU-115).
3. Tap **Session** → confirm the timeline is **not** rendered underneath (trap 1) and that narration
   *continues*: watch the server log for a second `agent=commentary` stream after you switch away.
4. Tap **Changes** → confirm the diff view still works and the label is intact.
5. Navigate away → confirm no further commentary streams (the release works).
6. Confirm the Commentary tab is **absent on desktop-width** and the desktop column is unchanged.

---

## 7. Risks

1. **The `<Switch>` fallback** (§3 trap 1) — the most likely defect; called out twice on purpose.
2. **`wantsReview()`** must not widen (§3 trap 2), or commentary silently starts fetching git diffs.
3. **`latched` must not be persisted.** It belongs in the non-persisted `sessionViewState`; putting it in
   the layout store would turn this into the cost the user rejected.
4. **360px is the tight end** — 114px per tab. "Files Changed 12" will likely ellipsize. Measured, not
   assumed, in P1; fallback is a one-line label change.
5. **The lease outlives the panel on mobile**, so `pagehide` + unmount release is the only thing stopping
   it. A leak here means a phone narrating in the background indefinitely.
6. **The legacy layout shares `mobileTabs()`** so the third tab appears there too. That is correct (one
   edit, no duplication) and the legacy layout is sunset (`oldInterfaceSunset = 2026-09-14`) anyway.
7. **FU-115 still stands** — the tab can sit on "Watching the agent" for a minute. Because the lease runs
   in the background, the lines will be there when you switch over, which is the point.

---

## 8. Explicitly out of scope

- The one-line ticker above the composer (rejected in favour of the tab).
- A bottom sheet (rejected; `packages/ui` has no sheet primitive, only Dialog).
- A mobile header button (rejected; consistent with Files Changed, which has none).
- Persisting the latch across visits.
- Any change to the server, the event, the routes, the panel's rendering, or the i18n copy.
- Narration for sessions you never opened (the rejected option 3).
