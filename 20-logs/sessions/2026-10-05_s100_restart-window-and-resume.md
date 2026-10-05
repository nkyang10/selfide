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
