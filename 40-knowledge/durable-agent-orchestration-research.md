# Durable/Overnight Agent Workflow Engineering — Research for p002

> Compiled 2026-09-07 (s002). Trigger: cycle-2 took ~90 min wall-clock though the engine itself ran
> ~15 min — losses came from a killed process and no resume (full redo). Goal: find the better
> process patterns to run multi-agent dev cycles unattended/overnight.

## 1. The core distinction: checkpoints ≠ durable execution
- **Checkpointing** = "I saved your state; you take it from here" — manual/partial resume
  (LangGraph checkpointer, CrewAI, Google ADK).
- **Durable execution** = "Your workflow WILL run to completion" — the runtime replays/retries steps,
  keeps step-level state, idempotency, survives crashes/waits (Temporal et al).
- Source: diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows
- **Verdict for p002:** MVP = do proper *checkpoint/resume* now (step-level, event-sourced); graduate to
  durable execution only if the engine becomes multi-tenant ops.

## 2. Temporal — the durable-execution reference
- https://docs.temporal.io/ai · Workflows resume after crash/timeout/**multi-day human wait**;
  retry failed steps in isolation; resume without reprocessing completed work.
- Patterns that map to our loop: **Approval** (human-in-the-loop as a durable wait — our clarify/plan
  gate), **Entity Workflow** (per-run-id workflow), **fan-out** (per-task workers), **Task Queues**
  (QoS/fairness across models/tenants).
- Cost: new runtime + worker + storage — heavy for a single-user prototype now.

## 3. Coding-agent-native resume (zero new infra)
- opencode **already** has the pieces: session events, `opencode export <sessionID>` / `opencode import`,
  `opencode run --session <id> --continue` (and `--fork`). → a crashed role agent can be RESUMED from
  its exported session instead of retried blind. This is the cheapest lever, on our own stack.
- OpenHands SDK shows the same idea productized: `conversation.pause()/run()` + **convo-persistence**
  + immutable event stream as the state source (docs.openhands.dev/sdk/guides/convo-pause-and-resume).

## 4. GitHub Actions as the durable, free runner (the pragmatic answer)
- Copilot cloud/coding agent is exactly this: "works autonomously in a **GitHub Actions-powered
  environment**" (docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent).
- Benefits for our engine: scheduled nightly (`on: schedule`), re-runnable jobs (`workflow_dispatch`/
  rerun = free "restart from job"), **per-step logs** (better than our jsonl), artifacts/cache for
  `ENGINE_STATE` continuity, runs without the dev-station/laptop online, and no process that a shell
  tool can kill. Runs on GitHub's runners → no machine spin-up.
- Trade-off: runner time limits (public runners ~6h/job) and secrets handling (repo Actions secret).

## 5. Patterns to adopt (ranked, for p002)

| Pattern | What to do | Effort |
|---|---|---|
| **Event-sourced run state** | Already partially there (`trail.md`, `phases-*.jsonl`, `workers-*.jsonl`). Make it the **source of truth**: a `state.json` per run with phase/worker statuses (todo/done/failed/skipped), idempotent updates. | small |
| **Step-level resume** | `run` first reads `state.json`; completed phases are skipped, the first incomplete phase is restarted. Worker tasks stay live per worker. | small |
| **Agent-session resume** | On agent crash, `opencode export <sessionID>` + `run --session --continue` instead of blind retry. | small |
| **Move execution into GitHub Actions** | Nightly workflow runs the driver; ENGINE_STATE cached/artifacts; kill-proof + per-step logs. | medium — recommended next |
| **Human-in-the-loop as durable wait** | Plan/approval gate becomes a "waiting" state that survives restarts (Temporal Approval pattern, simplified). | medium |
| **Temporal / durable runtime** | Only if the engine goes multi-tenant/prod-ops. | high, deferred |

## 6. Sources
- https://docs.temporal.io/ai
- https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows
- https://langchain-ai.github.io/langgraph/concepts/persistence/ (checkpointer; the "checkpoint" pole)
- https://docs.openhands.dev/sdk/guides/convo-pause-and-resume · https://docs.openhands.dev/sdk/arch/events
- https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent · https://github.blog/ai-and-ml/github-copilot/github-copilot-coding-agent-101-getting-started-with-agentic-workflows-on-github/
- https://www.truefoundry.com/blog/multi-agent-orchestration-frameworks (2026 survey)
- https://zylos.ai/research/2026-02-17-durable-execution-ai-agents/ (trade-offs)
