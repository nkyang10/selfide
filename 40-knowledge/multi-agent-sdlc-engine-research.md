# Multi-Agent SDLC "Engine" — Research for the Self-* Prototype

> Compiled 2026-09-07 (session s002). Goal: land the design of a prototype **self-testing /
> self-thinking / self-completing software development engine** — a system in which multiple
> agents play different product-development roles and which **operates through (self-accesses)
> GitHub** as its workspace/substrate. All claims below are linked; verify before coding.
> Companion docs: `agentic-web-ui-research.md`, `opencode-server-api.md`, `decisions-log.md`.

## 1. What the user's words map to in the state of the art

| Idea | Existing approach | Representative work |
|---|---|---|
| **Multiple agents, different product roles** | "Software company" MAS: PM / Architect / PM / Engineer / QA, SOP-driven assembly line | MetaGPT (ICLR'24), ChatDev |
| **Self-accessing GitHub** | Agents driven from Issue → branch → PR → review → merge; GitHub as the coordination + audit substrate | SWE-agent, GitHub Copilot coding/cloud agent, agent mode, Actions |
| **Self-testing** | Agents write/run their own tests; eval-harness-graded verification; agentic verifiers | SICA, Agentic Verifier / Agentic Rubrics, SWE-bench harness |
| **Self-thinking** | Reflection/self-critique, plan-then-execute, workflow autogeneration | Reflexion, AFlow (ICLR'25), Agentic SDLC products |
| **Self-completing** | Autonomous end-to-end resolution of tasks to mergeable PRs | Live-SWE-agent, Devin, OpenHands, copilot coding agent |

## 2. Multi-agent role frameworks ("different roles of product development")

### MetaGPT — the canonical "software company" MAS
- Paper: https://arxiv.org/abs/2308.00352 · Repo: https://github.com/FoundationAgents/MetaGPT
- Five roles: **Product Manager, Architect, Project Manager (planner), Engineer, QA Engineer**.
- Core philosophy: **`Code = SOP(Team)`** — Standardized Operating Procedures are encoded
  into prompts; intermediate artifacts are verified at each stage to cut cascading hallucinations.
- One-line requirement → user stories / competitive analysis / requirements / data structures /
  APIs / code. Productized as **MGX** (mgx.dev, "the world's first AI agent development team").
- Related: **AFlow** (arxiv 2502.12018, ICLR'25 oral): **automatically programs the agent
  *workflow* itself** via Monte Carlo search over operators — workflow-as-program, not hand-written.

### ChatDev
- Insight: https://atoms.dev/insights/chatdev-introduction .. performs development via layered
  role-playing chat (CEO/CTO/programmer/QA), instructor–assistant pairs per stage, verbal
  "discussions" between roles, outputs files + memory.

### Agent-team primitives in coding CLIs (what we can reuse cheaply)
- **Claude Code subagents**: fan-out to isolated sub-agents with own context/tools/roles, then
  merge — the dominant parallelization pattern (≈90% of real parallel agent work). Docs:
  https://code.claude.com/docs/en/sub-agents. Community have already built role-based
  dev workflows on it (e.g. `zhsama/claude-sub-agent`).
- **CrewAI**: framework-level multi-agent (research → implement → test → validate with hand-offs).
- **opencode** itself: has subagents + Task tool (multi-agent fan-out) + server API → we can
  build the engine on *our own* stack (ties into p001's SDK research).

**Takeaway:** role prompting + SOPs + sub-agent fan-out is a solved primitive; the open problem
is the *governance loop* (who verifies what, when) and the *self-improvement loop*.

## 3. Self-accessing GitHub — executing development through the repo

- **SWE-agent** (princeton-nlp, ~2.5k citations): LLM + Agent-Computer Interface turns a **GitHub
  issue into a PR** with file search/build/test feedback loops. Base for mini-swe-agent (the
  common open scaffold).
- **GitHub Copilot cloud agent / coding agent** (GA 2025/2026): assign an issue → agent plans,
  **opens a branch + PR, writes code, runs tests, asks for review**; runs in an **Actions-powered
  environment** with `GitHub/` tools (issues, PRs, files). Docs:
  https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent ·
  https://github.blog/ai-and-ml/github-copilot/assigning-and-completing-issues-with-coding-agent/
- **GitHub agent mode / Workspace**: issue- and PR-aware generation + multi-file editing; Copilot
  Workspace works directly from issues/PRs.
- **GitHub Actions as orchestration substrate**: events (push/PR/comment) → workflows → agents;
  auto AI review bots are a commoditized pattern (Sourcegraph Lighthouse etc.).

**Takeaway:** the "self-accessing GitHub" spine already exists as a pattern: **issue = task depot,
  branch = work unit, PR = deliverable, comment = review channel, Actions = scheduler**. Build the
  engine on top of (or beside) this spine rather than re-inventing it.

## 4. Self-improving / self-testing agents ("self-*" core)

### SICA — A Self-Improving Coding Agent (DeepMind, arXiv 2504.15228)
- An agent **edits its own source/prompts** and gets better: **17% → 53%** on SWE-bench Verified
  (+ LiveCodeBench gains). Data-efficient, **non-gradient learning driven by LLM reflection +
  code updates** (function-level "improvements" discovered on eval failures).
- This is the closest published existence proof of the user's "thinking → completing → improve"
  loop applied to a *coding agent's own operating code*.

### Live-SWE-agent — self-evolve *on the fly* (arXiv 2511.13646, repo OpenAutoCoder/live-swe-agent)
- First **live** agent: extends/revises its **own tool/config/capabilities at runtime** while
  solving an issue. Key insight: **"software agents are themselves software systems"**.
- Results: **79.2% SWE-bench Verified** with Claude Opus 4.5 (beats most proprietary scaffolds);
  45.8% on SWE-Bench Pro. Trivial to run: built on mini-swe-agent via a config.

### Verification & self-test tooling
- **Agentic Rubrics / Agentic Verifier**: an agent inspects the repo, writes a **checklist** for
  the *expected* fix, then execution-free grades the patch (Scale Labs; 54.2% on selective SWE
  tasks) — i.e. *self-testing without needing ground-truth tests*.
- **Eval harnesses** (the "self-test" substrate): SWE-bench (Verified), SWE-bench Pro (Scale),
  LiveCodeBench, terminal-bench. Anthropic's guidance: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents.
- **Survey of agent self-improvement**: https://selfimproving-agent.github.io/ — splits into
  *foundation-model* improvement vs *scaffolding/agent-system* improvement (we target the latter).

## 5. Reference architectures worth stealing

| System | Architecture | Why relevant |
|---|---|---|
| MetaGPT | SOP assembly line, role agents, intermediate verification | Role division + artifact hand-offs |
| Claude Code split-and-merge | Supervisor fans out ≤10 sub-agents, merges | Cheap multi-role parallel execution |
| OpenHands Agent Canvas (+ automation server) | Agent **Server** (REST) + Canvas UI + **automation** (scheduled/event-driven) + GitHub/Linear/Slack | "Engine + control center" separation — matches our IDE direction |
| GitHub Actions + coding agent | Webhook events → environment → agent → PR | GitHub-native scheduling + audit |
| SICA | Self-edit of agent **source** via eval-failure reflection | The improvement loop |
| AFlow | **Workflow** is generated/found by search, not written | Eventually: engine improves its own process |

## 6. Gaps (where the prototype earns its keep)

1. **No OSS system ties the loop together**: role-team (MetaGPT/Crew) + **GitHub-native execution**
   (CP-SWE-agent-ish issue→PR) + **self-improvement driven by the engine's own eval suite**
   (SICA/Agentic-Rubrics style) in one small, self-hostable engine. Most prior art is a single leg.
2. **Improvement of *role prompts / SOPs / workflow* across runs** (not just fixing the code of the
   harness): logging each run's outcome to a lessons file and rewriting agent briefs = cheap,
   unproven-in-combination.
3. **A governing/UX control plane** for the engine (panics, approvals, cost, watch) — absent from
   CLI-driven agent teams; this is where p001's mobile-multitasking UI plugs in later.

## 7. Sources
- https://arxiv.org/abs/2308.00352 · https://github.com/FoundationAgents/MetaGPT · mgx.dev
- https://atoms.dev/insights/chatdev-introduction
- https://code.claude.com/docs/en/sub-agents
- https://arxiv.org/abs/2504.15228 (SICA) · https://arxiv.org/abs/2511.13646 · https://github.com/OpenAutoCoder/live-swe-agent
- https://labs.scale.com/blog/agentic-rubrics · https://selfimproving-agent.github.io/
- https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent · https://github.blog/ai-and-ml/github-copilot/assigning-and-completing-issues-with-coding-agent-in-github-copilot/
- https://github.com/OpenHands/OpenHands (Agent Canvas)
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
