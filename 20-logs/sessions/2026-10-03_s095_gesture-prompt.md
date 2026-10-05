# s095 — Detect the gesture requirement, and make the prompt's tap *be* the playback

Follows s094. The question was "can we detect the touch requirement? if yes, trigger a prompt for user to
complete the requirement". Implementation + gates done; **the live browser check needs a deploy and is
waiting on the user.**

## The measurement that shaped it (run before any code)

Under Chrome's **strictest** autoplay policy — `--autoplay-policy=user-gesture-required`, where `play()` must
be issued inside a live gesture — a real tap on a real control changed nothing:

```
09:24:04 tap (Changes → Session)  →  09:24:06 play() REJECTED  NotAllowedError
09:25:35 tap (Changes → Session)  →  09:25:46 play() REJECTED  NotAllowedError
```

**"Tap once to unlock sound" is not a thing that exists.** The play always comes from a timer, and a timer is
never inside a gesture. So the prompt cannot unlock anything — **the tap has to be the playback.** Had this
been built as "detect, prompt, retry on a timer" it would have shipped a placebo that looks like a fix.

Detection itself is free and already in the code: the `play()` rejection. The only judgement is **which**
rejection, and the same trace shows both kinds — the notification chime rejects with `NotSupportedError`. A
codec failure is not something a tap can fix, so keying on the error *name* is the difference between a
working prompt and a misleading one.

## What changed

**`packages/app/src/utils/commentary-audio.ts`**
- `isGestureRequired(error)` — `name === "NotAllowedError"`, and nothing else.
- `play(url, clip)` became `attempt()` inside one promise, so a refused clip can be **replayed** by the same
  call path: same gap, same lock, same object URL, which is exactly as long as the line is waiting.
- On a gesture block: the watchdog is disarmed (it exists to catch a *resolved* play that never loaded, and a
  refusal has already said what is wrong — leaving it armed logs a false eight seconds later), the retry is
  parked, `onGestureRequired()` fires, and **the lock is held** so the next line cannot start on top of it.
- `resume()` — clears the parked retry, wakes an `AudioContext` with one frame of silence, then replays. Must
  be called from inside the gesture; that is the entire point.
- `wake()` — `resume()` + `createBuffer(1, 1, sampleRate)` + `start(0)`. Best-effort inside `try`/`catch`: a
  browser that throws instead of refusing must not take playback down with it, because playback may be allowed
  on its own.
- Anything that is not a gesture block — codec, CSP, **or a second refusal after the reader tapped** — takes
  the old path: one toast, lock released. One prompt per clip (`asked`), so a tap that does not help does not
  become a tap loop.
- `stop()` clears the parked retry, so a prompt tapped after the sound was switched off does nothing at all.

**`packages/app/src/pages/session/commentary-audio-player.tsx`** — raises a `persistent` actionable toast
(`showToast` already takes `actions`) and owns it: dismissed on the tap, when audio goes off, and on unmount.
The button's `onClick` is the gesture, so the toast and the remedy are the same object.

**i18n** — 3 keys (`session.commentary.audioBlocked.{title,description,action}`) in **all 62 locales**
(`parity.test.ts` fails otherwise). zh (Simplified), zht (Traditional) and ja translated; the other 58 carry
the English string as a placeholder, which is the FU-116/FU-131 debt again → FU-138.

## Gates

| Gate | Result |
|---|---|
| `bun run test:unit` (packages/app) | **852 pass / 0 fail** across 116 files — 7 new cases |
| `bun run typecheck` | clean |
| `oxlint` on the 3 changed TS files | **0 warnings, 0 errors** on the production files (the test file's 31 `no-unnecessary-type-assertion` warnings are pre-existing style: 27 of them are at HEAD) |
| `bun run build` (vite) | built in 11.58 s; `PARKED: the browser wants a gesture`, `resume() from a user gesture` and `Tap to hear this line` are all in `dist/assets/index-JF2avRq6.js` |

## The tests earned their keep immediately

`FakeAudio` refused by a sticky per-element flag, which **cannot express the behaviour under test** ("the first
attempt is refused, the one inside the tap is not") because the retry builds a brand new element. Replaced with
a static queue of refusals — one per `play()` — and the six cases went green. One case caught a wrong
assertion of mine: after the parked clip finishes, the next line starts *immediately*, so "still two
instances" was false; the assertion now says what the test means (three instances, empty queue, still playing).

## Part 2 — committed, deployed, and opened

- Committed **alone**, `0f92c71` (`fix(app): a blocked autoplay parks the line, and the prompt's tap is the
  playback`). 65 files, only `packages/app`: the 3 TS files + 62 locales. The s093 tree
  (`packages/core/src/v1/config/config.ts`, `packages/opencode/src/tool/*`) stayed uncommitted — and then
  shipped anyway, because a build compiles the whole checkout. That was in the question and the answer was yes.
- Deployed via `scripts/deploy-web-4447.sh --detach`: **`1.1.20261003095710`**, pid 1406061 on `:4447`.
  Markers confirmed in the shipped binary: `PARKED: the browser wants a gesture`, `resume() from a user gesture`,
  `Tap to hear this line` (×59 — English in en plus the 58 placeholder locales), `audioBlocked` (×63).

### The check, and a harness problem worth recording

**Run 1 passed**: the line parked, the button was found and tapped, and the clip played to `onended after
1.87s`. Then runs 2–4 exposed two harness faults of mine:

1. `timeout 290` killed run 2 mid-poll, and the resulting "browser has been closed" read like a product
   failure. A killed harness is not a failed feature — but it cost a run.
2. **Runs 3 and 4 never blocked at all.** Six clips, six `onended`, zero refusals — under the *same* strict
   flag that blocked run 1. So `--autoplay-policy=user-gesture-required` is **not a reliable way to test this**:
   whether a refusal happens depends on timing my harness does not control. A check that fires only sometimes
   is not a check.

So the final check replaces the flag with a **policy simulator** installed before any app script runs: `play()`
counts only while a click is being handled (`live` counter in a capture listener, cleared on the next task),
and rejects with a real `NotAllowedError` otherwise. Everything else is the real browser, the real server, the
real 390px viewport. That fires every time.

```
10:33:09 [audio] seq=39 PARKED: the browser wants a gesture. The line keeps the lock and waits.
10:33:10 TOAST  {"text":"Tap to hear this lineYour browser is blocking sound until you interact with the ",
                 "buttons":[" [aria-label=Dismiss]","Play"]}
10:33:10 tapped the prompt
10:33:10 [audio] resume() from a user gesture, 0 line(s) still queued
10:33:12 [audio] onended after 1.87s
```

The prompt renders with the right copy and a **Play** button, the tap is inside the handler, and the parked
line is heard. **FU-139 closed.**

One instrumentation error of mine, for the record: the `ended` **event** listener counted 0 while the app's own
`onended` fired, because `new Audio()` is not in the DOM and a non-bubbling `ended` never reaches `document`.
The app's trace was the trustworthy witness all along.

## Not done, and why

- **No live browser check.** A new prompt that has never been opened is exactly what broke in s091 (the Kobalte
  selector crash: 78 files, 1114 insertions, every gate green, and it threw on open). The proof is one run
  under the strict policy: expect a toast on the blocked line, tap **Play**, expect `onended`. That needs the
  app rebuilt into the binary and `:4447` restarted, which is the user's call.
- **iOS.** Unchanged and still unproven (FU-136). This change makes the blocked case recoverable wherever a
  gesture is possible, and the `AudioContext` addresses the silent switch, but nobody has held an iPhone.
- **The tree is not clean.** `packages/core/src/v1/config/config.ts` and `packages/opencode/src/tool/*` are
  uncommitted from s093, and a build compiles the whole checkout — so a rebuild would ship those too.