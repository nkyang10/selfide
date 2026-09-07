# Open Follow-ups

> The user↔agent contract. Anything waiting on someone lives here with an owner and due date.
> Agent flags items overdue >7 days at session start. Close items by filling in the resolution column.

| ID | Created (UTC) | Item | Owner | Priority | Due | Status |
|---|---|---|---|---|---|---|
| FU-001 | 2026-09-07 s001 | **Choose tech stack** for p001: fork `hosenur/portal` (leanest mobile-first) vs fork `chriswritescode-dev/opencode-manager` (most complete: auth, push, cron, process supervision) vs greenfield (Bun+Hono + React PWA). Recommendation: fork one, beat it. | user | high | next session | open — stack candidates + tradeoffs in `p001/README.md` |
| FU-002 | 2026-09-07 s001 | **Choose deployment target** for the web UI: dev-station only (fast loop) vs dgx-node-01 vs dgx-node-02. Also remote-access path for phone (LAN / Tailscale / tunnel). | user | high | next session | open — see `00-env/deployment-targets.md` |
| FU-003 | 2026-09-07 s001 | **Auth model**: none (LAN/VPN only) vs HTTP Basic (opencode native) vs full user auth (Better Auth like opencode-manager). | user | medium | when building | open |
| FU-004 | 2026-09-07 s001 | **MVP scope confirmation**: is the 9-point MVP (sessions → notifications → approvals → panic → diffs → plan-gate → offline → cost → inbox) right, or trim? | user | medium | when building | open — see `p001/README.md` §MVP |
| FU-006 | 2026-09-07 s001 | Target the phone during dev: which device(s)/browser(s) to test the mobile UX on? | user | low | when mobile UX starts | open |
| FU-007 | 2026-09-07 s002 | **Go-ahead for p002 prototype** building: user OK'ed design-first + scratch repo; engine MVP now built & dry-run OK. Confirm **live-run go** for the playground. | user | high | next session | open (go-ahead implied; live run = FU-012) |
| FU-008 | 2026-09-07 s002 | **Eval substrate for self-testing**: SWE-bench(Verified) vs a small private eval repo vs ticket-to-PR smoke tasks. Determines how "self-testing" is graded. | user | medium | next session | open |
| FU-010 | 2026-09-07 s002 | **Model choice for role agents**: use default opencode config or pin a cheaper/faster model for QA/engineer? Affects cost of ≥3 MVP runs. | user | low | next session | open — config `model` in engine.json |
| FU-011 | 2026-09-07 s002 | **Interview depth**: engine re-asks until BOTH say good; cap is `max_question_rounds` (default 2) — confirm OK, or prefer more rounds on complex work. | user | low | when clarifying UX | open |
| FU-012 | 2026-09-07 s002 | **Live engine run** on playground `nkyang10/cloud-pos-system`: approve `run --cycle 1` with real opencode agent exec (creates branch+PR+merge). | user | high | next session | ✅ LIVED 2026-09-07: cycle 1 shipped — PR #13 merged (+1138/−1, 15 QA tests). Ship-phase driver path still to re-verify with the new 5xx retry (manual completion during transient 500). |
| FU-016 | 2026-09-07 s002 | **Validate the fixed ship path**: run cycle 2 (or a re-run) so the driver's own create_pr→merge lands without manual help; also exercises multi-cycle re-push. | engine | medium | next session | open |
| FU-017 | 2026-09-07 s002 | **Close epic #12** on completion, or let cycle loops decide; suggest closing when user declares "requirement reached". | user | low | after FU-016 | open |
| FU-013 | 2026-09-07 s002 | **Token permissions**: fine-grained PAT passed `probe` PARTIALLY — works: contents push, issue create, metadata. **Missing (403):** issue comments/edit/close (Issues R&W), pull requests create/merge (PRs R&W). Fix in GitHub → Developer settings → fine-grained PAT → repo permissions: **Issues: Read and write**, **Pull requests: Read and write** (Contents already R&W). Then re-probe. Also rotate token after testing (it's in chat history). | user | high | next session | open — probe FAIL list recorded |
| FU-015 | 2026-09-07 s002 | **Playground cleanup**: close `cloud-pos-system` issues #1/#2 and delete `probe-base` branch (it became the tmp default until a real main exists) — possible after FU-013 perms. | engine | low | after FU-013 | open |

## Resolved

| ID | Resolved (UTC) | Resolution |
|---|---|---|
| FU-005 | 2026-09-07 s002 | **GitHub mirror name**: ide control center → `nkyang10/selfide` (main pushed; public). |
| FU-009 | 2026-09-07 s002 | **Target for engine runs**: real playground `nkyang10/cloud-pos-system` (public, empty), created; driver raises epic issues in-repo. |
| FU-014 | 2026-09-07 s002 | **Engine home**: stays inside selfide as `50-projects/p002-selfdev-engine/` (user chose subfolder over dedicated repo) — DEC-008. Visibility remains public (matches existing repos). |
