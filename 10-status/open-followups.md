# Open Follow-ups

> The user↔agent contract. Anything waiting on someone lives here with an owner and due date.
> Agent flags items overdue >7 days at session start. Close items by filling in the resolution column.

| ID | Created (UTC) | Item | Owner | Priority | Due | Status |
|---|---|---|---|---|---|---|
| FU-001 | 2026-09-07 s001 | **Choose tech stack** for p001: fork `hosenur/portal` (leanest mobile-first) vs fork `chriswritescode-dev/opencode-manager` (most complete: auth, push, cron, process supervision) vs greenfield (Bun+Hono + React PWA). Recommendation: fork one, beat it. | user | high | next session | open — stack candidates + tradeoffs in `p001/README.md` |
| FU-002 | 2026-09-07 s001 | **Choose deployment target** for the web UI: dev-station only (fast loop) vs dgx-node-01 vs dgx-node-02. Also remote-access path for phone (LAN / Tailscale / tunnel). | user | high | next session | open — see `00-env/deployment-targets.md` |
| FU-003 | 2026-09-07 s001 | **Auth model**: none (LAN/VPN only) vs HTTP Basic (opencode native) vs full user auth (Better Auth like opencode-manager). | user | medium | when building | open |
| FU-004 | 2026-09-07 s001 | **MVP scope confirmation**: is the 9-point MVP (sessions → notifications → approvals → panic → diffs → plan-gate → offline → cost → inbox) right, or trim? | user | medium | when building | open — see `p001/README.md` §MVP |
| FU-005 | 2026-09-07 s001 | **GitHub mirror name** for this repo (gdx → `nkyang10/dgx`; ide → ?). | user | low | when convenient | open |
| FU-006 | 2026-09-07 s001 | Target the phone during dev: which device(s)/browser(s) to test the mobile UX on? | user | low | when mobile UX starts | open |

## Resolved

| ID | Resolved (UTC) | Resolution |
|---|---|---|
| — | — | (none yet) |
| FU-007 | 2026-09-07 s002 | **Go-ahead for p002 prototype** ("self* dev engine"): opencode-subagents role team + GitHub-native issue→branch→PR + eval/self-test loop + lessons→prompt self-improvement. Need: OK + scope of MVP run + which model(s). | user | high | next session | open — research at `40-knowledge/multi-agent-sdlc-engine-research.md` |
| FU-008 | 2026-09-07 s002 | **Eval substrate for self-testing**: SWE-bench(Verified) vs a small private eval repo vs ticket-to-PR smoke tasks. Determines how "self-testing" is graded. | user | medium | next session | open |
| FU-009 | 2026-09-07 s002 | **Author repo details for scratch target**: name + visibility (private default?) to use for engine's first runs; created by driver via `gh`? | user | low | next session | open |
| FU-010 | 2026-09-07 s002 | **Model/loudness choice for role agents**: use default opencode config or pin a cheaper/faster model for QA/engineer? Affects cost of ≥3 MVP runs. | user | low | next session | open |
| FU-011 | 2026-09-07 s002 | **Interview depth**: engine re-asks until BOTH say good; cap is `max_question_rounds` (default 2) — confirm OK, or prefer more rounds on complex work. | user | low | when clarifying UX | open |
| FU-012 | 2026-09-07 s002 | **Live engine run** on playground `nkyang10/cloud-pos-system`: approve `run --cycle 1` with real opencode agent exec (creates branch+PR+merge). | user | high | next session | open — engine built & dry-run OK |
| FU-013 | 2026-09-07 s002 | **Token hygiene**: the shared fine-grained PAT in chat should be **rotated** after the live run; document scopes needed (repo write, issues, PRs) in `00-env/`. | engine | medium | next session | open |
| FU-014 | 2026-09-07 s002 | **Selfide repo**: future ide project work pushes to `nkyang10/selfide` (origin set). Decide whether github mirror stays public or private. | user | low | as needed | open |
