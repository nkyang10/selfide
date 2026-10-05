# s097 — "I want to run with earphones and know when the agent needs me"

Follows s096. Research + scoping only; no code touched. Asked and answered in Cantonese.

## The reframe that mattered

The request is not "background audio". It is **eyes-free awareness of a rare, discrete event**: the agent
needs me; I intervened; it is unblocked and I can leave it alone. Continuous prose is the *worst* delivery
for that — it is what makes people turn the feature off. Every option below is ranked against
"how cheaply and how reliably does a rare signal reach an ear in a pocket".

## Ruled out, with a source

**`speechSynthesis`** — device-local TTS would have cost zero bytes and zero radio.
[speech synthesis stops working on iOS when Safari is backgrounded](https://weboutloud.io/bulletin/speech_synthesis_in_safari/),
and recovering needs a page refresh or a Safari restart.

## Ranked solutions

1. **Push, spoken by the OS.** Announce Notifications ([Apple](https://support.apple.com/en-us/102536))
   reads notification bodies on AirPods. We already have the plumbing — `push/push.ts`, VAPID, DEC-015 —
   but it fires on **one** event with the hardcoded English body `"An OpenCode session finished."` The gap
   is small and specific: a "needs you" trigger, a body written as a spoken sentence in the UI language,
   and distinct urgency wording. Zero streaming, works with Safari suspended, and it is what Cursor and the
   Claude-Code hook+ntfy setups converged on.
2. **Web Audio, not a media stream** — for when continuous narration really is wanted. The
   `AudioContext` that DEC-064's tap already resumes is what survives a screen lock, and on interruption
   `statechange → "interrupted" → resume()` needs no gesture. Lines play as `decodeAudioData` +
   scheduled `AudioBufferSourceNode`, so no `play()` ever happens. **Silence is free, so idle cost is 0
   bytes** — versus 96 000 B/s (PCM) or 6 000 B/s (MP3 CBR) of mandatory real-time silence for a stream.
   A workaround for Apple's policy, not a guarantee; iOS 26 has its own reports of PWAs losing audio.
3. **A phone call or SMS** — the only channel with no browser dependency at all.

## Transparency, which is design rather than plumbing

- An **audio state language**: short locally-synthesised tones for *working / needs you / done / blocked*,
  0 bytes each, learned in one outing. Speech reserved for the two events that deserve words.
- Say **who unblocked it** — "approved" after your intervention — because that is the question a runner
  actually has.

## Still true

Nothing here has been run on an iPhone (FU-136, FU-140). The push option is the one that needs no new
platform gamble, and it is also the smallest change.
