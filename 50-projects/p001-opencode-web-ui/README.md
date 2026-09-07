# p001 — Better Agentic Web for OpenCode (`ide`)

**Project:** A web-interface wrapper around the **opencode** coding agent — better UI, better agentic web,
**mobile-multitasking first**: run, monitor, and intervene in multiple agent sessions from any device.
**Status:** 🟡 SCAFFOLDED — no product code yet (s001). Stack decision pending (FU-001).
**Bible:** `40-knowledge/agentic-web-ui-research.md` (landscape + UX patterns + MVP) · `40-knowledge/opencode-server-api.md` (the API we build on).

## Mission & differentiators

Build the mobile-first PWA that beats the incumbent `opencode web` and every community UI on **async
mobile multitasking**: notifications on done/needs-decision, phone-based approvals, panic controls,
and a Linear-quality activity view — not a terminal echo.

## Architecture direction (DEC-003/DEC-004)

- Backend spawns/orchestrates `opencode serve` instances; exposes a single API + **SSE bridge**; thin browser client.
- Talk to opencode via `@opencode-ai/sdk` / raw HTTP+SSE. **Not** ACP (stdio) for the browser path.
- Candidate stacks (FU-001, user picks): fork `hosenur/portal` (lean mobile) · fork `chriswritescode-dev/opencode-manager` (complete: auth/push/cron/supervision) · greenfield Bun+Hono+React PWA.

## MVP (9 points, ordered)

1. Session control plane (list/start/resume, SSE live view)
2. Async notifications (push + badge on **done** / **needs-decision** only)
3. Queued permission approvals from phone
4. Panic controls (pause / stop / take-over)
5. Collapsed tool-call tree + inline diff chips, deep-link diffs
6. Plan gate + autonomy dial
7. Offline shell (cached session list, queued messages, conflict notice)
8. Per-session token/cost meter
9. Triage inbox/task queue for concurrent agents

## Deliverables map

| Path | Meaning |
|---|---|
| `config/` | project configs, env templates, deploy configs |
| `notes/` | design/feasibility notes |
| `scripts/` | build/dev/deploy scripts (SoT) |
| `features/` | per-feature specs/status (`FE-<NNN>-<slug>/spec.md` + `status.md`) |
| `sessions/` | per-session working notes for this project |

## References

- opencode server API: `40-knowledge/opencode-server-api.md`
- Landscape + MVP research: `40-knowledge/agentic-web-ui-research.md`
- Decisions: `40-knowledge/decisions-log.md` (DEC-001..004)
- Dev loop: `30-runbooks/rb-001-local-dev-loop.md`
