# p002 — The Self* Development Engine ("self-test / self-think / self-complete")

**Project:** a self-hostable **software-development engine**: multiple agents, each playing a
different product-development role (assembler, engineer, QA, reviewer, retro, **researcher**),
operating **through a GitHub repo** (issues → branches → PRs = self-accessing GitHub), with a built-in
**self-testing loop** (write + run tests to green) and a **self-improvement loop** (retrospective
agent rewrites the engine's own role briefs/evals from run outcomes).
**Status:** 🟡 DESIGNED — design doc + operating model written (s002); no code yet.
**Bible:** `40-knowledge/multi-agent-sdlc-engine-research.md` (landscape + prior art) ·
`40-knowledge/opencode-server-api.md` (driving opencode agents).
**Why first:** the final IDE (p001) is huge; this engine is the smallest thing that proves the
core loop — *machines that plan, build, verify, and get themselves better* — before building UI.

## Operating model — the overnight cycle (user-side, the primary usage)

```
                            ┌────────────── NIGHT-CYCLE (L4) ──────────────┐
   before sleep             │                    overnight                 │     morning
 USER hands off:            │   ┌─────────────────────────▼────────────┐   │
 "piece of work: X"         │   │  1 REQUIREMENTS-PRIME               │   │
 + target feature/workflow │   │  engine asks questions ↭ user answers│   │
                            │   │  (loop until BOTH say "good")   ────┼───┐
        ┌───────────────────┼───┼─────────────────────────────────────┼───┴─►
        │ user records async  │   └────────────────────────────────────┘  morning
        │ (chat thread / issue checks, next morning)
        ▼                        │  2 KICKOFF (user confirmed plan)       │
   idle during the run          │      │                                  │
        ▲                        │  3 MULTI-AGENT RUN on one GitHub repo  │
   morning report ────────────► │  · planning (assembler)                 │
   user review: still "good"?   │  · agents RAISE issues, other agents    │
   yes → REQUIREMENT-REACHED ✓  │    claim & solve them                   │
   no  → re-prime requirement   │  · discussion on the SHARED BOARD       │
   and continue the SAME repo   │    (issue/PR comments)                  │
        └────────────────  L4-loop  ─────────────────────────────────────┘
```

**Night-cycle rules**
- **Hand-off:** user posts a piece of work + the target feature/workflow (any channel; the engine
  files it as the epic issue in the target repo).
- **Requirements-prime (interview):** the engine asks *specific* clarifying questions, one round at a
  time, until user and engine both call the plan "good" (measured: plan has requirements, acceptance
  criteria, and a task list the user confirms or edits). This is the p002 "question-exchange" gate.
- **Kickoff:** on confirmation the engine runs unattended through the night. Optional `confirm_kickoff`
  gate (default on) — nothing autonomous before the user's "good".
- **Multi-agent run on the same project/repo:** assembler plans; engineers build; QA tests; reviewer
  gates; deployers ship — and **agents open their own issues with other agents solving them**, all
  discussion logged on the **shared board** (issue threads + PR comments = the project's common board).
- **Idle research (L4 foreground):** a **researcher** agent is always active — scans the web for the
  subject area and feeds the board back toward the user requirement (new findings, better libraries,
  risks). Its output lands as issues/PR comments the other agents consume.
- **Morning checkpoint:** the engine posts a summary (done / paused / decisions / questions). User says
  keep → refine → continue on the same repo; or accepts → **requirement reached** and the cycle closes.
- **Recurring loop:** each overnight cycle resumes the same repo, re-primes requirements, and runs
  again — until user calls done.

## Core loop (per issue — the engine's heartbeat)

```
        EPIC ISSUE (from hand-off) / CHILD ISSUE (raised by agents)
              │ 1. think
        ASSEMBLER (product+architect) ——→ ENGINE_PLAN/<run-id>/PRD + design + task breakdown
              │ 2. approve (gate: plan-review, human or auto)
        ENGINEER(s) (per task, parallel subagents) ——→ code on branch  engine/<run-id>
              │ 3. test
        QA agent ——→ writes/extends tests, runs suite, patches until green (≤N iters)
              │ 4. review
        REVIEWER ——→ diff vs base, plan-compliance check → approve / request changes
              │ 5. complete
        release: merge branch, link PR↔issue, close issue (DEPLOYER ships if deployable)
              │ 6. improve
        RETRO ——→ LESSONS.md + rewrite role briefs/evals (itself PR'd, gated)
              └──────────────────────── recurse / next child issue / next night
```

Each phase writes artifacts into the repo (issue comments / `ENGINE_STATE/`), so GitHub is both
the machine's **workspace**, its **shared discussion board**, and its **audit trail** —
"self-accessing GitHub".

## Attention principle (think→think→complete→test→review)

- **Think twice**: Assembler emits requirements + design + task list before any code. Autonomous
  now; `plan-gate` config toggles human approval later (ties to p001 approval UX).
- **Complete small**: Engineer fanned out per task, each with its own context (prevents the
  cascade-hallucination failure MetaGPT identified in naive linear chaining).
- **Test to prove**: QA is a *first-class gate*, not an afterthought — writes tests, runs them.
- **Retro always**: every run records outcome; `lessons` feed back into prompts.
- **Improvement is PR'd, never naked**: prompt/tool edits go through the same review path.

## Architecture & build matrix

| Piece | Choice (MVP) | Rationale / rejected alternatives |
|---|---|---|
| Agent runtime | **opencode** (CLI role sessions + subagents / server API) | Our existing stack; roles = subagents with custom briefs; server later enables parallelism & p001 reuse |
| GitHub access | **`gh` CLI + `git`** | Simple, scriptable, no API key plumbing (key lives in env, per security rules) |
| Orchestrator | bash/cli scripts + state dir `ENGINE_STATE/` | MVP; revisit if state gets complex (→ sqlite/docs like `20-logs`) |
| Self-testing | QA runs the repo's real test runner (`pytest`/`npm test`/…) | Rejected: synthetic test-only evals first round |
| Self-improvement | RETRO → appends `LESSONS.md` + drafts new role-brief text; diff is PR'd | SICA-style source-rewrite deferred (it worked, but riskier); slate: prompt-level improve |
| Requirements gate | engine↭user interview until both say "good"; morning checkpoint report | the "question-exchange" the user asked for; no autonomous kickoff before "good" |
| Idle research | low-frequency web-search agent feeding board issues | keeps looping run aligned to the moving requirement |
| Eval harness (optional MVP2) | small fixed task set in scratch repo | SWE-bench is heavy; a 5-task harness proves the loop |
| Model | whatever `.opencode.json` uses (default) | per-engine config override later |

## Role briefs (`prompts/`) — v1 drafts

| File | Role | Deliverable | Gate |
|---|---|---|---|
| `assembler.md` | Product + architect (+ interview host) | PRD, design, task list, clarifying questions | plan-review / user "good" |
| `engineer.md` | Implementer | code committed on branch | QA green |
| `qa.md` | Tester | tests written, suite green (≤N iters) | suite result |
| `reviewer.md` | Code reviewer | verdict + report | approve |
| `researcher.md` | Idle web research (aligns project → requirement) | research briefs as issues/board comments | consumed by assembly |
| `retro.md` | Meta (self-improvement) | lessons + brief edits | human merge of its PR |

## MVP scope (one night-cycle, scratch repo)

1. Scratch target repo (throwaway). Engine creates it via `gh`.
2. **Cycle 1 (kicked by user):** user hands off "build a tiny todo CLI named `todo`" (+ target
   workflow "install, use, git-init sync"). Engine interviews (≤2 q-rounds) → user says "good" →
   overnight run: assembler→engineer→QA→reviewer→merge; agents raise/solve a child issue; researcher
   posts ≥1 relevant board finding; morning summary appears on the epic issue.
3. **Cycle 2–3 (refine):** user reviews morning summary, tweaks the requirement; engine resumes the
   **same repo**; repeat until user says "requirement reached". Delta (time/iterations per cycle)
   recorded in `ENGINE_STATE/runs/`.
4. Exit criteria (MVP done):
   - night-cycle runs unattended from hand-off → morning report (only gates pause it);
   - clarify interview completed before kickoff and its transcript is in `ENGINE_STATE/runs/<id>/`;
   - `ENGINE_STATE/runs/<id>/` has full artifact trail (plan, diffs, test log, review report);
   - `ENGINE_STATE/LESSONS.md` grows; brief edits go through a PR.

## Out of scope for MVP
- Web/mobile control plane + approvals UX (→ p001 later; engine stays CLI now).
- Multi-repo / multi-engine parallelism; cost meters; distributed runners.
- Editing the *orchestrator's own source* (SICA-style) — only prompts/lessons improve for now.

## Deliverables map

| Path | Meaning |
|---|---|
| `config/` | `engine.yaml.example` (roles, iteration caps, gates) |
| `prompts/` | role briefs (the improvable brain) |
| `scripts/` | orchestrator + guards (SoT) |
| `features/FE-001-core-pipeline/` | spec + status (think→complete→test→review) |
| `features/FE-002-operating-cycle/` | spec + status (overnight cycle, interview, researcher, morning report) |
| `notes/` | feasibility/API notes |
| `sessions/` | per-run working notes |
| `ENGINE_STATE/` | generated run records + lessons (git-ignored) |

## References
- Research + prior art: `40-knowledge/multi-agent-sdlc-engine-research.md`
- opencode server API / subagents: `40-knowledge/opencode-server-api.md`
- Decisions: `40-knowledge/decisions-log.md` (DEC-005)
- Dev loop: `30-runbooks/rb-001-local-dev-loop.md`
