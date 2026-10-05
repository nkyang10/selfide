# iOS background audio — what the platform actually allows

Written 2026-10-03 (UTC), for FU-136. Everything below is about **iOS Safari / iOS standalone PWAs**;
Android Chrome is a different story and is at the end.

The question that prompted this: "the page is playing a sound, the phone goes to sleep — does it keep
playing, and can we make it behave like background music?"

## The two states are different, and only one of them works

| What you do | Does the sound continue? | Source |
|---|---|---|
| Screen locks / auto-locks, **still in Safari** | **The clip that is already playing finishes.** The web process is deliberately kept alive while audio plays. | [WebKit #173332 comment 2 (Eric Carlson, Apple)](https://bugs.webkit.org/show_bug.cgi?id=173332) — "The web process, normally suspended when in the background, is kept alive while playing audio" |
| …then the clip ends | **Silence.** You cannot start the next one. | [WebKit #173332 comment 24](https://bugs.webkit.org/show_bug.cgi?id=173332) — "**the issue isn't that `ended` event is not fired. It's that `audio.play()` does nothing when the app is in the background or the screen is locked**" |
| Switch to another app, or go Home | **Stops**, and there is no workaround — this is broken for standalone PWAs too. | [WebKit #198277](https://bugs.webkit.org/show_bug.cgi?id=198277) — "Audio still stops when switching to another app, or going to Home Screen. background audio is broken in both standalone and fullscreen, iOS does not support it" |

So the ceiling on iOS is **one clip, and only while the user stays in Safari**. "Background music" behaviour —
a queue that keeps advancing — is not available to a web page on iOS. There is no background execution
mode, no background fetch, and Apple has not given Safari a background-audio capability.

The bug worth reading in full is **173332**: it was filed in 2017 as "`.ended` does not fire when the
screen is off", patched in 2019, then **reopened by regression** in iOS 17.2, and finally closed in
January 2024 with the finding quoted above — the event *does* fire; the `play()` that follows is what
silently does nothing. Anyone planning a playlist-style player should read comment 24 and the successor
bug **261554** rather than the title.

## What this app does about it, today

Nothing — and that is deliberate. `commentaryShouldWatch` releases the commentary lease the moment
`document.visibilityState` goes hidden (`packages/app/src/pages/session/commentary-watch.ts:41`), so a
locked phone stops *generating* lines within a heartbeat. The reason is cost, not capability: FU-122's
argument was that a hidden tab must not keep paying a model call every ten seconds to narrate nobody
hears.

Consequence: even if background playback worked, there would be nothing new to play. Any "keep talking
while my phone sleeps" feature has to change **both** halves — what the browser will play, and whether we
pay to keep producing.

## The options, honestly

**A. Screen Wake Lock — the only platform-supported way to get what you asked for.**
`navigator.wakeLock.request('screen')` is supported in iOS Safari **16.4+**
([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API),
[web.dev: supported in all browsers since May 2024](https://web.dev/blog/screen-wake-lock-supported-in-all-browsers)).
The screen never dims, JS keeps running, and every existing mechanism — the queue, the 400 ms gap, the
15 s lease heartbeat, the latch — keeps working untouched. Cost: battery and a screen that stays on.
Pair it with the audio toggle so it exists only while the commentary is actually speaking.

**B. Web Audio with lookahead scheduling — could get a *few* clips past the screen lock, and might fix the
silent switch.**
Schedule decoded buffers on the `AudioContext` clock ahead of time (the technique Chrome's own tracker
describes) rather than calling `play()` per clip. The audio then runs on the native thread, so no JS is
needed to advance it. Two unknowns, both needing a real iPhone: whether iOS keeps scheduling a context
whose page is backgrounded, and how much battery the process costs while locked. There is a real hint in
the other direction — [a PWA user reports iOS kills the audio context when it is *paused*](https://www.reddit.com/r/PWA/comments/1h2vmod/ios_pwa_music_playback_stops_when_locked/)
— which is consistent with "a running context survives, an idle one does not".
A side benefit worth knowing: audio routed through a started `AudioContext` is the standard iOS trick for
getting **out of the ringer category**, which is what makes a phone on silent play sound at all. That is
the same mechanism DEC-064 already uses in the tap handler.

**C. Pre-render a backlog and accept a fixed depth.**
The server already renders audio before the line is published (`commentary-audio.ts`), so it could render
the next N lines ahead and let the client download them while foregrounded. Then a locked phone plays
until the backlog runs out. This bounds the problem instead of solving it, and the lease still has to be
kept (or the backlog rendered and the lease dropped, which is the interesting version: pay once, then go
quiet).

**D. Stop asking the browser to do it.** For real background audio on iOS the only reliable answer is a
native app with a background-audio mode. The nearest thing available inside a web UI is the push channel
already built in DEC-015 — each line as a notification, so a locked phone *shows* the narration even
though it cannot speak it.

## Android, for contrast

Chrome keeps the renderer alive for playing media, so audio continues with the screen off and the page is
not frozen; Media Session gives lock-screen controls. Memory pressure is the risk, not policy. If the
feature is for phones generally, Android needs none of the above.

## What nobody has verified

Everything about **this app on an iPhone**: that the clip finishes with the screen locked, that the silent
switch is defeated by the `AudioContext`, and whether option B survives at all. Chromium under
`--autoplay-policy` is not a substitute (s095). One iPhone, one minute, settles option A.
## Follow-up: does making it a *stream* help, and what does silence cost? (same day)

**A stream is the one mechanism that beats the screen lock.** iOS's blocker is *starting* playback
while backgrounded, not *fetching* it. A single stream that begins while the reader is looking at the page
and **never ends** needs no second `play()` call, so it keeps going through a screen lock. That is the whole
of the benefit — switching apps still kills it (#198277), so it survives a locked screen and nothing more.

**The price is that silence must flow at real-time rate.** A media element consumes its buffer in wall-clock
time, so an idle stream that stops sending underruns and stalls — and restarting it needs `play()`, which is
exactly what is forbidden in the background. Pre-buffering does **not** reduce the average bitrate (it only
lets you send in bursts, saving radio wake-ups, not bytes). So the honest number is: *the cost of silence at
the codec you choose.*

| Silence encoding | Cost | Note |
|---|---|---|
| PCM 48 kHz / 16-bit / mono | **96 000 B/s ≈ 5.76 MB/min ≈ 338 MB/h** | exact arithmetic, no encoder needed — and unacceptable |
| MP3 CBR at the format this project already uses (48 kbps, 24 kHz mono) | 6 000 B/s ≈ 360 KB/min | nominal bitrate; a real encoder emits far less for pure silence, but **it is encoder-specific and must be measured** |
| Opus with DTX | a few bytes per 20 ms frame | the format is built for this; still measure rather than assume |

**Could not measure the codec rows on this box**: the only ffmpeg available is Playwright's stripped build,
which has `libvpx` and **no audio encoders at all** (`-encoders` lists nothing but VP8). So any figure for
"how many bytes is one second of MP3 silence" has to come from the encoder actually chosen, measured.

**Transport overhead, measured here on our own server.** The app already holds an SSE connection open
(`GET /global/event`). Captured for 65 s and parsed by event type:

```
server.heartbeat    6x    99 B each     9 B/s   0.54 KB/min
```

**That 99 bytes every ~11 seconds is the entire cost of keeping a stream alive with nothing happening.**
The 420–564 KB those two captures moved was *my own session working* (`message.part.delta` × 129/471) —
activity, not overhead. So the wire cost of an idle-but-open connection is negligible; **the cost that
actually matters is the silence media itself, and the battery.**

## The iOS append API is ManagedMediaSource, not MSE

Plain MSE is not on iOS. Apple shipped **Managed Media Source in Safari 17.1** for iPhone/iPad
([WebKit, Oct 2023](https://webkit.org/blog/14735/webkit-features-in-safari-17-1/)), which "adds the
capabilities of MSE, without any of the drawbacks" — including better buffer management and lower power,
which is precisely the property a gapless narration stream needs. One caveat from the same post: support
"is only available when an AirPlay source alternative is present, or remote playback is explicitly
disabled", which needs checking for an audio-only case on a real device.

## Recommended shape, if this is ever built

One long-lived element fed by a server endpoint that stays open, started once from a real gesture; the
server streams rendered MP3 lines back to back and **cheap silence in between**, with a bounded backlog.
Two preconditions that have nothing to do with audio: **the lease must be held while hidden** (it is
released today, `commentary-watch.ts:41`, because a hidden tab must not keep paying), and a real iPhone
must confirm that a continuously-fed stream survives the lock at all.

## The actual use case, and the solution space (2026-10-03, s097)

The requirement is not "background music". It is: **running with earphones, eyes-free, knowing when the
agent needs you** — and knowing whether it is your intervention that unblocked it, so you know when it is
safe to leave it alone. That reframing changes the ranking of every option above, because the signal that
matters is rare and discrete (**"needs you"**), not continuous prose.

### Dead end, ruled out with a source: `speechSynthesis`

Synthesising on the device would have cost zero bytes and zero radio. It does not work:
[speech synthesis stops working on iOS when Safari is backgrounded](https://weboutloud.io/bulletin/speech_synthesis_in_safari/)
— "this seems to occur when the app goes into the background WHILE it is in the midst of speaking. You're
required to either refresh the page or restart Safari to get the speech synthesizer working again."
(Safari 15.4+, and this bulletin is the specialist tracker.) **Do not build an ear channel on local TTS.**

### Solution 1 — the one the ecosystem actually uses: push, spoken by the OS

Notifications are announced by Siri on AirPods/Beats — [Apple support: announce notifications with
Siri](https://support.apple.com/en-us/102536), Settings → Notifications → Announce Notifications. The
notification body is what gets read aloud, so a phone in a pocket, screen locked, delivers the sentence
into the ear with **no streaming at all**.

We already have the plumbing: `push/push.ts` (VAPID, DEC-015, iOS 16.4+ with a Home Screen install). Today
it fires on one event with a hardcoded English body — `"An OpenCode session finished."` — so what is
missing is small and specific:

1. a **"needs you"** trigger (permission request / question), which the app already models;
2. the body written **as a spoken sentence**, in the UI's language, not a status string;
3. distinct wording per urgency, because a runner must learn to tell them apart.

This is the same shape every coding agent converged on: Cursor's forum thread "Push Notifications
(Mobile/Desktop) When Agent Needs User Input or Approval", and hook-plus-ntfy setups for Claude Code.
**Cheapest, most robust, and it is the only channel that also works when the phone is in a pocket with the
screen off and Safari suspended.**

### Solution 2 — for genuinely continuous narration: Web Audio, not a media stream

This is the important correction to "just stream it". The community workaround for iOS is an
`AudioContext`, not an `<audio>` element:

- **Start it inside a gesture** — which DEC-064's tap handler already does (`commentary-audio.ts`,
  `resume()` → `wake()`).
- **Handle the interruption.** [niconiconi's note](https://niconiconi.neocities.org/tech-notes/force-enable-web-audio-autoplay-on-ios-for-incompatible-apps-via-userscript/)
  is the clearest write-up: "if you minimize the browser or turns off the screen, an AudioContext may
  become interrupted… `running -> interrupted` … **Previously allowed, we can resume it without user
  interaction.**" So `onstatechange` → `interrupted` → `resume()` needs no gesture. `interrupted` is an
  iOS-specific state, not in the Web Audio spec.
- Then play each line as `decodeAudioData` → `AudioBufferSourceNode.start(atTime)`, scheduled with
  lookahead. No `play()` call ever happens, so the "cannot start playback in the background" rule is never
  hit.

**The cost answer to the question actually asked:** with Web Audio, **silence is free**. It is a local
audio graph, not bytes on a wire. Idle cost is **0 bytes** — versus the streaming design's
96 000 B/s (PCM) or 6 000 B/s (MP3 CBR) of mandatory real-time silence. Data is then only the lines, which
the server already renders ahead of publication (s088), at 48 kbps mono — a 30-word line is 38–41 KB of
real speech. Cost while speaking ≈ 6 kB/s; cost while quiet ≈ 0.

Caveats, stated plainly: this is a workaround for Apple's policy, not a guarantee (the same note calls it
exactly that, and notes the userscript approach "doesn't always work"); the silent-looping-`<audio>` variant
is the same idea reported from the other direction (a quiet long loop keeps the page and its WebSocket
alive on iOS screen lock). And iOS 26 has its own reports of audio breaking in PWAs and needing Safari's
data cleared. **Nothing here has been run on an iPhone.**

### Solution 3 — the only thing that ignores the browser entirely

If it must work while the user is in another app, use the OS: a **phone call or SMS when intervention is
needed**. No browser, no audio session, no policy. Costs money per event and is crude, but it is the only
channel with no platform dependency — and for "I am running and I want to know *now*" it is the honest
answer.

### Transparency, which is the part that is actually design

- **An audio state language instead of prose.** Short, distinct, locally synthesised tones for
  *working / needs you / done / blocked* — 0 bytes each, and a runner learns them in one outing. Speech is
  then reserved for the one event that deserves words.
- **Only two events deserve interruption.** "Needs you" and "done". The 10-second narration tick is
  background texture; it is what makes people turn the whole thing off.
- **Answer the question the user actually asked out loud:** after you intervene, say so — "已批准" /
  "approved" — so the ear can confirm *your* action unblocked it. That is the difference between a
  notification channel and a commentary channel.
