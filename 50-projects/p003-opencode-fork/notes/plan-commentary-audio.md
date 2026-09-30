# Plan — FU-122: spoken commentary (text-to-speech for the narration)

> **Status:** PLAN ONLY — no feature code written. Prepared 2026-09-29 (UTC), session **s085**.
> **Builds on:** FE-028 / DEC-057 (commentary), FU-111 (mobile), FU-120 (no echoing the reader).
> **User's request (verbatim):**
> *"new feature to follow up the commentary feature / i have build a text to speech api /
> `curl -X POST http://192.168.1.162:8880/v1/audio/speech -H "Content-Type: application/json" \
> -d '{"input":"你好","voice":"cantonese"}' -o out.mp3` / add in setting v2 under commentary /
> on-off audio commentary / audio speech api url ip with port default 192.168.1.162:8880 /
> audio voice name default cantonese / for the audio feature, make it available with the commentary text
> at the same time. / since this is play one time only, no cache / only play new commentary /
> audio in a queue no overlap with some time gap between each audio / only play the opening agent chat
> tab's new commentary audio"*
> **User's decisions** (asked before planning): the TTS service was not up at first — **"try again now"**,
> after which it answered; and audio plays for the **foregrounded tab only**.

---

## 0. Executive summary

Everything needed already exists except the audio itself. The commentary store, the SSE event, the
settings-v2 section, the persisted layout store and the active-tab concept are all in place, so this is
**one new module plus three settings rows**.

| Requirement | Reality |
|---|---|
| Speak each new commentary line | ✅ the lines arrive as `session.commentary` events and already sit in `sync().data.commentary[sessionID]` |
| Settings under Commentary | ✅ `settings-v2/general.tsx` already has a `CommentarySection` (enabled + preferences) to extend |
| API URL / voice, with defaults | ✅ new fields on the same persisted `layout.commentary` store; no new store |
| At the same time as the text | ✅ the event is the trigger — audio is fired from the same store write |
| One-time, no cache | ✅ the design is stateless: audio is a function of "an entry I have not spoken", tracked by `seq` |
| Queued, no overlap, with a gap | ✅ needs a small queue — see §3 |
| Only the foregrounded tab | ⚠️ **this changes the lease** — see §2, it is the one non-obvious part |

**Shape: 1 new module (`commentary-audio.ts`) + 1 settings section extended + 1 store field. No server
change, no new route, no new event, no DB change.** The narration text pipeline is untouched.

---

## 1. The API, measured rather than assumed

Probed live on `192.168.1.162:8880` (the first attempt got `connection refused` — the service was still
starting; it answered on retry):

| Probe | Result |
|---|---|
| `{"input":"你好","voice":"cantonese"}` | **200**, `audio/mpeg`, **12,528 bytes**, **242ms** — a real `MPEG ADTS layer III, 24 kHz mono` |
| ~30-word commentary line | **200**, **38–41 KB**, **0.32–2.36s** |
| unknown voice | **400** `application/json` — `{"error":"unknown voice '…'. did you mean: []? GET /v1/audio/voices?locale=zh-HK for Cantonese voices."}` |
| empty input | **422**, 133 bytes |

**It is an Azure-Speech-compatible service**, which matters twice over:

1. **`cantonese` is an alias, not a voice name.** `GET /v1/audio/voices?locale=zh-HK` returns three
   Cantonese voices, and `cantonese` resolves to **`zh-HK-HiuMaanNeural`** (Female, Hong Kong). The other two
   are `zh-HK-HiuGaaiNeural` (Female, Online-Natural) and `zh-HK-WanLungNeural` (Male, Cantonese-Male).
2. **There are 322 voices and 23 friendly aliases** (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`,
   `en`, `english`, `en-female`, `en-male`, …). So the voice setting can offer the short names the user
   already knows, and the service resolves them.

**Design consequence:** the voice field is a **free-text string sent verbatim**, defaulting to
`cantonese`, exactly as the user specified. It is *not* a hard-coded dropdown of 322 voices — that would be
a 322-entry translation surface and would break the moment the service's voice list changes. A
`GET /v1/audio/voices` call can back a *suggestion* later; the field stays free text so any alias or full
name works.

**Failure behaviour, from the probes:** a bad voice is a **400 with a JSON error**, not a hang. So a
mistyped voice is a **visible, attributable error** (toast, once, then back off) rather than silence.

---

## 2. The one non-obvious requirement: "only the opening agent chat tab"

The user chose **foregrounded tab only**. This is not just an audio filter — **it changes the lease**, and
that is the part worth stating plainly.

Today the lease is: desktop watches while the commentary column is open; mobile watches once the tab has
been latched. Both hold **while the tab is in the background**. With audio, that becomes wrong in the
user's ears: a backgrounded tab would keep generating narration that nobody sees, and — worse — the moment
two tabs are open, the queue would interleave two sessions' audio.

So audio forces a decision about generation, not just playback:

| Option | Behaviour | Cost | Verdict |
|---|---|---|---|
| **A. Gate the lease on foreground** (recommended) | A backgrounded tab holds no lease, so it stops narrating. Coming back re-takes it. | Narration you "missed" while away is simply not generated | **Chosen.** It is the only option where the user's ears and the token bill agree, and it reuses the existing `commentaryShouldWatch` policy with one more term |
| B. Keep narrating, mute audio when backgrounded | Text keeps accruing in every tab; only the focused one is voiced | Tokens spent on tabs nobody is reading — the thing the lease was built to avoid | Rejected |

**Implementation of A:** `commentaryShouldWatch` already takes `isDesktop`, `panelOpened`, `latched`,
`enabled`. Add `foregrounded`, sourced from the app's existing visibility plumbing
(`document.visibilityState` + `visibilitychange`, already used in `layout.tsx:440`,
`server-sdk.tsx:345` and `directory-layout.tsx:101`) — **not** invented. One extra term, and the same
predicate now governs both spending and speaking, which is the property that keeps them from drifting.

The *per-tab* part ("only one tab speaks") falls out of `foregrounded` for free: a tab that is not the
foregrounded one is not narrating, so it has nothing to queue.

---

## 3. The audio module

`packages/app/src/utils/commentary-audio.ts` (new). Deliberately **plain TypeScript, not Solid** — it owns
an `Audio` element and timers, has no reactive state, and must be testable without a component tree
(`packages/app` has no `.test.tsx`).

```
enqueue(entry, { baseUrl, voice, sessionID })
  ├─ ignore if audio disabled, or this entry's seq was already spoken
  ├─ push { seq, sessionID, text } onto the queue
  └─ pump()

pump()
  ├─ if playing, or the gap since the last clip has not elapsed → return
  ├─ shift the queue; POST /v1/audio/speech {input, voice}
  ├─ on 200 → objectURL → audio.play() → on 'ended' → release + schedule the next after GAP_MS
  └─ on error → toast once, drop the clip, continue (one bad voice must not wedge the queue)
```

**The invariants, stated so they can be tested:**

1. **One clip at a time.** A single `Audio` element; `pump()` is a no-op while `playing` is true. This is
   what "no overlap" means mechanically.
2. **A gap between clips.** `GAP_MS` (default **400ms**) is measured from the previous clip's `ended`, not
   from when it was requested, so a slow fetch never eats the gap.
3. **Only new entries.** Spoken-ness is tracked as a `Set<sessionID:seq>` plus a high-water mark per session.
   Re-opening a panel, a reconnect replay, or the 200-entry initial paint **must not replay history** — the
   store is populated with old entries on load, and audio is explicitly "new commentary only". A per-session
   high-water mark (`seq` is monotonic) is enough and cannot leak: it is seeded from the first entry seen.
4. **No cache.** Every line is fetched fresh. Object URLs are revoked on `ended`. The browser HTTP cache is
   bypassed with `cache: "no-store"` so a replayed line cannot be served from disk.
5. **Failure is non-fatal and visible.** A `400` (bad voice) toasts once with the server's own message and
   then suppresses repeats for that voice, so a misconfigured voice does not produce a toast every 10s.
6. **Autoplay policy.** Browsers block audio until the user has interacted with the page. Since the toggle
   lives in a settings dialog the user *clicked*, the first `play()` is user-initiated and allowed; the
   queue resumes from there. If a play is rejected, the entry is dropped and the queue continues — never a
   stuck "playing" flag, which is the classic failure here.

**Why not fetch-and-decode in a Worker / cache the audio?** The user said no cache, and lines are ~40KB and
arrive at human pace. A blob URL per clip is the simplest thing that satisfies "one time only".

---

## 4. Settings (extends the existing Commentary section)

Three rows appended to `CommentarySection` in `settings-v2/general.tsx` — same component, same persisted
`layout.commentary` store, same i18n pattern:

| Row | Control | Default | Notes |
|---|---|---|---|
| **Audio commentary** | switch | **off** | Off by default: audio is intrusive and browsers gate it. Turning it on is also the user gesture that satisfies autoplay |
| **Speech API** | text field | `192.168.1.162:8880` | Stored as `host:port` exactly as specified and rendered into `http://<host:port>/v1/audio/speech`. A field rather than a scheme dropdown because the user specified an IP and port, and a wrong scheme is the likeliest misconfiguration |
| **Voice** | text field | `cantonese` | Free text so aliases (`cantonese`, `en-male`, …) and full names (`zh-HK-HiuMaanNeural`) both work. A 400 from the service is surfaced verbatim, which is better UX than a stale dropdown |

**The audio rows are disabled while the master commentary switch is off** — the same pattern the existing
preferences textarea already uses, so it reads as one settings group.

All three are **per browser** (they live in the same per-server layout store as the other commentary
settings), so a phone and a desktop can differ — which is what you want, since audio is a desktop/headphone
thing.

---

## 5. What triggers playback

The trigger is the **store write**, not the panel:

- `event-reducer.ts` already appends every new `session.commentary` entry to `sync().data.commentary[sessionID]`.
- A single subscriber in the session view watches that list and calls `enqueue()` for entries whose `seq` is
  above the session's high-water mark.
- Because the lease is already foreground-gated (§2), **anything arriving here is for the foregrounded
  session** — the "only one tab speaks" rule needs no extra filtering.

This is deliberately **not** wired into the panel component: the panel unmounts when you close it, and audio
must keep going. The panel is a view; the store is the event.

---

## 6. Tests, benchmark, gates

**Unit (`commentary-audio.test.ts`, pure logic extracted from the module):**
- the queue never runs two clips at once (given a `play` that never ends, the second entry does not start);
- the gap is measured from `ended`, not from request time;
- an entry at or below the high-water mark is **not** spoken (the "only new" rule), and the high-water mark
  survives a panel remount;
- a failed request drops that clip and the **next one still plays** (a wedged queue is the worst failure);
- a rejected `play()` (autoplay blocked) releases the lock rather than stalling.

**Not unit tested, and said so:** actual audio output and the autoplay gesture. Those are checked live.

**Live check on :4447, after deploying:**
1. Settings → General → Commentary shows the three new rows; toggling audio on persists across a reload.
2. With audio on and a real turn running, **one line plays as its text appears** — confirm the audio and the
   panel line are the same entry.
3. Open a **second** agent tab, start work in both: only the focused tab's audio plays.
4. Switch to another browser tab (or another app): audio **stops**, and the lease is released (no
   `agent=commentary` streams in the log while backgrounded).
5. Type a bad voice → one toast naming the service's own error, then silence; the queue keeps working.
6. Confirm no overlap: three rapid lines produce three sequential clips with gaps, not overlapping audio.

**Gates:** `bun turbo typecheck` 30/30 · app `bun run test:unit` (never bare `bun test` — FU-109) ·
i18n parity 5/5 (3 new keys × 65 locales, English values per the FU-026 pattern) · oxlint 0 errors.

---

## 7. Risks

1. **Autoplay blocking** is the most likely first-run failure: a browser that has never seen a user gesture
   on the page rejects `play()`. Mitigated by the settings-dialog gesture and by the release-not-stall rule
   (§3.6), and it is the first thing the live check will hit.
2. **A mistyped voice** is a `400` on **every** line, which without the once-per-voice backoff would toast
   every 10 seconds. §3.5 handles it.
3. **Foreground-gating the lease changes existing behaviour**: a backgrounded tab stops accruing narration, so
   you can lose lines you would previously have had waiting for you. That is the deliberate trade (§2) and it
   should be in the settings copy, not hidden.
4. **The lease now depends on `document.visibilityState`**, which is exactly the signal iOS Safari handles
   unreliably — `directory-layout.tsx:65` carries a comment about that. The existing code works around it for
   sync; the same workaround is reused rather than reinvented.
5. **Voice list drift.** Free text never breaks; a hard-coded dropdown would. §1 explains why it stays free.
6. **Two windows, one browser**: `visibilitychange` is per-document, so two *windows* can each be
   "visible". Two visible windows would both narrate and their audio could interleave. Rare, and the queue is
   per-document so they would not corrupt each other — but it is a known limit, not a solved problem.

---

## 8. Explicitly out of scope

- Server-side audio generation, or proxying the TTS through opencode (it is a LAN service; the browser can
  reach it directly, and proxying would add a route for no gain).
- Caching, pre-fetching, or queueing audio while backgrounded.
- Selecting voices by locale automatically, or a 322-entry voice picker.
- Volume, speed, pitch, or playback-position controls.
- Reading commentary aloud for sessions other than the foregrounded one.
- Any change to how the narration text is generated (FE-028 is untouched).
