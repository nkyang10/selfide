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
| Assembler plan → committed | ✅ | agent call + git commit + board note |
| **Engineers in parallel** (≥2 tasks) | ✅ | per-task `git worktree` + branch, batched `max_parallel`, merge, branch housekeeping |
| Researcher (idle, concurrent) | ✅ | background agent during implementation; findings posted to board |
| QA tests-to-green | 🟡 | QA **agent itself iterates** to green (prompt enforces it); the driver-level `qa_iterations` counter is not implemented as a driver loop — failure mode = QA reports and documents inability, no auto re-kick |
| Review + verdict file | 🟡 | reviewer writes `review.md` **if** it writes where the driver looks (3 candidate paths); verdict parsed |
| **Reviewer gates merge** | ✅ **fixed now** | `REQUEST_CHANGES` blocks auto-merge; `require_human` never merges. (Was a decorative phase before the fix.) |
| Ship: PR + merge | ✅ | PR create/merge permissions live-verified |
| Morning report | 🟡 | prints + posts; uses run trail/meta (plan section shows interview plan, not the in-repo assembler plan) |

## Robustness

| Concern | Status | Verdict |
|---|---|---|
| github.com flakiness (443 drops ~130s) | ✅ | git ops retry (3x, backoff); REST unaffected; one live push observed succeeding on retry |
| Agent stdout deadlock (PIPE) | ✅ **fixed now** | agents stream to `ENGINE_STATE/runs/<id>/agent-*.log` instead of an undrained pipe |
| FDs/cleanup | ✅ | stdout handles closed after wait; rogue worktrees removed; probe self-cleans |
| Secrets | ✅ | token only via env; nothing committed (sweep done repeatedly) |

## What is NOT ready / needs user decision

1. **Live end-to-end run** — the full `cycle` has never executed with real agents against the
   playground (only dry-run + isolated live pieces: agent exec, and permissions). First real run is
   still outstanding (FU-012).
2. **Interview intelligence** — questions/plan-stub are template-based; Assembler-driven interview is
   designed but not wired (`prompts/assembler.md` covers planning, not the Q&A loop).
3. **QA iteration cap** — driver-level `qa_iterations`/`review_rounds` counters present but the driver
   does not loop; relies on the agent's own loops.
4. Defaults tuned for a **throwaway repo** — recommend keeping auto-merge only on playground repos;
   on any real project switch `gates.review: require_human`.

## Conclusion

The engine is **ready for a first supervised live run** on a playground repo (all permissions gate
live-verified, agent-exec live-verified, dry-run of the whole flow passes). It is **not yet** the
set-and-forget overnight machine of the full vision: interview is template-based and the driver
loops are minimal. With `--dry-run` + the probe + reviewer-gate + logs, the expectations are
clearly documented so the user knows what is and isn't autonomous.
