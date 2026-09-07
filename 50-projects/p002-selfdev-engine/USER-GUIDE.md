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
| plan | Assembler (+ prior `NEXT-CYCLE.md`) | `ENGINE_PLAN/<run-id>/{PRD,design,tasks}.md` on branch `engine/<run-id>` |
| implement | Engineers (pipelined ThreadPool, ≤ `max_parallel` concurrent) | commits per task on `engine/<run-id>`; per-worker log `runs/<id>/workers-<cycle>.jsonl` |
| research | Researcher (idle, in parallel) | findings posted on the issue |
| test | QA | tests added/run to green |
| review | Reviewer | `review.md` verdict — `REQUEST_CHANGES` blocks the auto-merge |
| **design (every cycle)** | Designer (product-design party) | **`ENGINE_PLAN/<run-id>/NEXT-CYCLE.md`** + each proposal mirrored as its own **`[proposal] …` issue** (`engine/proposal` label), linked from the PR |
| ship | driver | PR opened → merged into `main` (see gates below) |

The loop is self-feeding: every cycle the **research party + product-design party** propose the next
cycle's tasks/refinements; the next cycle's Assembler treats `NEXT-CYCLE.md` as its input and plans on
top of it — until you say the requirement is reached.

### Step 4 · Morning
```
python3 scripts/driver.py report --run <run-id> --cycle 1
```
The report prints and is posted on the epic issue: what shipped, what decided, the **research+design
proposals for the next cycle**, and the next question for you.
- Requirement met? Close the epic. **Done.**
- Not yet? Pick/confirm the proposals you want (reply on the board → `clarify --answer "…"`), then
  `run --cycle 2` on the SAME repo — next cycle consumes `NEXT-CYCLE.md` and keeps converging.

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

## Logs & observability
Every cycle writes `ENGINE_STATE/runs/<run-id>/workers-<cycle>.jsonl` (per-worker start/end/exit/commits) and
`phases-<cycle>.jsonl` (assembler/engineers/QA/reviewer/designer/ship timings + results); the morning report
includes the phase summary. Worker failures are also posted to the board.

## 4. Safety & expectations

- **Nothing runs before the plan is GOOD** (kickoff gate). The reviewer's verdict **must be `APPROVE`**
  and **QA must pass** for an auto-merge; else the PR stays open for you. Every agent is exit-checked
  (with one retry); a failing/lost agent aborts or skips **loudly** on the board — never a silent empty cycle.
- Every agent run has a timeout (900–2400s), so nothing idles forever on a stuck model.
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
