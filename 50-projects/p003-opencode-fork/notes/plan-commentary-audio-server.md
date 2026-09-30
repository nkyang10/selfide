# Plan — server-side TTS: render the narration once, store it, serve it

Session: s088 · Supersedes the on-demand design shipped in `8b8cc2a`
Status: approved by the user, three decisions taken (see Decisions)

## The problem with what is deployed

`8b8cc2a` renders speech **at playback time**. The browser asks
`POST /session/{id}/commentary/speech` when it is about to play a line, and the
server calls the LAN box then. Three consequences, all real:

1. **The user waits.** The line appears as text, then the browser blocks for
   1–3 s of TTS while the reader is already reading it.
2. **A TTS failure is a silent line.** The narration is fine; the audio is not;
   the user sees text and hears nothing, with no way to retry.
3. **The host and voice are client choices**, so `host` is a request field and
   therefore an SSRF sink — guarded, but guarded rather than absent.

## The design the user asked for

Render once, at narration time, on the server; ship only a hash.

```
commentary tick → row written (audio = null) → event published  ← text arrives now
                                    │
                                    └─ forked fiber ─ TTS ─ write <data>/commentary-audio/<hash>.mp3
                                                        └─ UPDATE row SET audio = <hash>
                                                        └─ publish session.commentary again
                                                                       ↓
client: shows the text, sees audio = <hash>, GETs the file, plays it
```

The TTS call **must not** be on the row-write path: a 3 s render would delay the
text the user is trying to read. Hence the fork.

## Decisions taken by the user

| Question | Answer |
|---|---|
| TTS fails or times out | **Pre-render only, no fallback.** No MP3 means a silent line. `POST /commentary/speech` is deleted. |
| Retention | **Cap per session + total size**, swept on write. |
| Host and voice | **Both from server config**, **hardcoded to `192.168.1.162:8880` in `opencode.json`**. **Not in settings v2** — no Admin rows, no client rows. |

The no-fallback answer is the simplest and it is a real cost, recorded here so it
is not rediscovered as a bug: when the speech box is down, every line is
text-only until it comes back. There is one code path and one failure mode.

## Decisions taken by me, and why

- **Hash = `sha256(voice + "\n" + text)`, first 32 hex chars.** The voice is in
  the hash so changing it invalidates the cache instead of replaying the old
  voice. 32 hex chars is 128 bits — collision-free at any plausible row count.
- **Content-addressed, so dedupe is free** — but it means **two rows can share
  one file**. Retention must therefore unlink a file only when *no surviving row*
  references that hash, or it will break playback for the row that still points
  at it. This is the one subtle part of the whole change.
- **`audio` is a nullable column on `session_commentary`**, not derived on the
  client. The client must be able to tell "no audio" from "audio not ready yet",
  and only the server knows that.
- **The event is republished, not a new event type.** The reducer has to learn
  to *replace* an entry with the same `seq` instead of appending it.
- **`Cache-Control: private, max-age=31536000, immutable`.** Content-addressed
  means the bytes never change for a URL — but the route is authenticated, so it
  is `private`, never `public`, or a shared cache would serve one reader's audio
  to another.
- **The hash is validated against `^[0-9a-f]{32}$` before it touches the
  filesystem.** It arrives in a path segment.
- **The `speechBaseUrl` guard stays.** The host is config rather than per-request
  now, so it is no longer an SSRF sink — but the guard still validates whatever is
  in the config file, at zero cost.
- **Audio on/off stays in the Commentary section.** Whether *you* want to hear it
  is a per-browser preference; where the box lives is config, not UI.
- **No settings surface at all for host/voice.** The user's call: hardcode the
  host in `opencode.json` and keep it out of settings v2 entirely. That removes
  the Admin-row work, the `PATCH /global/config` leaf-patching rule and the
  explicit-Save requirement — the whole "a config write disposes every open
  instance" hazard disappears with them.
- **No migration of the dead `localStorage` keys.** `commentary.audioHost` and
  `commentary.audioVoice` simply stop being read.

## Shape

1. **Schema** — `audio` nullable text on `session_commentary`, plus a migration.
2. **Render** — `commentary.ts` forks a fiber per accepted line: hash → dedupe
   check → TTS via config host/voice → write file → `UPDATE` row → republish.
   30 s timeout, 8 MB cap, failures logged and left as `audio = null`.
3. **Retention** — after a write, drop the oldest `audio` references past the
   per-session cap, then enforce the global byte ceiling, unlinking only hashes
   nothing points at any more.
4. **Serving** — `GET /session/{sessionID}/commentary/audio/{hash}` → the bytes.
   Authenticated like every session route, `audio/mpeg`, immutable, 404 when the
   file is gone or the hash is not a hash.
5. **Config** — `commentary.speech.{host,voice}` in the global config file, with
   the host written out explicitly as `192.168.1.162:8880`. **No UI.** The schema
   keeps the same defaults, so the feature works even if the key is absent.
6. **Client** — `CommentaryAudio` takes a `src` and plays it; the host/voice rows
   and the whole `POST /commentary/speech` call go away. The queue, the
   high-water mark, the gap and the no-overlap guarantee are untouched.
7. **Delete** `POST /commentary/speech`, its handler and its exercise scenario.

## Not covered, filed rather than dropped

- **Disk usage is now unbounded in principle.** The caps bound it; nothing
  reports it. An Admin row showing "N MB of stored narration" would be the honest
  follow-up.
- **No audio for a line written while the feature was off.** Text-only, forever.
- **The on-demand path is gone, so an old session cannot be re-spoken.** Its
  entries stay `audio = null`.
- **No way to change host or voice from the UI**, by choice. It is a config-file
  edit and a restart.
