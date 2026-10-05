# Session s099 — "can we recover a session when the daemon stops?"

User question (asked right after two deploys killed the server this agent runs on):

> "consider the situation a scenerio that when deploy markcode. the server daemon will stop. we cannot
> promise the daemon always on. can we do some recovery action to let original working on session
> continue their work? just some i think of
> - executing command -> report the possible ruin command in last execution ask llm to verify result by
>   another command
> - waiting for llm return -> replay the request to llm again
> - anything else?"

**Status: research + design only. No code touched.** Analysis: `40-knowledge/session-interruption-recovery.md`.

## What the fork actually does today (measured, not assumed)

- Our deploy gives a turn **2 seconds**: `kill` → `sleep 2` → `kill -9`, and the web path has no
  SIGTERM handler (`scripts/deploy-web-4447.sh:46-52`).
- **`SessionStatus` is memory-only** (`session/status.ts:25-34`), so after a restart every session
  reads idle — a killed turn is indistinguishable from a finished one.
- **The interruption signal already exists**: the assistant row persists with `time.completed` unset
  (`core/session/message-updater.ts:33`, `projector.ts:148` treat "assistant && !time.completed" as
  the in-flight message). v1 has `metadata.interrupted` for abandoned tools (`session/prompt.ts:97-99`);
  v2's runner has no equivalent.
- **No boot recovery** anywhere; the fork's own rule says post-crash continuation "requires an
  explicit separate design".
- **The primitive for a continuation already exists**: the durable inbox (`core/session/input.ts`,
  `admit` + `Delivery`), which is what a resume should use — not a request replay.

## Verdict on the user's two ideas

- **(a) verify the possibly-ruined command → correct and highest-value**, provided it says
  *unknown* (never "failed"), verification is read-only and bounded, and destructive tools get a
  pre-execution snapshot so there is something to roll back to.
- **(b) replay the request → right in exactly one case** (no tool had started; pure LLM wait) and
  dangerous otherwise: it re-runs side effects and double-charges. The correct form is
  resume-from-transcript via the durable inbox.

## Added layers the question did not name

Drain-on-shutdown · serve app from disk in dev (**UI-only deploys then kill nothing**) · deploy-when-idle ·
zero-downtime handoff (needs a DB lease/heartbeat, since drains are process-local) · interrupted stamp +
UI honesty · bounded opt-in resume-on-boot + client Resume button · idempotency keys.

**Ordering:** drain → dev-serve-from-disk → interrupted stamp → resume-on-boot → leases → snapshots.
Recovery machinery is a mitigation; not killing sessions is the fix.

## Follow-ups filed

FU-141 drain-on-shutdown · FU-142 serve app from disk in dev · FU-143 interrupted stamp + Resume affordance
