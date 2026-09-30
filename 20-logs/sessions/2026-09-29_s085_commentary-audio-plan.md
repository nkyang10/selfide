# s085 — FU-122: spoken commentary (TTS for the narration) — plan

- **Opened (UTC):** 2026-09-29
- **Status:** PLANNED — no feature code written.
- **Fork:** `50-projects/p003-opencode-fork/opencode` (`dev`, HEAD `d52e02e`)
- **Plan:** `50-projects/p003-opencode-fork/notes/plan-commentary-audio.md`
- **Builds on:** FE-028 / DEC-057 · FU-111 (mobile) · FU-120 (no echoing)

## Request

Text-to-speech for the commentary panel, with the exact curl the user supplied, three settings rows under
Commentary, audio at the same time as the text, one-time playback with no cache, a non-overlapping queue
with a gap, and audio only for the foregrounded agent tab.

## The API, probed live

The first attempt returned **connection refused** — the service was still starting. On the user's "try again
now" it answered:

| Probe | Result |
|---|---|
| `{"input":"你好","voice":"cantonese"}` | **200** `audio/mpeg`, **12,528 bytes**, **242ms** — real `MPEG ADTS layer III, 24 kHz mono` |
| ~30-word commentary line | **200**, **38–41 KB**, **0.32–2.36s** |
| unknown voice | **400** `application/json`, with the service naming its own voices endpoint in the error |
| empty input | **422** |

**It is Azure-Speech-compatible.** `cantonese` is an *alias* resolving to **`zh-HK-HiuMaanNeural`**; there are
**322 voices and 23 friendly aliases** (`alloy`, `en-male`, …). That decides the settings design: the voice
is **free text sent verbatim**, not a 322-entry dropdown — a picker would be a 322-item translation surface
and would rot the moment the service's list changes. A bad voice is a **400 with a readable message**, so
misconfiguration is visible rather than silent.

## The user's decisions

- The service "try again now" — it was mid-startup, not misconfigured.
- Audio for the **foregrounded tab only**.

## The one non-obvious consequence

"Only the foregrounded tab" is not just an audio filter — **it changes the lease**. Today a backgrounded tab
keeps holding the lease and keeps generating narration nobody sees; with audio, two open tabs would
interleave. So the chosen answer also gates *generation* on foreground, which is the only option where the
user's ears and the token bill agree.

`commentaryShouldWatch` already takes `isDesktop / panelOpened / latched / enabled`, so this is **one more
term** — sourced from the app's existing `visibilitychange` plumbing (`layout.tsx:440`,
`server-sdk.tsx:345`, `directory-layout.tsx:101`), not invented. The same predicate then governs both
spending and speaking, which is what stops them drifting apart.

## Shape

**1 new module + 3 settings rows. No server change, no new route, no new event, no DB change.** The narration
pipeline is untouched; audio is a subscriber to the store the event already writes.

- `utils/commentary-audio.ts` — a plain-TS queue (no Solid): one `Audio` element so "no overlap" is
  mechanical, a 400ms gap measured from `ended`, a per-session `seq` high-water mark so **only new** entries
  speak and a panel remount never replays history, `cache: "no-store"`, and object-URL revocation.
- Playback is triggered from the **store write**, not the panel — the panel unmounts when closed and audio
  must not stop with it.
- Settings extend the existing `CommentarySection`; all three rows are per-browser, like the commentary
  settings they sit beside.

## Things worth remembering

- **Autoplay is the likely first-run failure**, and the settings toggle is the user gesture that satisfies
  it. A rejected `play()` must release the lock or the queue wedges forever — that is the classic failure and
  it is explicitly tested.
- **A mistyped voice 400s on every line**; without a once-per-voice backoff that toasts every 10 seconds.
- **iOS Safari handles `visibilitychange` unreliably** — `directory-layout.tsx:65` already carries a comment
  about it, and the fix there is reused rather than reinvented.
- **Two windows in one browser** are both `visible`; they would each narrate. Known limit, not solved.

## Close-out

Plan written, records updated, **no feature code touched**. The fork is unchanged from `d52e02e`.
