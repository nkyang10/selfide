# User Guide — the Self* Development Engine

You speak, it builds. Give the engine a piece of work + the target feature, answer a few questions,
and a small team of agents (assembler, engineers, QA, reviewer, researcher, retro) works on your
project on GitHub overnight. Every step is posted to the repo's issues/PRs so you can wake up to a
morning report instead of a wall of chat.

> Runs from the driver: `50-projects/p002-selfdev-engine/scripts/driver.py`
> Ops runbook: `30-runbooks/rb-002-night-cycle.md` · This guide is the user-facing manual.

## 1. One-time setup (do this once)

**A. Environment (dev-station)**
- Python 3.10+ and `git` are all the engine needs (it is `stdlib`-only).
- The pathe to the opencode binary in `config/engine.json` → `opencode_bin`
  (default `/home/mark/.opencode/bin/opencode`). opencode must have a **working model/provider**
  configured — the agents are opencode agents. Optional: pin a model in the config (`model`).

**B. GitHub token** (used only from the environment, never in files)
```
export GITHUB_TOKEN=github_pat_…
scopes required on the playground/target repo:
  Contents:  read and write   (push the engineering branches)
  Issues:    read and write   (epic + child issues, board comments)
  Pull requests: read and write (PRs + merge)
```
Check it quickly with the engine's own probe:
```
python3 scripts/driver.py probe            # target from config
python3 scripts/driver.py probe --repo other/owner-repo
```
Expect all `PASS`. The probe creates nothing lasting (it self-closes issues and deletes its branch).

**C. Point the engine at your project**
- One-off per run: `--repo owner/name`
- Or make it the default in `config/engine.json` → `target_repo`.
- The repo must exist and have a default branch (`main`).

## 2. The overnight cycle — your actual usage

### Step 1 · Hand off, before sleep
```
python3 scripts/driver.py handoff --work "import stock levels and manage checkout" --feature "stock screen + checkout flow"
```
The engine files the epic issue `[epic] <feature>` on the repo and opens the run record
(`ENGINE_STATE/runs/<run-id>/`). It posts its **clarifying questions** on the issue (the board).

### Step 2 · The question-exchange (until BOTH say GOOD)
Answer on the board, then tell the engine:
```
python3 scripts/driver.py clarify --run <run-id> --answer "Python, no auth, happy path only"
```
Repeat per round (default max 2). If you're already confident, skip the Q&A and mark the plan good:
```
python3 scripts/driver.py clarify --run <run-id> --good
```
Nothing autonomous happens before the plan is GOOD.

### Step 3 · Kick off — leave it running overnight
```
python3 scripts/driver.py run --run <run-id> --cycle 1
```
What happens (all visible on the repo):
| Phase | Role agent | Visible artifact |
|---|---|---|
| plan | Assembler | `ENGINE_PLAN/<run-id>/{PRD,design,tasks}.md` on branch `engine/<run-id>` |
| implement | Engineers (parallel, 1 worktree-task each) | commits per task on `engine/<run-id>` |
| research | Researcher (idle, in parallel) | findings posted on the issue |
| test | QA | tests added/run to green |
| review | Reviewer | `review.md` verdict — `REQUEST_CHANGES` blocks the auto-merge |
| ship | driver | PR opened → merged into `main` (see gates below) |

### Step 4 · Morning
```
python3 scripts/driver.py report --run <run-id> --cycle 1
```
The report prints and is posted on the epic issue: what shipped, what decided, what's next.
- Requirement met? Close the epic. **Done.**
- Not yet? Answer/refine on the board, then `run --cycle 2` on the SAME repo — the loop keeps
  converging until you say it's reached.

### One-shot convenience
```
python3 scripts/driver.py cycle --work "..." --feature "..."   # handoff + auto-answer + run cycle1 + report
```
(`cycle` answer itself with "proceed with sensible defaults" — use it for throwaway/demo runs.)

## 3. Config knobs (`config/engine.json`)

| Key | Default | Meaning |
|---|---|---|
| `target_repo` | `nkyang10/cloud-pos-system` | default repo the engine works on |
| `opencode_bin` | `~/.opencode/bin/opencode` | agent runtime |
| `model` | `""` (opencode default) | pin a model for all roles |
| `engineer.max_parallel` | `2` | engineers running at once |
| `researcher.on` | `true` | idle research during implementation |
| `gates.plan` | `auto` | plan accepted without a human pause |
| `gates.review` | `auto_merge` | merge PR when reviewer approves; `require_human` = never auto-merge |
| `require_mgmt.max_question_rounds` | `2` | interview rounds before auto-plan |

## 4. Safety & expectations

- **Nothing runs before the plan is GOOD** (kickoff gate). Mor over: the reviewer's
  `REQUEST_CHANGES` **blocks the merge** and the PR is left for you (or a re-run).
- Lightweight interview: MVP questions are provided by the engine template; the *real* plan is
  produced by the Assembler during `run` and lives in `ENGINE_PLAN/` in the repo.
- Cost: every phase calls a model. One overnight cycle ≈ 1 (plan) + N (engineers) + 1 (QA) + 1
  (review) + 1 (research) agent runs. Keep `tasks.md` small (≤5 tasks) to stay cheap.
- Network: github.com can be flaky; the engine retries git ops. If a cycle dies, re-run it.
- The token lives in the environment only — **never paste it into files or the repo.**
- A playground repo is advised (`cloud-pos-system`) while you get used to it.

## 5. Troubleshooting

| Symptom | What to do |
|---|---|
| `probe` shows FAIL on PR/comment/issue | token missing `Issues`/`Pull requests` read & write → fix in GitHub, re-probe |
| engine chokes on an empty repo | ensure the repo has a default branch (`main`) with at least one commit |
| run dies mid-phase | check `ENGINE_STATE/runs/<run-id>/agent-*.log`, fix the trigger, rerun `--cycle N` |
| merge skipped "reviewer requests changes" | read the PR + `review.md`, finish it manually or refine + next cycle |
| `opencode run` errors | opencode binary/model not configured → check `opencode_bin` + opencode provider |
