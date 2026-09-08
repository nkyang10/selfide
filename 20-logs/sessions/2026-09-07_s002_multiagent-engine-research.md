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

## Cycle 2 + pipeline/logging enhancements (late s002)
- Cycle 2 shipped (PR #14 merged): delete-item + qty; Designer emitted NEXT-CYCLE.md (new feedback
  loop live: research+design → next-cycle tasks every cycle).
- Post-cycle enhancements per user: worker-phase logging (workers-*.jsonl/phases-*.jsonl → report),
  pipelined parallel engineers (ThreadPoolExecutor), curl fallback for the create_pr 500 client quirk,
  per_page comment fix. Verified compile + dry-run.
- fields: two manual ship completions so far (transient/curl 500s); next cycle should self-ship via the
  curl fallback.

## Durable-orchestration research (s002, user ask)
- Findings: checkpointing ≠ durable execution (Diagrid); Temporal = reference for durable agents
  (Approval pattern for human gates, fan-out for tasks); opencode already supports session export/import
  → cheap agent-level resume; GitHub Actions as the free, kill-proof, scheduled durable runner (Copilot
  cloud agent uses it); OpenHands SDK pause/resume + immutable event stream as state source.
- Recommendation to adopt (small→medium): event-sourced `state.json` per run; step-level resume;
  opencode session-resume on crash; then move the engine's execution into a nightly GitHub Actions
  workflow; Temporal deferred.

## Event-sourced resume implemented + validated (s002)
- Per-cycle `state-<n>.json`: each phase persists {status,start,end,note} on completion (idempotent).
- cmd_run: reads state; if a phase is done it's skipped; the first incomplete phase restarts IN PLACE
  (no branch reset, worktrees kept); ship marked merged on skip.
- Live test: seeded all-phases-done → all skip, rc=0, no agents/PRs. GitHub Actions hosting remains the
  documented next step (needs opencode+provider on the runner).

## 30-cycle marathon launched (s002)
- New epic #15 on cloud-pos-system: FULL cloud POS (12 targets incl. multi-station concurrency, realtime
  sync push, QR/barcode scanners, voice AI assistant, HK-tax HTML export, coupons, auth, UX).
- marathon mode built (`--max`, `--start`, `--min-gap`, TARGETS.md gate; designer maintains targets).
- Detached (setsid) run pid 1171474; watching = epic #15 board + /tmp/opencode/marathon.log.
- To note: each cycle ~8-12 model runs; 30 cycles ≈ many hours + significant model cost.

## Marathon relaunches + /pulls 500 flap (s002)
- First marathon attempt stalled: cycles built code but create_pr repeatedly 500 (GitHub flap); manual
  curl + _curl_retry both succeed when GitHub healthy -> confirmed GitHub-side intermittent /pulls 500.
- Also found+fixed parallel-engineer merge-conflict crash (reset index before checkout; -X theirs fallback;
  file-disjoint task scoping) -> the earlier abort.
- Relaunched marathon (pid 1404587) from cycle 1 with: retries/backoff, curl fallback, ship-only resume
  retry (6x, 90s cooldown), zero-gap chaining. Cycles 1-3 content from earlier attempts was NOT merged
  (lost from main) — re-run rebuilds it.
