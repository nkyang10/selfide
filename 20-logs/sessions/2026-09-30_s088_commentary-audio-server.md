# s088 — Server-side TTS: render the narration once, store it, serve it by hash

Session opened 2026-09-30 10:05 UTC
Goal: replace the on-demand speech proxy shipped in `8b8cc2a` with the user's
design — synthesize at narration time on the server, store the MP3 under a
content hash, ship only the hash, and let the client fetch and play the file.

## The user's proposal, verbatim in intent

> server side (markcode webui host side) when complete the commentary text,
> immediately fire a direct call to tts and download the mp3 to local storage
> with a filename in hash. and then pass the hash with commentary to webui
> client side. client side show the commentary and request the sound once
> received. and then play the sound in client side

Agreed, and it fixes the three real weaknesses of what I shipped: the reader waits
1–3 s for TTS after the text has already appeared, a TTS failure silently costs
the audio, and `host` is a request field (an SSRF sink I guarded rather than
removed).

## Three decisions the user took

1. **TTS failure → no fallback.** Pre-render only; `POST /commentary/speech` is
   deleted. Simplest and one failure mode: while the speech box is down, lines
   are text-only.
2. **Retention → cap per session + total size**, swept on write.
3. **Host and voice → server config only**, and the settings rows move to the
   **Admin** tab.

Audio **on/off** stays in the Commentary section: whether you want to hear it is a
per-browser preference, not an admin concern.

## Plan

`50-projects/p003-opencode-fork/notes/plan-commentary-audio-server.md`

The subtle part, recorded up front: the file name is **content-addressed**, so two
commentary rows can legitimately share one file. Retention must therefore unlink
a file only when no surviving row still points at its hash, or it breaks playback
for the row that does.

## What shipped

`cc63c93 feat(app): render the spoken narration on the server and serve it by hash`,
pushed to `origin/dev`. Deployed `1.1.20260930111050`, pid 1904297.

### The shape

Narration is written and published as **text only**, first. A fiber forked into the
instance scope then renders the audio, writes `<data>/commentary-audio/<hash>.mp3`,
records the hash on the row, and publishes the line a second time. The client shows
the text immediately and fetches `GET /session/{id}/commentary/audio/<hash>` only
when it goes to play.

Why the fork matters: on the critical path a 30 s speech timeout would delay the
text the reader is trying to read — the one thing the commentary exists for.

### Live proof

A real narration line, rendered by the deployed build:

```
seq 1   audio: c74fd04aa40ae83396d35fe95b95e526
        "Listed the utils directory, then read commentary-a…"
file    ~/.local/share/opencode/commentary-audio/c74fd04aa40ae83396d35fe95b95e526.mp3
GET     /session/{id}/commentary/audio/c74fd04a… → 200
        100,418 B base64 → 75,312 B → MPEG ADTS layer III v2, 24 kHz mono, 48 kbps
```

Route guards, all checked live: unknown hash **404**, `../../opencode.jsonc` **400**,
uppercase hash **400**, no auth **401**. `POST /commentary/speech` now falls through
to the SPA, identical to any unknown path.

## Three bugs, and what each one taught

**1. The render never ran.** `Deps.scope` was optional and the layer never set it, so
the `if (deps.scope)` guard skipped rendering entirely — a feature that compiles,
typechecks, and does nothing, with no error anywhere. The scope is now **required**,
taken from inside `InstanceState.make`. (`Scope.scope` does not exist in this Effect
version; it is `Scope.Scope`.)

**2. The reducer threw the audio publish away.** `applyDirectoryEvent` dropped any
entry whose `seq` it had already seen. That is correct for a reconnect replay and
fatal here, because the second publish **is** the audio arriving — so the client never
learned the hash and every line stayed silent. It now replaces the entry in place and
stays a no-op for a true replay. This is the bug that would have made the whole feature
look like it simply did not work.

**3. Retention nulled every row's audio.** Live evidence: MP3 files on disk, every
entry `audio: None`. The cut-off was `rows[retention]?.seq ?? Number.MAX_SAFE_INTEGER`,
and with fewer rows than the cap that matched **every** row in the session. Found by
checking the database rather than the filesystem — the files looked perfect. The
lesson is the one this whole session keeps teaching: check the thing downstream of the
one you just proved.

## A pre-existing bug this exposed

A narration stream that ended mid-JSON fell through to the raw-text path and stored the
partial contract as the line. Observed live in a panel as:

```
{"speak": true, "text": "commentary-watch
```

41 characters, JSON and all. `looksLikeContract` now treats a truncated contract as
silence, which is right on its own terms: a line the model never finished writing is
not a line worth saying out loud.

## Gates

- `bun turbo typecheck` — **30/30**
- app audio **18/0**; opencode commentary + commentary-audio **58/0**; event-reducer
  **23/0**; speech-target **23/0**

**The full `bun test` suite was skipped at the user's request.** So app-wide unit tests
and `test:httpapi` are **not** re-verified for `cc63c93` — the speech-route scenario in
the coverage harness was updated to the new route but never executed. That is the one
gate this commit is missing.

## Carried from the parallel session

`MAX_RETAINED_ENTRIES` row pruning in `commentary.ts` was still uncommitted and the
audio retention builds directly on it, so it went in with this commit. Stated in the
commit body rather than left to be discovered.

## Still open

- **`test:httpapi` unrun** against the new route.
- **Client-side playback not observed.** The server contract is proven end to end, but
  the audio toggle row did not render in the Playwright profile (`audioEnabled: "?"`),
  so no browser ever issued the `…/commentary/audio/<hash>` request. The client is the
  one link with no live evidence.
- **Only ~1 line in 3 turns produces narration at all** — the model's choice, unchanged.
- Disk usage is bounded but not reported anywhere.
