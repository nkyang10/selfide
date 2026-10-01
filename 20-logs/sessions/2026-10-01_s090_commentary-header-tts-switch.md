# s090 — Commentary: re-confirmed no blocking, TTS switch moved into the panel title, entry count removed

Session opened 2026-10-01 01:35 UTC · **code complete, gates green, NOT built, NOT deployed** ·
branch `dev` at `204b53f` in `50-projects/p003-opencode-fork/opencode`

Three items, asked together: (1) re-confirm the narration never blocks the agent's own work,
(2) move the spoken-commentary on/off switch into the commentary panel title, next to the title,
(3) remove the number next to the commentary panel title.

---

## 1. Is the narration blocking the agent? Re-confirmed — no, in code and live

The worry is real in the abstract: both are LLM calls on the same session. The answer is that
they never touch the same piece of machinery.

**The agent's turn is serialized by `SessionRunState`, and the narration never goes near it.**
`run-state.ts:52-94` owns one `Runner` per session (`ensureRunning` / `startShell`), and that
runner is the only thing that sets `status` busy/idle (`onBusy` / `onIdle`, `:60-65`). A second
turn arriving while one runs is refused with `Session.BusyError` (`:71-75`). The commentary's
only relationship to any of that is:

- **it reads** `status.get(sessionID)` (`commentary.ts:726`, `:860`) and never writes it — the
  only writers are the runner's `onBusy`/`onIdle`;
- **it calls `llm.stream` directly** (`:746`, `:898`), not `SessionPrompt.loop` — the same
  sibling shape as `SessionPrompt.ensureTitle`, which is the precedent the whole feature was
  built on. A per-session `Runner` guard therefore does not apply to it, so it cannot make a
  prompt fail as busy, and a prompt cannot queue behind it;
- **its own `inFlight` set is scoped to itself** (`:745`, cleared in `Effect.ensuring` `:778`)
  and `specialInFlight` is separate (`:893`, `:925`).

**Both directions, then:**

| Question | Answer | Where |
|---|---|---|
| Does a commentary call delay / reject a prompt? | No — it holds no session lock; the agent's `Runner` never sees it | `run-state.ts:52`, `commentary.ts:746` |
| Does a prompt delay the commentary? | No — the tick is forked, so it never awaits the turn | `commentary.ts:963-964` (`Effect.forkScoped` per tick) |
| Do two watched sessions block each other? | No — the per-session sequential loop was replaced by per-session forks in s084 | same lines |
| Does a slow narration call block the *next* narration for that session? | Yes, by design — bounded at `CALL_TIMEOUT_MS` 120s, and it holds only that session's `inFlight` | `commentary.ts:61`, `:722` |

**And it is confirmed by the running server's own log, on this very session.** `logs/deploy/opencode.log`
(`run=e997c2bd`, session `ses_f0ae08ca6ffeWf3hb8LLojMVNR`):

```
01:41:47.079  stream agent=build       <- the agent's step 5 begins
01:41:48.540  stream agent=commentary  <- narration starts 1.5s later, WHILE build is in flight
01:41:50.442  evaluated permission=read ... src/session/commentary.ts   <- agent's tool ran during it
01:41:50.475  loop step=6
01:41:56.350  loop step=7
01:42:28.556  stream agent=commentary
01:42:48.564  stream agent=commentary
```

The narration call overlapped the agent's step and the loop kept advancing through steps 6 and
7 while it ran. A second session was narrated concurrently at `01:41:28.622`.

**The one shared resource is the provider endpoint, not this codebase** — two concurrent
requests to the same model. On `ocgo`/`dgx` that is unremarkable; on a single-slot local server
it could make both slower, which is a deployment property and not a lock in either path.

**Not blocking, but worth naming:** the tick calls `sessions.messages({ sessionID })`
(`:730`), which pages the **whole** transcript every 10s (`session.ts:828-851`, a
`limit: 50` page loop with no ceiling). On a very long session that is real work every tick.
Not a lock, not a correctness bug, and not in scope here — filed as FU-128.

---

## 2 + 3. The panel title bar

Both edits are in `packages/app/src/pages/session/commentary-panel.tsx`, one component, one
header — which is why they were cheap:

- **the number is gone**, together with the `total` memo that fed it. It existed so a scroll
  truncated at 15 lines would not look like data loss; with the count gone that reasoning is
  a lie in a comment, so the comment on `entries` was rewritten rather than left to rot. What
  actually guarantees "nothing is lost" is that the newest line is always at the bottom.
- **the spoken toggle now sits beside the title**, in the place the count occupied, using the
  same v1 `Switch` the rest of the header's tokens belong to (28×16, fits the `h-9` row).

Design calls worth recording:

- **It reads the same store the audio player reads** (`layout.commentary`), so there is one
  switch and not two that can disagree — same rule as the `audioEnabled` memos in
  `context/layout.tsx:618-620`, which exist precisely so the settings row and the panel cannot
  drift apart. That is why the settings row was **removed** rather than left as a duplicate
  (`settings-v2/general.tsx`), and why the panel is the only place a reader has to look.
- **Still disabled while narration itself is off** (`!commentary.enabled()`) — the exact rule
  the removed row had, because a voice for lines that are never produced is a control lying
  about its effect.
- **No new i18n key.** The switch's accessible name is
  `settings.general.commentary.row.audioEnabled.title` ("Read the commentary aloud"), visually
  hidden. Adding a `session.commentary.audio.*` twin would have meant 62 more locale files and
  a fresh batch of the FU-116 English-placeholder class. Parity test: **5 pass / 0 fail, 979
  assertions**, unchanged.
- **A toggle next to the lines is also the better autoplay answer.** The toggle was already the
  user gesture the browser's autoplay policy wants (FU-122); next to the narration it is a
  gesture the reader makes *while reading*, which is when they decide they want sound.

`settings.general.commentary.row.audioEnabled.description` is now unreferenced — left in place
rather than deleted, because removing a key means 62 locale edits and the row it described may
come back.

---

## Gates

- `packages/app` `bun typecheck` — **clean**
- `packages/app` `bun run test:unit` — **832 pass / 0 fail** (115 files, 3239 assertions)
- `i18n/parity.test.ts` — **5 / 0**, 979 assertions, no key added or removed
- `oxlint` on both files — **0 errors** (1 pre-existing warning in `general.tsx:523`, untouched)

**A gate I ran wrong first, and the correction matters for the next agent:** a bare `bun test`
in `packages/app` gives **748 pass / 9 fail**, and the 9 failures are
`SyntaxError: Export named 'use' not found in solid-js/web/dist/server.js` — an artifact of
running without `--conditions=solid`. The real gate is `bun run test:unit`
(`--conditions=solid --preload ./happydom.ts`), which is **832/0**. Confirmed by stashing the
change and re-running: identical 748/9, so it was never my edit. No drift in the recorded gates.

## Not built, not deployed

Nothing was built or deployed this session. Consequences, stated plainly:

- the moved switch has **never rendered in a browser**;
- s089 is still undeployed with it (`kind` markers, the closing line, the decision line, the
  15-line cap, retention 15) — FU-126;
- the running `:4447` build `1.1.20260930111050` still serves the old header with the count
  and no switch.

## Follow-ups

- **FU-127 (new, agent):** s089 + s090 are one un-deployed stack; one build verifies all of it.
- **FU-128 (new, agent, low):** `sessions.messages()` is paged in full on every 10s tick.

---

## Deploy (same session, after the user's "git push, deploy")

**Pushed `34e0593`** (`204b53f..34e0593` on `origin/dev`). Worth recording the check before it:
`origin` is the fork mirror `nkyang10/opencode` and `origin/dev` was already level with `204b53f`;
the "ahead 94 commits" `git` reports is against **`upstream/dev`** (anomalyco), which is not the push
target and must never be pushed to here.

### The deploy kills this session, so the risky half was verified first

`.web-4447.pid` is **2344370 — this agent's own parent process**. `deploy-web-4447.sh` stops the
listener *before* building, because the running binary **is**
`opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode` and `build.ts` writes to that same
path; overwriting a running executable is ETXTBSY. So a compile error would surface *after* the user's
web UI was already gone, leaving no server and no agent to diagnose it.

Mitigation, taken before anything was stopped: run the bundling step alone, on the live tree, with the
pinned toolchain — **bun 1.3.14** (`~/.cache/opencode-build/bun-1.3.14/bun-linux-aarch64/bun`; the box
is **aarch64**, so the `x64` path does not exist and guessing it wastes a minute):

```
OPENCODE_CHANNEL=mark-dev VITE_APP_VERSION=predeploy bun run --cwd packages/app build
  → ✓ built in 10.92s, dist/assets/index-ieBDksMZ.js  2,807,156 B
  → grep: "commentary-audio-enabled" 1 · "Read the commentary aloud" 1
```

The change is therefore proven to survive the bundler before anything is killed. What remains
unproven until the new server answers is the `bun --compile` step and the restart itself.

### What was launched

`setsid nohup bash -c 'sleep 45; scripts/deploy-web-4447.sh'` → `testing/deploy-4447.log`. The delay
is so this report reaches the user before their listener disappears. **This turn cannot report the
outcome** — the kill lands mid-turn.

### Resume checklist for whoever picks this up

1. `tail -40 50-projects/p003-opencode-fork/testing/deploy-4447.log` — expect `built:` then
   `new server pid=…`.
2. `cat …/testing/.web-4447.pid` and compare with `ss -ltnp | grep 4447`; the version should be
   newer than `1.1.20260930111050`.
3. `GET /` on `:4447` serves a bundle containing `commentary-audio-enabled` — **not** the count, and
   **not** the old header.
4. In the browser: open the commentary panel and **click the switch**, then assert a new line is
   actually *heard*. An `aria-checked` that flips is not proof — the FU-119 lesson.
5. The first real narration on this build will also exercise s089 for the first time: 15 lines, live
   timestamps, the closing line, the decision line and its `kind` markers. FU-126's `[audio]` trace
   and its `console.error`s are still in this build and should come out once the feature is confirmed.

---

## The TTS port: `:8881` is a **different build**, not a moved port

The user asked to test moving the speech port from 8880 to 8881. Two rounds of probing, and the
second round changed the finding — recorded in full in `40-knowledge/tts-service-192-168-1-162.md`.

**The first probe failed and the failure was informative.** 8880 answered (200, 14,832 B, 1.03 s);
8881 **refused**, instantly, three times over 30 s, while the host pinged at 15 ms and 8880/8080/3000
stayed open. "Refused" is not "moved" — a dropped packet times out — so nothing was guessed, and the
service was polled instead. **It came up ~40 s into a 2-minute poll** and answered immediately. So
the outage was a restart in place, which is worth knowing before anyone reads a refusal as a typo.

**Then the contract, which is where the news is.** `GET /v1/audio/voices` on 8881 returns **exactly
one** voice, `canto-tts-nano-v1`, with 17 aliases (`cantonese`, `nova`, `yue`, `default`, `en`, …).
8880 returns **322** Azure voices and 23 aliases. Cross-proved, so it is not a stale catalogue:
`zh-HK-HiuMaanNeural` is **400 on 8881** and **200 on 8880**; `canto-tts-nano-v1` is **200 on 8881**
and **400 on 8880**. 8881's own error body says *"canto-tts publishes exactly one voice"*. The audio
differs too — **64 kbps with an ID3v2.4 tag** against 8880's untagged **48 kbps**, and a 30-word line
came back in **3.78 s** instead of 7.02 s. Same wire contract, different model behind it.

**What that means, and why the config was not edited:** `cantonese` is an alias on **both**, so
`commentary.speech.host` is the only line that has to move — but a config write **disposes every open
instance**, and a voice set to any full Azure name would come back text-only on 8881. That is the
user's call, so it is FU-129 rather than a quiet edit. For the record, a wrong voice **degrades**
rather than breaking: `append` publishes the line first and forks the render, so a 400 leaves the row
without an `audio` hash and the reader still gets the text (`commentary.ts:690-695`).

## Deploy result (found after the restart)

`1.1.20261001015710`, pid **2382304** on `:4447`, from `34e0593`. The bundle pre-check did its job:
the app built in 10.92 s before anything was killed, so the compile was never the risk. What is
still unproven is the switch **in a browser** — FU-127's checklist stands, and the two speaker
portraits differ (64 kbps + ID3 vs 48 kbps bare) if the service is moved later.

---

## Part 2 — the voice picker (the user's follow-up: dropdown beside the switch, both services, immediate)

**Pushed `99ae794`, deployed as `1.1.20261001030331` (pid 2492886 on :4447). Never seen in a browser.**
The user has handed the coding work to another agent, so this part of the record is the handover.

### Why it is a (service, voice) pair — the measurement came first

`:8880` and `:8881` are **two builds of one service**, not one service on two ports (full table in
`40-knowledge/tts-service-192-168-1-162.md`, cross-proved: `zh-HK-HiuMaanNeural` is 200/400 and
`canto-tts-nano-v1` is 400/200 across the two). **Both answer to `cantonese`, with different audio**
(untagged 48 kbps vs 64 kbps + ID3). A dropdown of *names* would therefore have been a trap: pick
`canto-tts-nano-v1`, the server renders on `:8880`, every line comes back **text-only**, and the
panel looks broken. Four places carry the endpoint because of that — the content hash, the store
(one setter), the lease, and the option value. DEC-061.

The trap is also why `hashFor` changed: the voice was in the hash so a voice change invalidates the
store, and the same argument applies one level up. Without the host, `:8880`'s recording is served
for a line `:8881` was asked to speak.

### What shipped

- **Server** — `commentary.speech.hosts` (additive; `host` stays the default), `CommentaryAudio.voices`
  with a tolerant `parseVoices` that reads both wire shapes, `GET …/commentary/voices` returning
  `{default, sources}`, and `voice`/`host` on the lease. `watch()` now takes one preferences object.
- **Client** — `utils/commentary-voices.ts` (the picker's rules, pure, 10 tests), a `SelectV2` in the
  header grouped by endpoint, `layout.commentary.host/voice` undefined until chosen, and the lease
  re-taken on a pick so the **next line** speaks in it.
- **i18n** — 2 keys × 62 locales; the picker's own label reuses the audio row's existing title.

### Choices worth arguing with

- **A dead endpoint is data, not an error.** `{voices: [], error}` and a **tenth** of the cache TTL,
  measured against `:8881` refusing connections for ~90 s. A picker that dropped half its list would
  be indistinguishable from one that has nothing to say.
- **A pick nothing offers is still shown.** If the service drops a voice, the picker does **not**
  silently jump to another; it shows the unresolvable pick. Changing the narration without saying so
  is worse than a stale label.
- **The default pair is sent by the server, not guessed by the client** — it is config.
- **A line already on screen keeps its voice.** "Immediately" means the next line; the audio is
  content-addressed and already stored.

### Gates

`bun turbo typecheck` **30/30** · app **842 pass / 0 fail** (116 files, +10) · opencode commentary trio
**94/0** · `test:httpapi` **236 / 0 / 0 / 0** (+1 scenario; it caught the missing one, as designed) ·
oxlint **0 errors** on all 9 touched files. Full `packages/opencode`: **3720 pass / 8 fail**, and the
**same 8 fail with the change stashed** — pre-existing and environmental, not mine.

Two things a successor should know: `bun run generate` in `packages/client` produces **no diff** for
this route (it is in the httpapi group, not the default protocol API — same as s083's
`/project/{id}/directories`), and `test:httpapi` leaves an **untracked, un-ignored**
`packages/opencode/config.json` behind, which is a trap for the next `git add -A`.

### Handover: what is unverified

Nothing in part 2 has run in a browser. The concrete checks, in the order that catches the most:

1. Open a session, open the commentary panel, and confirm the **switch and the picker** are both in
   the title bar with no entry count. That is part 1's change, still unverified.
2. `GET /session/{id}/commentary/voices` on the live server should return **both** endpoints
   (`hosts` is in the config now) — 323 voices on `:8880`, 1 on `:8881`.
3. Pick a `:8881` voice, then send a prompt: the next line's hash must differ from the same words on
   `:8880`, and `commentary audio render failed` must **not** appear in `testing/web-4447.log`. A
   400 here is the trap DEC-061 describes, and it is the one failure that looks like nothing.
4. The `[audio]` trace and its `console.error`s are still in this build (FU-126).

### Handover note: another agent is already in this tree

The last state check found `packages/opencode/src/session/commentary-audio.ts` and
`packages/opencode/src/session/commentary.ts` modified **after** `99ae794`, and the edits are **not
mine** — both are doc-comment corrections, and one of them repairs a comment my change made false
(`SpeechSettings` said "the client never chooses a host and there is no request field to abuse", which
the picker invalidated). Whoever is doing the coding work now should commit those two files as their
own; I left the working tree exactly as found — not staged, not committed, not reverted — because
taking another agent's in-flight edits is the FU-117 hazard this repo has already been bitten by once.
