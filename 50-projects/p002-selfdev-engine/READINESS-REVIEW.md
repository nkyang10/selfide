# Readiness Review — is the engine ready for a user to use?

> Walkthrough of the USER-GUIDE step-by-step against the actual code, after the fixes made in
> session s002 (reviewer-gate enforcement, agent-log routing, cycle-2 re-push, git retries).
> Date: 2026-09-07 · Status legend: ✅ READY · 🟡 READY-with-known-limits · ❌ NOT READY

## Environment setup

| Guide step | Status | Verdict notes |
|---|---|---|
| Python3 + git only | ✅ | driver is stdlib; verified `python3.12` |
| opencode binary + provider/model | 🟡 | `~/.opencode/bin/opencode` found; **agent exec live-verified** with a real model call (smoke: agent wrote a file). Requires user's opencode provider to be configured and funded. |
| Token env + scopes | ✅ | `driver.py probe` on playground = **ALL PASS** (contents, issues, comments, push, PR, delete) after user granted Issues+PRs R&W |
| Point engine at project (`--repo` / config) | ✅ | `target_repo` in config; `--repo` override validated |

## Hand-off → interview → kickoff

| Step | Status | Verdict notes |
|---|---|---|
| `handoff` creates epic issue | ✅ | live-verified path (probe + dry-run); creates `[epic]`, posts questions to board |
| Engine asks clarifying questions | 🟡 | **heuristic template questions** for MVP — not yet Assembler-generated; answers fold into a *stub* plan only |
| `clarify` until both say GOOD | ✅ | rounds + `--good` gate implemented; **nothing runs before GOOD** (enforced in `run`) |
| Plan quality | 🟡 | real plan is produced later by the Assembler inside the repo (`ENGINE_PLAN/<run-id>/`); the interview itself drafts only a stub — acceptable MVP, flagged in guide |
| Kickoff | ✅ | `run` requires `meta.good`; auto-gate `plan: auto` |

## During the run (the actual dev cycle)

| Phase | Status | Verdict notes |
|---|---|---|
| clone + branch `engine/<rid>` | ✅ | with FF re-push fix for cycle 2+ (stale remote branch deleted first) |
| Assembler plan → committed | ✅ | **exit-code checked + 1 retry**; no parseable `tasks.md` → cycle aborts with a board note (no silent empty run) |
| **Engineers in parallel** (≥2 tasks) | ✅ | per-task `git worktree` + branch on a **pipelined ThreadPool (max_parallel)** — no batch stalls; **each agent's exit code and ≥1 commit verified**; worker failures skipped with board notes; per-worker + per-phase JSONL logs |
| Researcher (idle, concurrent) | ✅ | background agent during implementation; findings posted to board |
| QA tests-to-green | 🟡 | driver **runs QA, checks exit, retries once**; if QA fails → **blocks auto-merge**. QA's test files are committed into the PR (previously lost); iteration is the agent's own loop (`qa_iterations` not a driver loop) |
| Review + verdict file | ✅ | reviewer must write `ENGINE_STATE/review.md`; only an explicit `APPROVE` authorizes auto-merge |
| **Reviewer gates merge** | ✅ | merge happens only if gate auto **AND QA ok AND verdict=APPROVE**; `require_human` never merges; missing/unclear verdict leaves PR open |
| Ship: PR + merge | ✅ | PR create/merge permissions live-verified; PR body carries plan/QA/verdict summary |
| Morning report | 🟡 | prints + posts; uses run trail/meta (plan section shows interview plan, not the in-repo assembler plan) |

## Robustness

| Concern | Status | Verdict |
|---|---|---|
| github.com flakiness (443 drops ~130s) | ✅ | git ops retry (3x, backoff); REST unaffected; one live push observed succeeding on retry |
| Agent stdout deadlock (PIPE) | ✅ **fixed now** | agents stream to `ENGINE_STATE/runs/<id>/agent-*.log` instead of an undrained pipe |
| **Lost/vanish role trigger** | ✅ **fixed now** | every agent run is exit-code-checked and retried once; phase artifacts are verified (plan tasks, per-task commits, QA result, APPROVE verdict); failures abort/skip **loudly** with board notes instead of silently continuing |
| **Kill/crash → full redo** | ✅ **fixed now** | event-sourced `state-<cycle>.json` per phase; `run` resumes from the first incomplete phase, keeps branch/worktrees, skips completed phases — live-validated (all-skip, rc=0) |
| **Idle forever / hang** | ✅ **fixed now** | every agent waits with a timeout (900–2400s) and is killed on expiry; REST calls now carry a 45s timeout (previously unbounded → could hang forever); git ops capped 200s/attempt |
| FDs/cleanup | ✅ | stdout handles closed after wait; rogue worktrees removed; probe self-cleans |
| Secrets | ✅ | token only via env; nothing committed (sweep done repeatedly) |

## What is NOT ready / needs user decision

1. **~~Live end-to-end run~~** 🟡 PARTIALLY — first live cycle shipped on the playground (plan → 4 parallel
   engineers → QA → review → PR merged, +1138/−1); the ship phase itself was completed manually after a
   transient GitHub 500 (fix: REST 5xx retry) — re-run needed to prove the driver lands PR+merge unaided.
2. **Interview intelligence** — questions/plan-stub are template-based; Assembler-driven interview is
   designed but not wired (`prompts/assembler.md` covers planning, not the Q&A loop).
3. **QA iteration cap** — driver-level `qa_iterations`/`review_rounds` counters present but the driver
   does not loop; relies on the agent's own loops (a failing QA correctly blocks the merge).
4. Defaults tuned for a **throwaway repo** — recommend keeping auto-merge only on playground repos;
   on any real project switch `gates.review: require_human`.

## Conclusion

The engine is **ready for a first supervised live run** on a playground repo (all permissions gate
live-verified, agent-exec live-verified, dry-run of the whole flow passes). It is **not yet** the
set-and-forget overnight machine of the full vision: interview is template-based and the driver
loops are minimal. With `--dry-run` + the probe + reviewer-gate + logs, the expectations are
clearly documented so the user knows what is and isn't autonomous.
