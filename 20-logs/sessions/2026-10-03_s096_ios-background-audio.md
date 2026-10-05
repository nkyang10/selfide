# s096 — Can the commentary keep talking while the phone sleeps?

Asked in Cantonese, answered in Cantonese. **Research only — no code touched.**

The short answer, and it is not what either of us wanted: on iOS the ceiling is **one clip, and only
while the user stays in Safari**.

## What the platform actually does

| What you do | Result |
|---|---|
| Screen locks, still in Safari | The playing clip **finishes** — WebKit keeps the web process alive for playing audio |
| That clip ends | **Silence.** `play()` does nothing in the background; this is the finding WebKit closed #173332 with in Jan 2024 |
| Switch app / go Home | **Stops**, standalone PWAs included (#198277) |

So "background music" behaviour is not available to a web page on iOS at all: no background execution,
no background fetch, no background-audio mode.

The trap worth recording: **#173332's title lies.** Filed in 2017 as "`.ended` does not fire when the
screen is off", patched in 2019, regressed in iOS 17.2, and closed with the comment that the event *does*
fire and the following `play()` is what silently does nothing. A title-level reading would have sent us
looking for a missing event handler instead of at the permission.

## The app-side half, which is easy to forget

`commentaryShouldWatch` releases the lease on `visibilitychange` (`commentary-watch.ts:41`), so a locked
phone stops *generating* lines within a heartbeat — deliberately, because FU-122's argument was that a
hidden tab must not keep paying for narration nobody hears. **Any "keep talking while asleep" feature has
to change both halves**: what the browser will play, and whether we keep paying to produce it.

## Options put to the user

- **A. Screen Wake Lock** — iOS Safari 16.4+. The screen stays on, JS keeps running, every existing
  mechanism keeps working. Battery cost. The only supported route to continuous narration.
- **B. Web Audio lookahead scheduling** — buffers scheduled on the `AudioContext` clock, so the audio runs
  on the native thread and no JS is needed to advance it. Two unknowns, both needing a real iPhone.
  Side benefit: a started `AudioContext` is also the standard silent-switch unlock, which is the same
  mechanism DEC-064 already uses.
- **C. Pre-render a backlog** — the server already renders audio ahead of publication, so pay once, then
  go quiet, bounded depth.
- **D. Push** — the DEC-015 channel exists; a locked phone *shows* the narration.

Android needs none of it.

Full detail, sources and citations: `40-knowledge/ios-background-audio.md`. Tracked as **FU-140**.

## Part 2 — "what if it is a stream, and how much does silence cost?"

**A stream is the one thing that beats the screen lock**, because iOS forbids *starting* playback in the
background, not fetching it: a stream that starts in the foreground and never ends needs no second
`play()`. It still dies when the user switches apps (#198277).

**Silence has to flow at real-time rate** — an element drains its buffer in wall-clock time, and restarting
after an underrun needs `play()`. Pre-buffering does not reduce the average bitrate.

**Measured, our own server, 65 s of SSE with nothing to say:** `server.heartbeat` = **99 B every ~11 s =
9 B/s ≈ 0.54 KB/min**. The 420–564 KB in the same window was my own session's `message.part.delta` —
activity, not overhead. So transport is free; the silence media and the battery are not.

**Not measured:** codec silence. The only ffmpeg on this box is Playwright's stripped build, which has
`libvpx` and no audio encoders at all. PCM is exact arithmetic (96 000 B/s — unusable), MP3 at this
project's 48 kbps nominal is 6 000 B/s, and Opus DTX is the format designed for it — but the MP3 figure is
encoder-specific and must be measured on the encoder actually chosen.

Also recorded: iOS's append API is **ManagedMediaSource** (Safari 17.1), not MSE.
