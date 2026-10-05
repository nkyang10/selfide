# Session s100 — restart window + interrupted + resume (items 1, 3, 4)

User's spec, in their words: *"do 1 - notify by ajax, countdown in user's webui without server side make
sure the count keep countdown without server reaction, block prompt input box, hold any next action and
perform with rebound (4) after restart"* + **3** and **4**. Confirmed mapping: **1** = drain + countdown
notice · **3** = interrupted stamp + UI honesty · **4** = bounded resume-on-boot. (2 skipped by user.)

Plan: `50-projects/p003-opencode-fork/notes/plan-restart-window-and-resume.md`.

## S1 — DONE, committed `b19f8db`, live-verified

- `packages/opencode/src/server/lifecycle.ts` (new): process-global window `{ deadline, reason }` with
  `arm / disarm / info / remainingMs`. Process-global on purpose — `InstanceState` is keyed per directory
  and would give every project its own answer. **`remainingMs` travels instead of a timestamp** so a
  device with a skewed clock still counts the right seconds (DEC-060's reasoning).
- `GET/POST /global/lifecycle` on the existing global group; POST arms, never stops (the stop stays with
  the caller).
- `cli/cmd/web.ts`: SIGTERM/SIGINT drain. A handler suppresses Node's default exit, so it owns the exit;
  a **second** signal exits at once (a reader pressing Ctrl-C twice, or a deploy that ran out of patience).
- `scripts/deploy-web-4447.sh`: arms the window over HTTP → SIGTERM → waits out the window → SIGKILL only
  as a backstop. **The old `sleep 2` is now the backstop, not the window.**

**Gates:** typecheck 30/30 · `test/server` **332 pass / 2 fail** vs baseline **325 / 2 fail** — the same two
pre-existing failures (`Server.listen … response logs`, `project directories …`), +7 from my file; 8 unit
tests in `test/server/lifecycle.test.ts`. Live on a source instance (:4450, isolated XDG, login gate on):
`{draining:false,…}` → arm 45 s → a 600 s request **does not extend it** → counts down on its own → a 2 s
request **does** take over → SIGTERM logged `draining for 7998ms` and the process **exited at t+10s**.

### The bug only the live run found

The first SIGTERM logged `draining for 0ms` even though an 8 s window had just been armed. Cause:
`arm()` compared `deadline <= target`, which is also true for a window that has **already elapsed** — so an
expired window was never cleared and silently swallowed every later arm. Unit tests passed because each
case started from a clean module. Fix: only an **open** window (`deadline > now`) can block a longer
request; an expired one stays visible as `draining` (this process really is still up and still meant to
stop — unblocking input now and dying a second later is the worse lie) but no longer blocks. Regression
test pins it. **FU-133 again, from the other side: the unit suite was green and the feature was broken.**

## S2 / S3 — not started

S2 = client context: poll the window, **client-side** countdown from `Date.now()`, blocked composer, held
submits flushed on reconnect. S3 = interrupted derivation (no migration: tail assistant without
`time.completed` while the session is not busy) + marker + Resume button + one-shot resume endpoint.

**Not deployed yet, deliberately:** with no client half the window is invisible, so deploying S1 alone
buys nothing a reader can see.

## Follow-up fixes from the self-review (user: "協助修正" the known gaps)

Both recorded gaps from the review are now closed — commit **`8dcc25c`** (pushed).

1. **`opencode serve` now drains too.** The handler moved into
   `ServerLifecycle.installSignalDrain(label)` (module-level `installed` guard), called in **both**
   `web.ts` and `serve.ts` — a headless server is the one most likely to be killed by tooling.

2. **The drain now ends when the last turn finishes, not when the window elapses.** New
   `packages/opencode/src/session/active-turns.ts` — a process-global counter with
   `begin/end/active`. Hook: **`SessionPrompt.loop`** (`prompt.ts`) — the v1 loop is the live prompt
   path for the web UI (the HTTP handler uses `SessionPrompt.Service`; `SessionV2.prompt` is only
   reached from `control-plane.ts`), and the v2 `SessionExecution.active` set would have counted
   nothing. `Effect.suspend` + `Effect.ensuring` around `ensureRunning` means:
   - **joined waiters hold a slot** — a second `prompt()` onto a running turn keeps the count up
     until that awaiter is satisfied (the safer lie for a drain);
   - success, failure and interruption all release;
   - `end()` clamps at zero, so a stray finalizer cannot produce "-1 turns".
   The drain tick (500 ms) exits as soon as `remainingMs() == 0 || activeTurns == 0`, and logs which
   of the two happened. `GET /global/lifecycle` now carries `activeTurns` — **the first live run
   after wiring showed the field silently stripped**: I had added it to `Info` but not to the
   `GlobalLifecycle` response schema, and `Schema.Struct` drops undeclared fields on encode. Fixed,
   re-proven: `{"draining":false,…,"activeTurns":0}`.

**Live proofs** (source instance, isolated XDG): idle server + 60 s window armed + SIGTERM →
**"drain complete — exiting" at t+2 s** (was: full 60 s); autostart path still drains; second signal
still exits immediately. `test/server` **339 pass / 2 fail** — the same two pre-existing failures
(lifecycle tests now 9, covering the counter including the negative clamp).

**Known limits, deliberate:** a standalone `SessionPrompt.shell` is not counted (deadline covers it);
the busy-path live check (turn in flight → drain waits) still rides on S3's live check because it
needs a real provider turn; the counter is per-process, which is exactly the unit a drain owns.

## S2 — DONE, committed `218a2a6`, pushed

- **`context/restart-state.ts`** (pure, unit-tested): the phase machine. A failed poll is
  `reconnecting` (a daemon that died without draining must not look idle); **404 is `idle`** (an old
  server can never announce a window — holding forever would make the feature worse than nothing); a
  500 is an outage, not an old server. `deadlineFrom` stamps the client's clock with the reported
  duration, so a skewed phone counts the right seconds.
- **`context/restart.tsx`**: polls the **active connection's** `/global/lifecycle` every 5 s (Basic
  auth when the stored connection has a password; same-origin cookies otherwise), stamps
  `deadlineLocal = Date.now() + remainingMs`, and ticks the countdown locally every 250 ms —
  **no server round-trips after the stamp**.
- **`components/restart-banner.tsx`**: bottom-center pill (ProviderTip's corner — collides with
  nothing), countdown during `draining`, `app.server.retrying` during `reconnecting`;
  `pointer-events-none` wrapper so it shields nothing.
- **`prompt-input/submit.ts`**: the shared submit factory blocks during `blocking()` — the text
  **stays in the editor** (never captured away), a toast says so, and an `owedSubmit` flag re-fires
  `handleSubmit` when the phase returns to idle. An editor emptied while held is a cancelled prompt.
  One hook covers every composer (session + drafts) since all go through `createPromptSubmit`.
- **i18n**: `restart.window.countdown` / `restart.held.title` / `restart.held.description` added to
  en + all 62 locale files (real zh/zht translations; English placeholders elsewhere — the FU-116/131/138
  debt class). Parity test green.
- **Mount**: `RestartProvider` + `RestartBanner` in `SharedProviders` — inside `ServerProvider`, so
  `useServer().current` resolves, and shared by both layouts.

**Gates:** typecheck clean · restart-state 7/7 · parity green · `test:unit` **851 pass / 8 fail — all
8 in `submit.test.ts`, which fails identically on a stashed tree**: a pre-existing
`Export named 'use' not found in solid-js/web server build` breakage that `--only-failures` had been
masking (the flag skips previously-passing files, so nobody re-ran this one). My restart mock in that
test is correct for when it gets fixed; the underlying import-chain breakage is **FU-144**.

**Not yet live-verified in a browser** (FU-133): the countdown has never been watched. First chance:
the next deploy — the deploy script arms the window over HTTP, so the banner should appear on every
connected client before the kill.

## S3 — DONE, committed `d3f9645`, pushed

**Server** — `POST /session/{id}/resume` (httpapi session group + handler):
- refuses `busy` (SessionStatus not idle) and `nothing-to-resume` (no incomplete tail assistant);
- derivation = `MessageV2.latest(page({limit:10}))`'s assistant with `!time.completed` — the newest
  10 messages suffice, no full-history scan;
- admits the continuation via the same fire-and-fork path as `prompt_async`, with the interrupted
  turn's own `agent` + `providerID/modelID`;
- continuation text is LLM-facing English, **not i18n**, and says exactly what the recorded analysis
  demands: the effect of started tool calls is *unknown*, verify read-only first, then finish, do not
  redo done work;
- **one-shot with no extra state**: the admitted continuation is a newer message than the incomplete
  assistant, so the derivation stops being true the moment it lands.

**SDK regenerated** (`packages/sdk/js` script/build.ts — the earlier "no drift" check ran against
`packages/client`, the wrong package: the v2 SDK **is** generated from the httpapi groups). Both
`global.lifecycle` and `session.resume` are now typed; `packages/client` (legacy protocol) unchanged.

**Client** — derived, no migration, no boot scan:
- `rows.ts`: a `TurnDivider{label:"cut-off"}` row when the turn is active, the session idle
  (`!inFlight`), and the turn's **last** assistant has `!time.completed && !error`. A graceful abort
  carries an error and stays with the existing "interrupted" divider; during a live turn the tail
  assistant is also incomplete, which is why the idle condition is load-bearing.
- `message-timeline.tsx`: the divider renders `SessionInterrupted` — accent dot, "Interrupted — the
  server restarted mid-turn", and a **Resume** button calling
  `sdk().client.session.resume({ sessionID })` (the raw v2 dir-scoped client; the compat layer's
  `ServerApi` is the legacy client and has no resume). Marker vanishes reactively: status flips busy
  on admission, and the derivation is false once the continuation lands.
- i18n: `ui.message.cutOff` + `ui.message.cutOff.action` in the **ui** domain (the key lives in
  `packages/ui/src/i18n`, not the app's) — en + 62 locales, real zh/zht.

**Gates:** typecheck 30/30 · rows-current **11/11** (4 new: marks the last idle turn, marks nothing
while busy/retry, marks nothing completed, marks only the last turn) · parity green · restart-state
7/7 · `test/server` re-run **339/2** same-as-baseline.

**Not live-verified yet (FU-133):** the happy path needs a real provider turn. The natural check:
the next deploy interrupts this very session's turn — the marker + Resume should appear on it, and
clicking it should continue the work. That is the validation plan.

## Code review of the whole feature (user: "do a code review")

Read every file again with fresh eyes. **Four findings; one of them is the most valuable thing this
session produced**, and it came from re-reading the *server's* message-creation order rather than my
own code.

### 1. FIXED — a prompt whose assistant never started was silently swallowed (`fb4d94e`)

`prompt.ts:1217` writes the assistant message **before** the model call (and
`finalizeInterruptedAssistant` finalizes it on interrupt), so a stop during a slow completion leaves
the "incomplete assistant" shape my derivation read. But the gap **before** that row — persisting the
user message, then compaction / system prompt / history — is a second shape: a transcript ending in a
user message with **no assistant at all**. Nothing marked it, and the endpoint answered
`nothing-to-resume`, so the prompt just sat there forever.

Both sides now read it: the endpoint treats "newest message overall is a user message with no
assistant after it" as resumable (borrowing agent + model from the **user** message, which carries
both), and the row derivation marks it. Verified `noReply` — the only other way to get a user message
with no assistant — **has no callers**, so the shape has exactly one meaning.

**A test that encoded the old behaviour had to be corrected, which is the point of the review:** the
existing "shows the progress row for a submitted turn the server has not acknowledged" asserted
`rows("idle") === ["UserMessage"]` for a user-only turn — i.e. it *pinned* the swallowed prompt as
correct. It now expects the divider, with the reason in the test.

### 2. FIXED — `Effect.orDie` on a documented error path

`MessageV2.page` fails with `NotFoundError` when the session row is gone; `orDie` turned that into a
**defect**, i.e. a 500 crash instead of the endpoint's declared 404. Now mapped to the existing
`notFound(...)` helper.

### 3. RECORDED, not fixed — the busy check is not atomic, and status is per-process

The endpoint reads in-memory `SessionStatus` and then admits the continuation. Between the two, a
second tab can submit a real prompt, and the continuation then **steers** into that turn (the user
sees two prompts, one of them the synthetic "the server restarted" text). Also inherited from the
fork's process-local design: if the desktop sidecar and the web server both run, a session busy in
the *other* process reads `idle` here. Both are bounded (steer, not a second turn; the marker still
clears) and the honest fix is a DB lease — FU-145, deliberately not built in this session.

### 4. VERIFIED SAFE — the double `capture()` in the resubmit path

The resubmit effect checks emptiness with `prompt.capture()` and then `handleSubmit` captures again.
`capture: () => value` (`context/prompt-state.ts:235`) is a pure snapshot accessor, so calling it twice
cannot double-consume the editor. Checked rather than assumed.

**Gates after the fixes:** typecheck 30/30 · rows-current **12/12** (one new never-started case, one
corrected expectation) · restart-state 7/7 · parity green · `test/server` 338/2 — the same two
pre-existing failures.

## Self-review verdict (user: "do u agree the fixes just now?")

Honest answer recorded: **fix 2 agreed unreservedly; fix 1 agreed in direction but I had
under-weighted two things, now corrected (`da48bae`)**:

1. **The multi-device flash.** Phone + desktop on one session (the s097 pattern): a just-submitted
   prompt is assistant-less on the *other* device for the beat between its write and the first status
   event — the marker would offer Resume on a turn that is about to start. Fix: the never-started
   shape now requires **staleness** (`> 30 s`, `Timeline.neverStartedStaleMs`); an honest gap cannot
   be that old, and a crash's aftermath always is. The incomplete-assistant shape keeps **no**
   threshold — the row's existence proves the turn ran and died. Accepted cost: a tab left quiet
   never re-derives, so its marker waits for the next sync event. The stamp is the server's clock, so
   the threshold absorbs skew.
2. **The continuation text was wrong for the never-started shape.** "your previous turn was cut off"
   — there *was* no turn. Now: "the previous turn was cut off **or the last prompt was never
   processed** … complete the last user request" (the model still sees the original prompt above it).

**And the review of the review caught its own bug:** my first cut-off condition used `||` with a
non-null-asserted `lastAssistant` on both sides — `assistantMessages.length === 0` crashed on the
right side. TypeScript could not catch it (the assertion silenced it); only the new test did.
Restructured to a ternary.

**Gates:** typecheck 30/30 · rows-current **13/13** (new: a one-second-old never-started turn is not
marked) · `test/server` 338/2 same-as-baseline.
