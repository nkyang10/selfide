# FE-001 — Core Pipeline

**Owner:** p002 (engine) · **Status:** DESIGNED (s002) — not built
**Goal:** ticket → think → complete → test → review → merge → improve, unattended, on a scratch repo.

## Requirement
Driver accepts a ticket text + target repo; runs the role pipeline of README §Core loop; each
phase's artifacts land in the repo (`ENGINE_STATE/` + issue/PR); final state = merged PR with
green tests; RETRO produces lessons + prompt-edit PR.

## Behaviours
1. **Intake**: `engine run --repo <owner/name> --ticket "<text>"`. If ticket is a text, file an
   issue in the repo; if an issue URL, use it. Assign `run-id` (UTC+slug).
2. **Think**: Assembler subagent reads issue + repo tree; writes `ENGINE_PLAN/<run-id>/` (PRD,
   design, tasks) on branch `engine/<run-id>`; opens plan-review PR/comment.
3. **Complete**: per task, Engineer subagent (own context) edits on the same branch; commits are
   conventional (`feat(<task>): …`).
4. **Test**: QA subagent adds/extends tests, runs the registered test command, patches code/tests
   until green (cap `iterations`, default 3). Logs suite output to `ENGINE_STATE/<run-id>/test.log`.
5. **Review**: Reviewer diffs branch vs base, checks plan compliance; outputs verdict + report to
   `ENGINE_STATE/<run-id>/review.md`. `approve|changes`. Changes → back to step 3 (cap 2 rounds).
6. **Complete PR**: open PR (title `[engine/<run-id>] <summary>`, body links issue), merge on
   approve, close issue.
7. **Improve**: RETRO subagent reads run trail → appends `ENGINE_STATE/LESSONS.md`; if it proposes
   brief/prompt edits, they land in a *separate* PR `engine/retro/<run-id>` (human-merge gate).

## Gates (configurable in `engine.yaml`)
- `plan_gate: auto|human` (auto = Assembler plan accepted without pause)
- `review_gate: auto_merge|require_human` (MVP default: auto_merge on approval)
- `qa_iterations: 3`, `review_rounds: 2`

## Out of scope (deferred)
- multi-repo fan-out, cost metering, web UI, orchestrator self-edit.

## Acceptance (MVP)
- [ ] `python scripts/driver.py run --repo … --ticket "todo CLI"` completes unattended.
- [ ] Merged PR + green suite + issue closed in scratch repo (or on repo).
- [ ] Run trail present in `ENGINE_STATE/runs/<run-id>/` (plan, diffs, test log, review).
- [ ] `LESSONS.md` grows; any brief edits appear as a separate PR.
- [ ] Run 3 outcome delta is measurably recorded (completion time / iteration count).

## Notes
- Driver language: start Python (stdlib + `gh`/`git` subprocess + opencode CLI); revisit if we want
  parallelism via opencode server API (lights the p001 integration path).
