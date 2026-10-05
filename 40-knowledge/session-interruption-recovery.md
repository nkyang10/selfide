# Session interruption & recovery — what survives a daemon stop, and what could

> Written 2026-10-05 (s099) from the user's question, after two deploys in one session killed the
> server this agent was running on. Question: *"when deploy markcode the server daemon will stop …
> can we do some recovery action to let original working on session continue their work?"*

## The question is really two questions

1. **How do we stop killing work?** (deploy hygiene)
2. **Given it died, how does the session pick itself up?** (recovery)

Most of the value is in (1). Everything in (2) is downstream of how often (1) happens.

## What is actually true today (read from the fork, not assumed)

| Fact | Evidence |
|---|---|
| **Our deploy gives a turn ~2 seconds.** `kill` → `sleep 2` → `kill -9`, and there is no SIGTERM handler in the web path. | `scripts/deploy-web-4447.sh:46-52`; no `process.on("SIGTERM")` in `packages/opencode/src/` (only subprocess cleanup, `index.ts:137`) |
| **"Busy" is memory-only.** Every session reads `idle` after a restart, so a dead turn is indistinguishable from a finished one. | `session/status.ts:25-34` — `InstanceState.make(new Map())` |
| **An interrupted turn leaves a precise signal.** The assistant row exists with `time.completed` unset; both the updater and the projector already treat "assistant && !time.completed" as *the in-flight message*. | `core/session/message-updater.ts:33`, `core/session/projector.ts:148` |
| **No boot-time recovery exists.** No scan for unfinished sessions in `SessionExecution`/runner/execution-local; the fork's own rule says post-crash continuation "requires an explicit separate design". | `core/session/execution/local.ts` (only `resume: coordinator.run`, a fiber, not a crash), `core/src/session/runner/index.ts` has no interrupt/orphan handling |
| **A durable input inbox already exists** — the primitive a continuation needs. | `core/session/input.ts` (`admit`, `Delivery` steer/queue, `promoted_seq`) |
| **v1 already has an "abandoned tool" marker; v2 does not.** | `session/prompt.ts:97-99` — `status === "error" && metadata.interrupted === true` |
| **`session/retry.ts` is provider-error retry** (429/5xx/network, backoff, 5 tries). It is *not* crash recovery. | `session/retry.ts:29-34` |

**Net effect today:** the DB keeps the user prompt, the partial assistant text and the tool calls
that started — but nothing anywhere says "this was interrupted", so the UI presents a truncated
reply as if it were the answer and the tab as idle.

## Verdict on the two ideas from the user

### (a) "report the possibly-ruined command, ask the LLM to verify with another command" — **right, and the highest-value idea here**

It is the only one that addresses the actual hazard: a tool that was *running* when the process
died may or may not have taken effect. Three refinements make it honest:

- **Never say "failed".** Say **unknown**. The signal exists (`shell.started` with no completion);
  the recovery prompt lists those calls as *"started, effect unknown — verify before continuing"*.
  A tool that was never reached must not be lumped in.
- **Verification must be read-only first** (`git status`, `ls`, `test -f`), and destructive tools
  need a **pre-execution snapshot** (stash/commit, or an FS snapshot) — otherwise "verify" only
  produces a damage report.
- **Cheap, bounded, one shot.** One verification pass, not a loop.

### (b) "replay the request to the LLM" — **right in exactly one case, dangerous as stated**

Replaying a request whose tool calls already ran **re-runs side effects** and double-charges;
"it timed out" is not evidence the model never acted. The correct primitive is not replay-the-request
but **resume-from-transcript**: admit a new durable input saying *"you were interrupted at step N;
re-check state, then continue"*, so the model re-derives from what is persisted instead of re-executing
something whose outcome is unknown. Replay-the-request is only safe when **no tool had started**
(pure LLM wait) — and even there, continuation is at least as good.

## The layers that were missing from the question

### Layer 0 — do not kill the work (cheapest, biggest effect)

1. **Drain on shutdown.** SIGTERM → stop admitting inputs, let in-flight turns finish (bounded,
   60–120 s), then exit. The deploy script must wait for drain instead of `kill -9` after 2 s.
   Most deploy-kills become non-events.
2. **Serve the app without restarting the daemon — and note the mechanism ALREADY EXISTS.**
   `OPENCODE_WEB_UI` (`packages/opencode/src/server/shared/ui.ts:42-46`, used at `:92-101`)
   makes the server **proxy** UI requests to that URL whenever the embedded UI is absent or
   `OPENCODE_DISABLE_EMBEDDED_WEB_UI` is set. Paired with `packages/app`'s vite dev server
   (`vite.config.ts:24-28`, `0.0.0.0:3000`) that is a full dev mode **with HMR and no daemon
   restart** — so a `packages/app` change cannot kill a working session. There is a test
   (`packages/opencode/test/server/httpapi-ui.test.ts:56-58`) and **no documentation**.
   *Correction worth keeping:* this follow-up was first filed as "build a new serve-`dist/`-from-disk
   path", which was **not needed** — the benefit is available today by flipping two env vars. What is
   missing is only that our `run-web.sh` / `deploy-web-4447.sh` never use it, that nobody has
   **verified it renders in this fork** (a bare DISABLE with nothing behind it serves a 404 — the
   trap the desktop's own notes record), and that app-only deploys still restart the daemon.
   Serving a built `dist/` from disk remains a reasonable *fallback* if the proxy path proves unusable
   (HMR websockets through a proxy are the usual suspect).
3. **Deploy only when idle**, or drain-then-swap: the deploy script can read session status and wait.
4. **Zero-downtime handoff** (new instance on a second port, old one drains, then swap) — needs a
   **DB claim/lease with TTL** per session, because `SessionExecution` is process-global and drains
   are process-local: two processes on one SQLite can double-run a session. That lease is also what
   makes any automatic recovery safe.

### Layer 1 — make the interruption honest

5. **Stamp interrupted turns** using the signal that already exists (`!time.completed`), with v1's
   `metadata.interrupted` as precedent. UI shows "interrupted — the server restarted" + a Resume
   affordance instead of a truncated final-looking answer.
6. **Stop reporting a dead turn as idle** — a durable marker also fixes the sidebar dot, the Thinking
   row and the `MarkCode [x of y]` title, which all read the in-memory status.

### Layer 2 — the recovery action itself

7. **Resume-on-boot, bounded, opt-in per session**: for sessions flagged interrupted, admit one
   continuation input ("you were interrupted; these calls may have partially run — verify, then
   continue"). **Not** for sessions blocked on a permission (that is the user's move, not the agent's —
   same rule DEC-056 uses for the tab counter).
8. **Lease/heartbeat** so resume only fires after the previous owner's claim expired.
9. **Client-side Resume button** rather than auto-spending: DEC-062's lesson (narration defaulting
   off per browser) is the same shape — a recovery that silently spends tokens reads as a bug.

### Layer 3 — repair (idea (a), done properly)

10. Persist "tool started, no result" as **unknown**, and surface it in the continuation prompt.
11. **Pre-execution snapshot** for destructive tools → verification has a rollback.
12. **Idempotency keys** where possible (content-hash writes make re-application a no-op).

### Layer 4 — bounded replay (idea (b), corrected)

13. Replay only from the transcript, and only when no tool had started.
14. Cap with backoff + a circuit breaker; keep provider-error retry (`session/retry.ts`) separate —
    they are different failures and must not share a counter.

## Ordering by value per effort

| Order | Action | Effort |
|---|---|---|
| 1 | drain-on-shutdown + deploy waits for drain | small (script + one handler) |
| 2 | ~~serve app from disk in dev~~ → **SKIPPED by user**; the `OPENCODE_WEB_UI` dev mode already covers it and was judged not worth pursuing | — |
| 3 | interrupted stamp + UI honesty | small |
| 4 | resume-on-boot (bounded) + Resume button | medium |
| 5 | DB lease/heartbeat → enables multi-instance + safe auto-resume | large |
| 6 | pre-exec snapshots, idempotency keys | large, per-tool |

**The honest summary:** recovery machinery is worth building, but it is a *mitigation*, not a fix.
The fix is not killing sessions — which today is a choice our own deploy script makes in two lines.

## Decision log for this design

- **2026-10-05 — FU-142 / layer 0 item 2 SKIPPED by the user** (*"看起來不像能做到, skip"*). The
  existing `OPENCODE_WEB_UI` proxy dev-mode was **not** verified live and no dist-from-disk path will
  be built. **Do not re-propose it.** Consequence accepted: app-only deploys keep restarting the
  daemon, so layer 1 (interrupted stamp) and layer 0 item 1 (drain-on-shutdown) are the only things
  that can still reduce the damage.

## Open questions

- Does the v1 cleanup path (`metadata.interrupted`) get reused, or does v2 need its own marker?
- Should resume be opt-in **per session** (a stored flag) or a global setting?
- Cost ceiling for an auto-resume: the continuation prompt itself spends a model call.