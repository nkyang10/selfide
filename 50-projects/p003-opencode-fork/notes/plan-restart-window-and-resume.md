# Plan — restart window (notice + countdown + hold) and session resume

> s100. The user's request, in their words: *"do 1 - notify by ajax, countdown in user's webui without
> server side make sure the count keep countdown without server reaction, block prompt input box, hold
> any next action and perform with rebound (4) after restart"* + items **3** and **4**.
> Confirmed mapping: **1** = drain + countdown notice · **3** = interrupted stamp + UI honesty ·
> **4** = bounded resume-on-boot. (Item 2 — dev mode — was skipped by the user; FU-142.)
> Analysis this implements: ide `40-knowledge/session-interruption-recovery.md`.

## Why this shape

The measurement that drives it: **our deploy gives a turn 2 seconds** (`deploy-web-4447.sh:46-52` —
`kill` → `sleep 2` → `kill -9`) and the web path has **no SIGTERM handler**, while the CLI entry
`packages/opencode/src/index.ts:135-141` ends with `finally { process.exit() }`. So a deploy is always
a hard kill, and the transcript keeps a half-written assistant message with no completion
(`core/session/message-updater.ts:33`, `projector.ts:148`).

The user chose the *client-visible* half of that fix: tell the reader what is happening, keep the
countdown running with no server, refuse new input, hold what they tried to do, and finish it after
the restart. **Draining is the server half of the same window** — the countdown is the drain made
visible, so the two cannot ship apart.

## D1 — Server: announce a drain, then drain

**State** — a process-global singleton (like `server/webui.ts`): `{ deadline: number | null }`, plus
the announce timestamp. It is a fact about the *process*, not about a directory, so it must **not**
be `InstanceState` (that is keyed per directory and would reset per project).

**Endpoint** — one read, one write, on the existing global group
(`server/routes/instance/httpapi/groups/global.ts`, beside `/global/webui` and `/global/dispose`):

- `GET /global/lifecycle` → `{ draining: boolean, remainingMs: number }`
- `POST /global/lifecycle` `{ timeoutMs }` → arm the window (used by the deploy script and by
  anything else that wants a graceful stop)

`remainingMs` rather than a bare deadline **on purpose**: the client stamps its own local deadline as
`Date.now() + remainingMs`, so a phone with a skewed clock still counts the right number of seconds.
This is the same reasoning as DEC-060 — the number is derived where it is known.

**Signal** — install `process.on("SIGTERM")` in the web command: arm the window if it is not armed,
wait for it to elapse (or for the drain to finish early — see below), then exit. **A SIGTERM handler
suppresses Node's default exit**, so the handler must call `process.exit()` itself; the existing
`finally { process.exit() }` in `index.ts` still covers the normal path.

**Drain completion** — `POST /global/dispose` already exists and disposes every instance. The drain
should end **early** if nothing is running, so the common case (nobody mid-turn) costs ~0 s instead of
the full window. The honest busy signal is the in-memory `SessionStatus.list()` (`session/status.ts:25`)
— process-global in practice, since the web server runs one process. First implementation: log the
busy set at exit so the log tells the truth about what was cut, and use a **fixed window** for the
countdown. A precise busy-wait is a follow-up, not a blocker: the user's requirement is that the
countdown is *visible and honest*, not that it is optimally short.

**Deploy script** — `scripts/deploy-web-4447.sh`: `POST /global/lifecycle {timeoutMs}` → wait for the
window (or for the early-exit) → `SIGTERM` → wait → `SIGKILL` only as a backstop. The 2-second sleep
becomes the *backstop*, not the window.

## D2 — Client: the restart window

**New context** `packages/app/src/context/restart.tsx` (a `createSimpleContext`, matching
`context/tabs.tsx` style):

- poll `GET /global/lifecycle` every 5 s while any tab is open, and immediately on reconnect /
  `visibilitychange` (the app already has that plumbing at `layout.tsx:440`, `server-sdk.tsx:345`)
- on `draining`, stamp `deadlineLocal = Date.now() + remainingMs` and enter the window
- **`remaining()` is computed on the client from `Date.now()`** — a local ticker, no server round-trips.
  This is the user's explicit requirement and the whole reason the window survives the server dying.
- phases: `idle` → `draining` (counting) → `reconnecting` (countdown elapsed, server not answering)
  → back to `idle` when a poll succeeds with `draining: false`

**Blocked input** — the v2 composer refuses to send while the window is open. Copy is minimized by
reuse: `app.server.retrying` exists ("Retrying automatically..."), `settings.general.row.followup.option.queue`
exists ("Queue") — **new keys only if a phrase cannot be expressed with those**, because every new
visible string costs 62 locale files and `i18n/parity.test.ts` (the FU-116/131/138 debt class).

**Held action** — a submit attempted during the window is **queued, not dropped**: the reader's
intent is the thing being protected. On reconnect the queue is flushed as an ordinary prompt (this is
*not* a request replay — see D4).

## D3 — Interrupted turns, honestly (item 3), with **no migration**

The signal already exists: an assistant message with no `time.completed`. Two facts make a stamp
unnecessary:

- during a live turn the tail assistant is *also* incomplete, but the session is **busy**
  (`SessionStatus`, in-memory — and it reads `idle` after a restart, which is exactly the case we care about)
- so **interrupted = tail assistant incomplete AND session not busy**, derived at read time

Consequences: no schema change, no migration, no boot scan — a pure function plus a marker in the
transcript, with unit tests. It also fixes the sidebar dot, the Thinking row and the `MarkCode [x of y]`
title, because all three read the same status that resets on restart. **Today all three show a dead
turn as finished.**

UI: an "interrupted" marker on that message + a **Resume** button.

## D4 — Resume (item 4), bounded and one-shot with no extra state

`POST /session/{id}/resume` admits **one** durable continuation input through the primitive that
already exists (`core/session/input.ts` `admit` + `Delivery`), with text that says what is true:
the server restarted, the last tool calls may have partially run, verify state then continue.

- refuses while the session is busy (someone is already working on it)
- **one-shot for free**: once the continuation is admitted, a user message follows the interrupted
  assistant, the tail is no longer incomplete, and the Resume button disappears. No counter, no column.
- the continuation must **re-derive from the transcript, not replay a provider request** — replaying
  re-runs side effects and double-charges. The user named this ("replay the request"); the recorded
  analysis says it is only safe when no tool had started, and resume-from-transcript is at least as good
  even there.

## Traps this plan is written around

- **A countdown that needs the server is not a countdown.** Hence `Date.now()` on the client, and
  `remainingMs` (not a server deadline) so clock skew cannot shorten or lengthen it.
- **`icon={<Icon …/>}` does not react** (AGENTS.md, FU-135): pass a getter where the prop allows it.
- **A feature that has never been opened is not tested** (FU-133): the live check is part of the
  stages, not an optional extra — arm a window by hand, watch the countdown, kill the server, restart,
  confirm the held prompt was sent and the Resume marker appears.
- **A build compiles the whole checkout**: this work sits in the tree alongside the uncommitted s093
  serper tree, so it ships with it unless that is committed first.
- Port **4447**, login gate on (FE-001), so every manual check needs auth.

## Stages

| Stage | Work | Gate |
|---|---|---|
| S1 | D1 server: state + endpoint + SIGTERM + deploy script | typecheck, opencode tests, live `curl` of the endpoint |
| S2 | D2 client: context, countdown, blocked composer, held queue, flush | typecheck, app tests, **live browser check** |
| S3 | D3 + D4: interrupted derivation + marker + Resume + resume endpoint | typecheck, app + opencode tests, **live browser check** |

## Open questions for the user

1. **Window length** — default 60 s? It must exceed a typical turn's remaining time to be useful, and
   every second of it is a second of not deploying.
2. **Held prompts: auto-send or confirm?** Auto-send spends tokens without a watcher (DEC-062's shape);
   confirming costs one tap.
3. **Resume: manual only, or opt-in auto?** Auto-resume spends a model call per interrupted session.