# FE-002 — Overnight Operating Cycle

**Owner:** p002 (engine) · **Status:** DESIGNED (s002) — not built
**Goal:** the user-side usage contract: hand-off → clarify → kickoff → autonomous overnight run on
one GitHub repo with shared board + idle researcher → morning report → loop until requirement reached.

## Requirement (verbatim user-specified flow)
Before sleep the user gives a piece of work + target feature or workflow. The engine understands it
and exchanges questions; the user answers; when both judge the picture "good", the engine starts work.
Multiple agents work in the same GitHub project: planning, deploying, discussing on the common board,
raising issues and other agents solving them; idle agents search/research the internet to push the
project closer to the requirement. This recurs until the user requirement is reached.

## Behaviours
1. **Intake / hand-off** (`handoff`): user message → epic issue in target repo
   (`[epic] <target feature>`), tagged `engine/epic`, milestone = cycle number.
2. **Interview** (`clarify`): engine posts ≤`max_question_rounds` rounds of questions to the epic
   issue (one answered round at a time), incorporating answers; stops when:
   - engine marks plan "good" (has requirements + acceptance criteria + task list) AND
   - user comments "good" (or edits/refuses → new round). Transcript → `ENGINE_STATE/runs/<id>/interview.md`.
3. **Kickoff** (`run`): fires only after "good" when `kickoff: confirm`. Runs the FE-001 pipeline,
   plus:
   - **self-raised issues**: any agent may post a work/spec question as a labelled child issue;
     the driver triages it to an idle engineer (issue → claim comment → solve → PR linking the child issue).
   - **shared board**: all milestones, decisions, and open questions live as issue/PR comments;
     the morning report is posted to the epic issue.
   - **researcher**: an idle subagent polls every `idle_poll_minutes`; scans the web for the epic's
     subject, posts findings as board comments/issues (`engine/finding`), referenced by assembler.
4. **Morning checkpoint** (`report`): at `night_cycle.duration_hours`, post summary (done / paused /
   decisions / next questions) and save `ENGINE_STATE/reports/<cycle>.md`.
5. **Recurrence** (`cycle N+1`): if `loop_until_accepted` and user's morning review != "requirement
   reached", re-prime requirements from the review comment and continue on the same repo.

## Gates
- Interview satisfied (plan "good" by both) affects `kickoff`.
- `duration_hours` hard-cap per cycle (bounded cost overnight).
- Morning report is always posted (user expects to review when waking).

## Acceptance (MVP night-cycle)
- [ ] `driver.py handoff --work "…" --feature "…"` creates epic + starts interview.
- [ ] Interview loop terminates with user "good"; transcript recorded.
- [ ] Overnight run completes FE-001 pipeline + ≥1 agent-raised child issue solved + ≥1 researcher
      finding posted; nothing runs before "good" when `kickoff: confirm`.
- [ ] Morning report on epic issue + on disk; cycle delta metrics recorded.
- [ ] Cycle N+1 resumes same repo from the morning review; loop ends on "requirement reached".

## Notes
- Single-user, single-repo first. Board = GitHub issue/PR comments (no separate project tool).
- Researcher content comes from the `web-research` skill (SearXNG/Serper), so findings are real URLs.
