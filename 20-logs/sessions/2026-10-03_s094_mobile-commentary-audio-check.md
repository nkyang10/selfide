# s094 — Feature check: commentary audio on a mobile browser, while on the chat tab

**Asked:** "for mobile browser, if i am in agent/chat tab, will there be commentary with voice out?"

Read-only investigation. No code touched.

## Verdict

**Yes — but only after the Commentary tab has been opened once in that page visit, and only while
the page stays foregrounded.** Both switches are off by default, and neither is reachable from the
chat tab on mobile.

## The chain, as read in the code

| Question | Answer | Evidence |
|---|---|---|
| Does audio depend on the panel being open? | **No.** `CommentaryAudioPlayer` is mounted at session-view level, outside the panel and outside the mobile tab `Switch`. | `pages/session.tsx:1399`, rendered at `session.tsx:2125` before the `Switch`; both layout branches render `sessionPanelContent()` (`session.tsx:2347`, `:2353`) |
| Does the *lease* depend on the panel being open on mobile? | **It depends on a latch**, not on the panel. First tap of the Commentary tab sets `commentaryLatched`, which holds the lease for the rest of the page visit. | `pages/session.tsx:2109`; policy `commentary-watch.ts:33-44` (mobile → `latched`, desktop → `panelOpened`) |
| Never opened the Commentary tab on mobile? | No lease → the server never narrates → no lines, no audio. | same two lines |
| Where are the two switches? | Both in the **commentary panel header**: narration on/off (`commentary-enabled`) and the sound mute (`commentary-audio-enabled`). So on mobile they are only visible on the Commentary tab. | `commentary-panel.tsx:168`, `:186` |
| Are they on? | **No.** `enabled: false`, `audioEnabled: false`. | `context/layout.tsx:300`, `:304` |
| Does staying on the chat tab keep it running? | Yes, via the latch. The chat and the commentary panel are mutually exclusive on mobile (`!mobileCommentary()` on the chat `Show`), so without the latch the narration would stop on every tap back to the chat. | `session.tsx:2203` |
| Does locking the phone / switching apps stop it? | **Yes.** `foregrounded` is a term of the same predicate, so a hidden document releases the lease and the server stops narrating. | `commentary-watch.ts:41-42`, signal at `session.tsx:445-452` |

## What is in the deployed build

`1.1.20261001150325`, pid 2924370 on `:4447` (binary mtime 2026-10-01 23:03). Markers found in the
binary: `commentary-audio-enabled`, `commentary-voice-picker`, `mobileTab`, `commentary/audio` (×2).
So the mobile commentary tab, the audio player and the voice picker are all shipped. `:4447` answers
**401** without credentials, so the page itself was not loaded.

## The two risks that a code read cannot settle

1. **A fresh `Audio` element per clip, and nothing pre-unlocks audio.** `createAudio()` is called
   inside `play()` (`utils/commentary-audio.ts:299-301`), so each line is a new element. Android
   Chrome allows `play()` once the document has been interacted with, so one tap should be enough.
   **iOS Safari is the unknown**: if it re-blocks each new element the queue drains silently — the
   rejection is reported once (`complain()` is keyed on the status, so `0` fires a single toast:
   "autoplay blocked — click the page once to allow sound") and every later clip fails the same way
   with no further message. The recorded belief ("the toggle is the gesture that satisfies autoplay
   policy", `commentary-config.md:194`) has only been tested on desktop.
2. **The silent switch.** iOS may route `HTMLAudioElement` through the ringer category, in which case
   a phone on silent plays nothing. No Web Audio unlock is attempted anywhere in the module.

Also worth telling the reader: there is **no wake lock** anywhere in the app, so a screen that sleeps
ends the narration — which is the same `foregrounded` rule as switching apps.

## Part 2 — the user asked for the test, so it was run

Four Playwright runs at **390×664** (`devices["iPhone 13"]`, `innerWidth 390`,
`matchMedia("(min-width: 768px)") === false`, so the mobile layout is genuinely in play) against
the deployed `1.1.20261001150325` on `:4447`. Harness in `/tmp/opencode/s094-*.mjs`, evidence in
`/tmp/opencode/s094*/`. Two throwaway sessions were created through the API; the password was read
from the server process env, never written into this folder, and the copy in `/tmp` was shredded.

**The answer to the question is yes, and it is now measured rather than read.**

| Step | Result |
|---|---|
| Mobile strip at 390px | `Session · Changes · Commentary` — all three present (`data-value`) |
| Commentary tab header | narration switch, sound button and the voice picker **all three found** |
| Tapping the tab | lease taken (`POST …/commentary/watch`), `unwatch` never sent |
| Narration on + sound unmuted | `aria-pressed="true"` on `commentary-audio-enabled` |
| **Back on the chat tab** | heartbeats kept coming every 15 s: `09:16:09 / :24 / :39 / :54`, **zero unwatch** over 45 s |
| A line arrives | `store changed: 1 line(s), newest seq=2` → enqueued **while the chat tab was showing** |
| Server render → publish | line first as text (`audio=none`, correctly skipped, not spoken), then republished with hash `bb9d0d38…` and spoken — the two-pass design behaving as designed |
| Audio route | `200`, 14 978 base64 chars → **11 232 bytes**, ADTS sync `fff3`, `MPEG ADTS layer III v2, 48 kbps, 24 kHz mono` — 11 232 B ÷ 6 kB/s = 1.87 s, matching the element's reported duration |
| Playback | `play() accepted` → `loadedmetadata duration=1.87s` → `canplay` → **`onended after 1.87s`** |
| Voice catalogue | `GET …/commentary/voices` → 322 voices on `:8880`, 1 on `:8881`, default `192.168.1.162:8880 / cantonese` |

**Autoplay is the one thing that needed two runs, and the first one was my mistake.** Run 1 passed
`--autoplay-policy=user-gesture-required`, which is Chrome's *strictest* mode — `play()` must be
inside a live gesture — and it rejected with `NotAllowedError: play() can only be initiated by a
user gesture` **despite** the page having been tapped four times. Under Chrome's **default**
policy the same sequence played to `ended`. So the s087-era claim that "the toggle is the gesture
that satisfies autoplay" holds for the Chrome family, and my strict flag was a harness artifact
producing a false negative — worth recording, because the artifact looks exactly like the iOS
failure it was supposed to be testing.

**What the test could not settle, stated plainly:**

1. **iOS.** WebKit's policy was never exercised — this is Chromium. And nothing in the code unlocks
   audio: `createAudio()` runs per clip (`commentary-audio.ts:299-301`), so there is no element
   pre-played during a gesture and no silent-buffer trick. If WebKit demands a gesture *at play
   time* rather than *in the document*, the feature is silent there, and because `complain()` is
   keyed on the status the reader gets **one** toast and then nothing.
2. **The silent switch.** Never testable off-device.
3. **The hidden-page rule.** Headless Chromium does not model visibility: `bringToFront()` on a
   second page left `document.visibilityState === "visible"` and produced no `unwatch`, and
   `Page.setWebLifecycleState: frozen` did the same. So `foregrounded` → release and the `pagehide`
   release stay **unverified by test** — code-read only. On a phone this is the difference between
   "narration stops when I lock the screen" and "it keeps narrating all night".
4. **Audibility.** Bytes and a decoded `ended` are not sound. Only the user's ears close that.

**One ergonomic finding worth more than the test.** Navigating to a *different* session produced **no
`watch` at all** — the latch is per session, exactly as `session.tsx:976-983` implies. So each new
agent tab needs one tap of its own Commentary tab, and a reload needs one tap again. That is
correct-by-design (it is what stops every session ever opened from narrating) and it is also the
thing most likely to be reported as "it stopped working".

## Follow-ups

- FU-123 advances: the chain is now proven at phone width, through real playback to `ended`. What
  remains is iOS and the user's ears.
- New FU-136: iOS WebKit autoplay + silent switch, unproven and unaddressed in code.
- New FU-137: the per-session latch means one tap per session and per reload; no affordance tells
  the reader that.