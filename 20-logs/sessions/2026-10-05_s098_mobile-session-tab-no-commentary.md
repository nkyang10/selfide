# s098 — "On a phone, in the Sessions tab, there is no commentary"

> **Renumbered on close-out.** I opened this as `s097`/2026-10-03, both wrong: the real UTC date was
> **2026-10-05**, and a parallel session had already written
> `20-logs/sessions/2026-10-03_s097_running-with-earphones.md`. That is FU-134's collision class (parallel
> sessions mint the same id because they cannot see each other), and renumbering in place while parallel
> work runs is what FU-134 says not to do — so I moved **my own** file only, left theirs untouched, and
> corrected the timestamps in the rows I had written. No other shared file is renumbered.

User report, read from the **live DOM** they pasted:

```html
<button id="tabs-cl-9254-trigger-session" role="tab" aria-selected="true" data-key="session"
        class="w-full !px-1 !py-2" tabindex="0" data-selected>Session</button>
```

`w-full !px-1 !py-2` is the **`compact` mobile tab strip** — `session.tsx:2081` is the only place that
class string exists. So this is the new-layout mobile top strip (or the bottom one, `session.tsx:2317`),
and `aria-selected="true"` means they are sitting on the **Session** tab.

**Status: diagnosis complete, no code touched, decision pending with the user.**

## What the report actually is: two separate failures stacked, not one

Both are true at once, and they have different fixes.

### 1. Never tapped the third tab → there is no lease at all, so nothing is narrated

`commentaryLatched` starts `false` (`session.tsx:108`) and the **only** writer is the Commentary tab's
own click handler (`session.tsx:2109`). `commentaryShouldWatch` on mobile is `latched`, full stop
(`commentary-watch.ts:43`). No latch → no `POST /session/{id}/commentary/watch` → the session is
never in `state.leases` → `tick` is never called → **no model call, no line, nothing spent**.

This is the s083 design (DEC-057 / FU-111) working exactly as specified: one deliberate tap, then
narration for the life of the page visit. What it did not design for is that **the tap is the only
affordance that exists** — there is no hint, no badge, no empty-state line anywhere in the chat.

### 2. Tapped once → lines still accumulate, but the chat tab renders none of them

The panel mounts only under `mobileCommentary()` (`session.tsx:2136`), and `!mobileCommentary()` on
the chat's own `<Show>` (`:2203`) is load-bearing — without it the chat would render *underneath* the
panel. So from the Session tab there is **no surface at all** showing the newest line. The only
perception path left is audio, and audio needs the second switch — which lives in the same panel
header (`commentary-panel.tsx`), i.e. also only reachable after the tap.

### 3. And narration itself is off in a fresh browser

`commentaryEnabled` defaults to **`false`** per browser (`context/layout.tsx:628`, DEC-062), because
narration costs a model call every ~10 s. So on a phone that has never opened the panel there are
**two** things to find and turn on, and the second one is inside the view that the first one unlocks.

**The one-line summary:** on mobile the commentary is behind a tab that latches itself, and the tab
you are left looking at shows none of it. `mobile-multitasking first` is the project's stated mission
(`README.md`), and this is the exact case it names — watching a turn while reading the chat.

## Why this is worth fixing rather than documenting

FU-137 already recorded the cost of the latch ("each agent tab and each reload needs one tap") and
called it "a decision, not a fix". This report is the user saying the decision did not survive
contact: the thing it costs is not one tap, it is **the feature looking absent**.

> **The session spans two days, and the log says so.** The reads, the edits and the four gates ran on
> **2026-10-03 11:07-11:47Z**; the doc tweak, the commit, the deploy and the three live runs on
> **2026-10-05 01:02-01:15Z**. Every row in `command-log.md` is dated from an artifact (commit time,
> binary version stamp, harness and screenshot mtimes) rather than from a clock I was guessing at — my
> first pass put the whole session on 10-03, and a bulk id replace also relabelled five rows belonging
> to the parallel earphones session before I looked at the result. Both are recorded there.

## Gate status

Read-only. `git status` in the fork is clean at `0f92c71`; the ide repo has the uncommitted s093/s095
docs tree (known, see `current-state.md`).
---

# Part 2 — the fix: mobile watches the layout, not the tab

The user's answer, in their words: *"當個畫面變得窄嘅時候，當佢變成三個tab嘅時候… 佢都當為睇commentary"*
— when the screen goes narrow and it becomes three tabs, treat being anywhere in it, including the
Session tab, as watching the commentary. The latch was the wrong shape for that sentence: it made the
**tap** the trigger, and the tap was the only affordance the feature had.

**The rule now** (`commentary-watch.ts:47`), one line:

```ts
return input.isDesktop ? input.panelOpened : true
```

`enabled` and `foregrounded` still sit in front of it, so the cost is bounded by exactly two things
that need no latch: a switch the reader sets deliberately, and one lease per session actually in
front of them. The second half of that was checked rather than assumed — **the router has no
keep-alive** (no `KeepAlive` anywhere in `packages/app`/`packages/ui`; routes are plain
`component={SessionRoute}`), so a second agent tab is unmounted and does not narrate. That is what
the latch was protecting against, and it was never the tab.

Deleted rather than left as dead state: the `latched` input, the `commentaryLatched` field in
`sessionViewState`, and the store write in the Commentary tab's `onClick`. A field that no longer
decides anything is a second answer to the same question.

**Commit `5d1668e`** (3 files, `packages/app` only), deployed `1.1.20261005010214`, pid 3037933.

| Gate | Result |
|---|---|
| `bun typecheck` (packages/app) | clean |
| app unit suite | **852 pass / 0 fail**, 116 files (6 in `commentary-watch.test.ts`) |
| oxlint, 3 files | **20 warnings before and after** (stashed and re-run to compare) — none added |
| `vite build` | built in 12.4 s |
| served bundle | `assets/index-D9sHujrM.js` contains the minified rule `panelOpened:!0`; `commentaryLatched` occurs **0** times |

**The new test is a real regression test, not a description.** The middle assertion of
`"mobile narrates from the chat tab, with no tap and no open column"` was run against the pre-s098
rule verbatim in `/tmp/opencode/s098/old-rule.test.ts`: **1 fail** (`Expected: true, Received: false`).

## Live verification at 390px — and three harness faults, all mine

`iPhone 13` viewport, deployed build, real server. Harness `/tmp/opencode/s098-live{,2,3}.mjs`.

| Step | Result |
|---|---|
| Narration switch, read from the control itself | `aria-checked` **false → true** (so the `enabled` gate is genuinely open, not assumed) |
| **Reload, zero taps on the Commentary tab** | first **HOLD at 2916 ms**, with `aria-selected="true"` on `session` |
| 50 s sitting on the chat tab | **4 holds, 0 releases** |
| Panel read last | `data-slot="session-commentary-list"` present, **15 entries** (the cap) |
| Back to the chat tab after visiting the panel | **2 holds, 0 releases** — s083's promise still holds |
| **Generation** | `session_commentary` rows **seq 40/41/42 written 01:09:38 / 01:09:58 / 01:10:38**, i.e. inside the window where the tab was `session` and the only Commentary tap was the setup one at 01:07:48 |

Under the old rule that reload produces **zero** calls, because `commentaryLatched` starts `false`
per page visit. That is the whole bug, measured rather than argued.

**Three faults, all in my harness, all of which would have read as product facts:**

1. `url.includes("/commentary/watch")` **silently drops every `/commentary/unwatch`** — the release is
   the event being counted. Take vs release lives in the *URL*: `watch` sends a payload, `unwatch`
   sends none (`utils/server.ts:233-241`), which is also why `watching=undefined` in the first run was
   the *hold*, not a malformed body.
2. `#commentary-panel` is the **desktop** id (`session-side-panel.tsx:767`). The mobile mount
   (`session.tsx:2137`) has no id, so `panel: null` meant "wrong selector", not "no lines". The
   layout-independent hooks are `data-slot="session-commentary-entry"` / `-list`.
3. Run 2 measured **zero lease calls in 50 s** and looked like a regression. It was DEC-062's
   per-browser default: **every Playwright run is a fresh profile**, so narration was off. This is the
   s087/s094 trap verbatim, and I walked into it because I skipped the setup step that run 1 had.

The `closing`-only lines in the DB are not a defect: the probes asked the agent for "the single word
N", so the turn completes in a moment and s092's `closing` rule fires every time.

## What this does NOT fix, on purpose

- **Narration still defaults OFF per browser** (DEC-062). A phone that has never opened the panel still
  gets nothing, and the only switch is inside the panel. The user's answer was about the *latch*, not
  about the opt-in, so the cost policy stands — but that is FU-137's second half and it is still open.
- **Nothing is rendered in the chat tab.** The user saw that and chose the simpler policy change over
  the inline ticker; the audio path was already the answer there (`commentary-audio-player.tsx:29`
  gates on `enabled`, not on the lease).
- **The tab label still reads "Commentary" in every locale** (FU-116).
