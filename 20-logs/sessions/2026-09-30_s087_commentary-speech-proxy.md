# s087 — Spoken commentary: find why the browser never asked for audio

Session opened 2026-09-30 08:36 UTC · closed 2026-09-30 09:56 UTC
Goal: the deployed build spoke nothing in the browser and no `/commentary/speech`
request was ever observed. Find the real cause, fix it, ship it, and prove it.

## What was actually wrong

Six separate causes, stacked so that each one hid the next. Only the last is a
property of the feature.

| # | Cause | Who found it |
|---|---|---|
| 1 | Audio commentary **defaults off**, and every Playwright run is a fresh browser profile, so the toggle enabled in one run is absent in the next | 08:46 — `opencode.global.dat:layout` showed `audioEnabled: true` only after an explicit toggle |
| 2 | The **commentary panel must be open** or no line is ever narrated (that is what takes the lease) | 08:53 — body text ended in the question dock |
| 3 | A session **blocked on a question dock has no composer**, so the turn never ran and the "missing composer" looked like a bug | 08:53 — `contenteditable: 0`, dock present |
| 4 | I created test sessions with the **base64 token as a literal directory**, so `prompt_async` died on `FileSystem.realPath` before the model ran | 08:56 — `logs/deploy/opencode.log` |
| 5 | Commentary needs **>120 chars of new activity** on a 10s tick (`MIN_ACTIVITY_CHARS`), so a two-line answer never narrates | 08:58 |
| 6 | Narration is **model-decided and stochastic** — roughly one session in three emits a line at all | 09:01–09:25 |

Causes 1–5 were harness mistakes. Every one of them looked exactly like a code
defect from the outside, which is why "no speech request" kept reproducing.

## The real code defects, fixed

1. **CORS.** The LAN service answers a browser preflight `OPTIONS` with `405` and no
   `Access-Control-Allow-Origin`. `curl` worked only because it sends no `Origin`.
   Fixed earlier in the session by proxying: `POST /session/{id}/commentary/speech`
   fetches server-side, returns base64.
2. **401.** The proxy is an ordinary authenticated route and the client sent no
   credential. Both login modes are now covered — Basic when the SDK holds one, and
   `credentials: "include"` for the session cookie `/login` actually hands out.
   Verified: cookie-only → 200, no credentials → 401.
3. **SSRF.** `host` is a user setting reaching an outbound request. `speechBaseUrl`
   now accepts only a bare host / host:port / LAN name and refuses loopback,
   link-local (incl. `169.254.169.254`), `localhost`, `0.0.0.0`, port 0, ports
   >65535, and any host carrying a scheme, path, query or credentials.
4. **Unbounded response.** Capped on the declared `content-length` and again on the
   bytes that actually arrived.

The SSRF unit test caught a real gap while being written: `:99999` matched the
five-digit port pattern and was allowed through.

## Proof it works

Run the exact `CommentaryAudio.speak` sequence in the page (same-origin proxy,
auth, `{input, voice, host}`, `cache: no-store`, base64 → Blob → object URL →
`HTMLAudioElement`). Both lines returned **200** and played to `ended: true`:

| File | Bytes | Duration | Format |
|---|---|---|---|
| `/tmp/opencode/audio-clips/direct-1.mp3` | 26,640 | 4.440 s | MPEG ADTS layer III v2, 24 kHz mono, 48 kbps, first-frame sync `0xfff3` |
| `/tmp/opencode/audio-clips/direct-2.mp3` | 35,424 | 5.904 s | same |
| `/tmp/opencode/audio-clips/deploy-verify.mp3` | 15,984 | — | same, from the final deployed build |

Natural path, captured with instrumentation: `[audio] effect {on: true, seq: 1}` →
`[audio] enqueue {seq: 1, accepted: true}` → `[audio] speak called`. The stochastic
narration made a full natural capture unreliable within a scripted window, which is
why the chain was verified directly as well.

## Gates

- `bun turbo typecheck` — **30/30**
- app suite — **739 pass / 9 fail**. The 9 are **pre-existing**
  `solid-js/web/dist/server.js` module-load errors in the comments, terminal and
  prompt-input tests. Proven pre-existing: re-ran with my three app files stashed →
  738/9, i.e. the same 9 and mine is the +1.
- `packages/app` audio tests — **17/0** (added one pinning cookie-mode auth)
- opencode commentary + speech-target + commentary-http — **74/0**
- `bun run test:httpapi` — **216 pass, 0 missing**, after adding the speech route to
  the coverage harness so it cannot be missed again
- `speechBaseUrl` unit tests — **23/0**

## Shipped

- `8b8cc2a fix(app): speak the commentary through the server, not from the browser`
  pushed to `origin/dev`. Also carries the `commentaryWatch` `instructions` payload
  the deployed panel already sends, which had been left uncommitted.
- Deploy `1.1.20260930093403`, pid 1834987. Live: LAN host 200 → 15,984 B MP3;
  `169.254.169.254` 400; `127.0.0.1:8880` 400; `:99999` 400; blank input 400.
- Served bundle `assets/index-C4u7B0HX.js`: `[audio]` **0**, `credentials:"include"`
  **1**, `commentary/speech` **1**.

## Deliberately left alone

- `packages/opencode/src/session/commentary.ts` + `test/session/commentary.test.ts`
  — commentary table retention pruning, another session's in-flight work.
- The provider / model-context-size files — same.
- `packages/opencode/config.json` — a `test:httpapi --mode auth` artifact (FU-112);
  deleted, since it regenerates.

## Still open

- **A human ear.** The audio chain is proven to `ended: true` with valid MP3 bytes,
  but "did it sound right" is the user's call. FU-123 stays open for that.

## Lesson

Six independent causes stacked behind one symptom, and five of them were mine. A
browser test that reports "no request happened" is a statement about the harness
before it is a statement about the code. Capture the credential the app really
uses, check what the page really rendered, and read the server log before blaming
the feature.
