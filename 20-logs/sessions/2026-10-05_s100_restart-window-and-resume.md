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
