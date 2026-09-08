# rb-002 — p002 engine: run a night-cycle on any project (hand-off → morning report)

**Risk:** low-medium (writes to a live GitHub repo: branches, PRs, merges). Default gates
(`review: auto_merge`, `plan: auto`) merge unattended — change them in `config/engine.json`
if you want human gates.

## Prerequisites (once)

1. `pip install` nothing; stdlib only (Python 3.12+, `git`).
   - Local Gitea (default for the
     playground): `source 50-projects/p002-selfdev-engine/scripts/engine-env-gitea.sh` and use
     `--repo mark/cloud-pos-system`. GitHub (fallback): export `GITHUB_TOKEN` instead.
2. Set the token in the environment (never in files): `export GITHUB_TOKEN=...`
   (must have repo write scopes). For public playgrounds keep it minimal.
3. Point the engine at the target repo:
   - per-invocation: `--repo owner/name` (any project), or
   - default: edit `50-projects/p002-selfdev-engine/config/engine.json` → `target_repo`.

## Hand-off (before sleep)

```
cd 50-projects/p002-selfdev-engine
python3 scripts/driver.py handoff --work "<piece of work>" --feature "<target feature/workflow>"
```

- Creates the epic issue `[epic] <feature>` on the repo, opens a state run under
  `ENGINE_STATE/runs/<run-id>/`, and posts the engine's first clarifying questions to the issue
  (the shared board).

## Clarify (question-exchange until BOTH agree it is good)

```
python3 scripts/driver.py clarify --run <run-id> --answer "<your answer>"
```

Repeat rounds (default max 2). When both sides are happy: `... clarify --run <run-id> --good`.
The engine marks the plan GOOD and only then is allowed to kick off.

## Run (autonomous, through the night)

```
python3 scripts/driver.py run --run <run-id> --cycle 1
```

Driver does: clone worktree → branch `engine/<run-id>` → materialize the role agents from
`prompts/*.md` → **think** (Assembler: PRD/design/tasks in `ENGINE_PLAN/<run-id>/`; cycle 2+ reads the
previous `NEXT-CYCLE.md` as input) → **complete** (Engineer per task, in parallel) → **test** (QA to
green) → **review** (Reviewer verdict) → **design** (Designer proposes `NEXT-CYCLE.md` = next cycle's
tasks/refinements, posted on the board) → **complete** (PR opened, merged if `auto_merge` + QA ok +
verdict `APPROVE`) — posting progress notes on the epic issue.

## Morning (report + next cycle)

```
python3 scripts/driver.py report --run <run-id> --cycle <n>     # prints + posts morning report
python3 scripts/driver.py cycle --work ... --feature ...        # convenience: handoff+clarify+run+report
```

- Check the epic issue for the morning report and the run trail under `ENGINE_STATE/runs/<run-id>/`.
- Requirement met? close the epic. Else: `clarify` a refinement, then `run --cycle 2` on the SAME
  repo (design reused; the loop keeps converging until the user says done).

## Notes / failure paths

- Dry-run first, always: add `--dry-run`.
- A failed QA/review gate does NOT merge; fix root cause, re-run the cycle.
- Token is read at run time from the environment only.
