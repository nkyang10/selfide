# Session s002 — Multi-Agent SDLC "Engine" Prototype Research

- **Started (UTC):** 2026-09-07
- **Trigger:** user asked to prototype a "self-test-thinking-completing software development engine" — multi-agent product-development roles self-accessing GitHub; wants research first.
- **Deliverable:** research + prototype design doc (`40-knowledge/` or `50-projects/p002-*`).
- **Status:** in progress

## Close-out (UTC 2026-09-07)
- Research complete → `40-knowledge/multi-agent-sdlc-engine-research.md`.
- Key finds: MetaGPT (SOP role team), SWE-agent/Copilot coding agent (GitHub issue→PR spine),
  SICA 17→53% (self-editing agent), Live-SWE-agent 79.2% (runtime self-evolve), Agentic Rubrics
  (test-free self-verification). Gap: nobody ties role-team + GitHub-native exec + self-improvement
  in one self-hostable engine → that is the prototype.
- Proposed prototype (pending user OK): opencode-subagents-based role team + gh-cli-driven repo,
  eval loop, lessons→prompt self-improvement.
- Follow-ups added: FU-007 (go-ahead + target repo), FU-008 (model/evals choice).

## p002 scaffold (after user answers)
- User: design-doc-first + fresh scratch repo as first target.
- Created `50-projects/p002-selfdev-engine/` with design README, FE-001 spec/status,
  config example, prompt placeholders. Renamed template scaffold p002-TEMPLATE→p000-TEMPLATE.
- DEC-005 recorded. Session s002 close-out pending final summary (see current-state.md addendum).

## Operating-model update (user usage feedback)
- User described the real usage: hand off before sleep, question-exchange interview till "good",
  multi-agent overnight run on one GitHub repo (board/discussions, issues raised+solved by agents,
  idle internet researchers), morning checkpoint, recur until requirement reached.
- Folded into p002: new "Operating model — the overnight cycle" section, FE-002 spec/status,
  researcher role brief, engine.yaml daily-cycle keys, DEC-006. s002 fully closed (research + design).

## Engine build + GitHub live (late s002)
- User: cloud-pos-system = playground for test cases only; engine must be generic for any project.
- Built p002 MVP: driver + github_api + 6 role prompts + config + rb-002 runbook. Dry-run validated.
- GitHub: created/used nkyang10/selfide (mirror of this control center, pushed) and
  nkyang10/cloud-pos-system (playground). DEC-007. FU-012..014 recorded.
- s002 fully closed: research → design → MVP code (dry-validated).

## Parallel-ready (late s002)
- Engineers now run in parallel via per-task `git worktree` branches + batched spawn (max_parallel);
  researcher runs concurrently as a background idle agent during the complete phase.
- Live-verified the opencode role-agent path (real model call, file write): found agents need
  block-style YAML `permission` (inline {} rejected by opencode schema); fixed in AGENT_FRONTMATTER.
- Engine is now ready for a live multi-role (parallel) dev cycle on the playground.

## FIRST LIVE CYCLE SHIPPED (late s002)
- run 20260907-1207 on cloud-pos-system: assembler plan ✓, 4 engineers in parallel ✓, QA 15 tests ✓,
  researcher ✓, reviewer APPROVE ✓, PR #13 merged +1138/-1, morning report posted to epic #12.
- Field fixes: absolute --dir for opencode; flat task branches; REST 5xx retry (DEC-009).
- Ship phase completed manually once (transient GH 500); FU-016 to re-verify driver self-ship.
