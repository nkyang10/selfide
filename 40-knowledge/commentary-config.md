# `commentary` configuration reference

Every key under `commentary`, its default, and what it actually costs. Read
alongside `tts-service-192-168-1-162.md`, which measures the *services* these
keys point at.

**Every field is optional.** An absent `commentary` section behaves exactly like
`commentary: {}`, and an empty `speech` / `special` behaves like no section at
all. Nothing here is required for the feature to work.

Defaults below are verified against the code, not remembered:

| Constant | File |
|---|---|
| `DEFAULT_RETENTION = 15` | `src/session/commentary-audio.ts:32` |
| `DEFAULT_MAX_BYTES = 512 MiB` | `src/session/commentary-audio.ts:34` |
| `CLOSING_GRACE_MS = 15_000` | `src/session/commentary.ts:75` |
| `SPECIAL_MIN_GAP_MS = 30_000` | `src/session/commentary.ts:68` |

---

## The current configuration on this machine

`~/.config/opencode/opencode.jsonc`:

```jsonc
"commentary": {
  "speech": {
    "host": "192.168.1.162:8880",                          // default render endpoint
    "hosts": ["192.168.1.162:8880", "192.168.1.162:8881"],  // endpoints the voice picker offers
    "voice": "cantonese"                                    // an alias on BOTH ports
  }
}
```

Nothing else is set, which means everything below is on its default.

---

## Narration — the running commentary

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | Narration at all. Note this is the **server** default; a fresh **browser** starts with narration **off**, because the client default is its own and deliberately differs. |
| `interval` | `10000` | ms between checks. This is the only timer in the engine. |
| `model` | `"session"` | `"session"` narrates on the model the turn is using; `"small"` on the provider's small model. `"small"` is the escape hatch if narration is too slow or expensive. |
| `maxEntriesPerTurn` | `20` | Per user turn, reset on each prompt. |
| `minActivityChars` | `120` | **The one that decides cost.** A tick with less than this much new activity never calls the model. Most idle ticks are skipped by it. |
| `narrationHistory` | `100` | Previous entries shown to the model for continuity. |
| `minGap` | `10000` | ms between two entries, measured from the newest **stored** entry, so it survives a restart. |

**What it costs.** A watched, busy session spends a model call roughly every
`interval`, gated by `minActivityChars` and `minGap`. Measured on this box a
single line takes **43–99 s** with a reasoning model, so the real cadence is
"whenever the model finishes", not every 10 seconds. `maxEntriesPerTurn` is
therefore rarely the binding constraint.

---

## `commentary.speech` — where and how it is spoken

| Key | Default | What it does |
|---|---|---|
| `host` | `192.168.1.162:8880` | The endpoint rendered with when nothing else says otherwise. |
| `hosts` | `host` alone | Endpoints the voice picker offers, `host` first. |
| `voice` | `cantonese` | Voice **name or alias**; the service resolves both. |
| `retention` | `15` | Stored audio files kept per session. |
| `maxBytes` | `536870912` (512 MB) | Ceiling on stored narration across **all** sessions. |

### `host` vs `hosts`, and why both exist

`:8880` and `:8881` are **two builds of one service**, not one service on two
ports. `:8880` proxies Azure's 322 voices; `:8881` bakes exactly one
(`canto-tts-nano-v1`, 17 aliases). **Both answer to `cantonese`, with different
audio.** Cross-proved: `zh-HK-HiuMaanNeural` is **400 on 8881**, and
`canto-tts-nano-v1` is **400 on 8880**.

So a dropdown of bare voice names would be a trap — pick the `:8881` voice, the
server renders on `:8880`, and **every line comes back text-only** with a 400 the
reader never sees. The endpoint therefore rides alongside the voice in four
places, and each is load-bearing: the content hash, the store, the lease and the
option value. See DEC-061.

`host` is deliberately still `:8880`: it is what a browser that has never opened
the picker renders with, and `:8880` answered throughout while `:8881` was
refusing connections (for ~90 s, which means *still starting*, not *wrong port*).

### Where the files go, and what "retention" really costs

Audio is rendered **on the server** when the line is written and stored under its
content hash:

```
~/.local/share/opencode/commentary-audio/<hash>.mp3
```

`hash = sha256(voice + "\n" + text)`, first 32 hex. The voice is in it, so
changing the voice invalidates the store instead of replaying what the previous
voice said. Real files measured here: **12–98 KB**, so `retention: 15` is roughly
**0.2–1.5 MB per session**.

The browser never holds a file: it fetches base64, decodes to a `Blob`, plays it
from an object URL and revokes it. **Nothing is cached in the browser.**

Retention unlinks a file only when **no surviving row references its hash** —
files are content-addressed and shared between rows, so unlinking by age alone
would break playback for the row that still points at it.

---

## `commentary.special` — the two lines that are not narration

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | Produce both special lines. |
| `minGap` | `30000` | ms between two special lines, so a flapping session cannot spam. |
| `closingGrace` | `15000` | How long the session must sit idle before "all done" is said. |

- **`closing`** — a fixed phrase in the web UI's own language (`All done.` /
  「工作完成」), so half a second of audio says what a paragraph could not. **No
  model call.** The phrase is resolved by the client and travels on the lease,
  because the server has no i18n at all.
- **`prompt`** — model-written, because its job is to name the **real** options
  and that cannot be a fixed string. It wins over `closing`: a session blocked on
  a permission is *also* technically idle, and "done" would be a lie.

`closingGrace` is why the line is honest: a reader who is about to type again
never hears it, because the session goes busy again long before the grace runs out.

---

## What is deliberately **not** configurable

| | Where it lives | Why |
|---|---|---|
| Whether a browser plays sound | per-browser, panel header | A reading preference, not a server setting — and the toggle doubles as the user gesture that satisfies autoplay policy. |
| Which voice a browser picked | per-browser, panel header | Carried on the lease; the picker only offers voices from `hosts`. |
| The closing phrase | per-browser, translated | The server cannot know the reader's language. |

The client **cannot** choose a host outside `hosts`, and whatever it sends still
goes through `speechBaseUrl` before any request is made — loopback, link-local
(the `169.254.169.254` metadata address), port 0 and out-of-range ports are all
refused.

---

## Troubleshooting

| Symptom | Look at |
|---|---|
| No commentary at all | Is the browser toggle on? Narration is **off by default per browser**. |
| Text appears but never any sound | The mute icon in the panel header. Muted by default. |
| Every line text-only, no error | The voice belongs to the *other* endpoint — the DEC-061 trap. Check `hosts`. |
| One line sounds, the next is silent | The first is a fixed closing phrase; the next may not have rendered. Check `testing/web-4447.log` for `commentary audio`. |
| A toast saying speech failed (404) | The row's file is gone. Reconcile runs once per instance and clears it. |
| Disk filling | `maxBytes` and `retention`; the directory is `~/.local/share/opencode/commentary-audio/`. |