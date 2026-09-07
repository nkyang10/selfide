# Implementation Decisions Log (ADR-lite)

> Every non-trivial implementation/setup decision gets an entry here: what was decided, why,
> what was rejected. Append-only. This is how future sessions understand *why things are the way they are*.

Format:

```
### DEC-<NNN> — <title> (<YYYY-MM-DD>)
- **Decision:**
- **Rationale:**
- **Alternatives rejected:**
- **Consequences / revisit when:**
```

---

### DEC-001 — Folder-as-control-center, agent-maintained docs (2026-09-07)
- **Decision:** All project work runs from this folder; AGENTS.md bootstraps any future agent; logs are append-only markdown (no database/tooling dependency). Structure mirrors gdx.
- **Rationale:** Same benefits as gdx: portable, human-readable, works offline, full auditability; user explicitly asked for the same structure.
- **Alternatives rejected:** External PM tooling; chat-only memory (lost between sessions).
- **Consequences:** Agents must diligently close out sessions or the system decays; rotation policy in `20-logs/POLICY.md`.

### DEC-002 — Capture the 7-level research as permanent knowledge (2026-09-07)
- **Decision:** The web/UX/architecture research done for this project is persisted verbatim-ish into `40-knowledge/agentic-web-ui-research.md` + `40-knowledge/opencode-server-api.md`, with source URLs, so no re-research is needed.
- **Rationale:** Golden rule #6; research consumed expensive parallel searches; future sessions must not repeat it.
- **Alternatives rejected:** Leaving it in chat history only.
- **Consequences:** Knowledge docs are the reference for the p001 brief; update them when new facts land.

### DEC-003 — Build on opencode's HTTP+SSE server API, NOT ACP, for the web UI (2026-09-07)
- **Decision:** The web UI (backend) will talk to `opencode serve` over REST + SSE (port 4096) via `@opencode-ai/sdk` or raw HTTP. ACP (stdio JSON-RPC) is out of scope for the browser path.
- **Rationale:** opencode's server API is exactly what all working community UIs use (portal, oc-web, opencode-vibe, native mobile clients); browsers cannot spawn stdio children so ACP requires a stdio→HTTP bridge (ngent-style) with no benefit here; one codebase can later drive multiple opencode instances by pointing at multiple ports.
- **Alternatives rejected:** ACP-over-stdio fixed to a local proxy (extra moving part); WebHook-only model (no push channel).
- **Consequences:** All live/SSE event subscriptions use `GET /event`; auth is opencode's HTTP Basic (see FU-003).

### DEC-004 — Stack decision DEFERRED to user (FU-001) with recommendation (2026-09-07)
- **Decision:** No code yet. Three candidate paths on the table: (A) greenfield Bun+Hono+React PWA, (B) fork `hosenur/portal` (lean mobile-first baseline), (C) fork `chriswritescode-dev/opencode-manager` (most complete: auth, push, cron, supervision). Recommendation: B or C to bootstrap, then beat the incumbent on mobile multitasking UX.
- **Rationale:** All three proven; greenfield costs time but zero legacy; forking captures working SSE/process-management fast.
- **Alternatives rejected:** — (open, awaiting user).
- **Consequences:** Revisit when FU-001 is answered; record the pick here.

### DEC-006 — p002 operating model is a user-driven overnight night-cycle (2026-09-07)
- **Decision:** p002's primary user-facing flow is the **overnight cycle**: user hands off work +
  target feature before sleep → engine↭user clarifying interview until both say "good" → confirmed
  kickoff → autonomous multi-agent run on **one GitHub repo** (planning, deploying, shared board via
  issue/PR comments, self-raised child issues solved by other agents, an idle **researcher** agent
  doing web research to steer toward the requirement) → morning report → loop on the same repo until
  the user says "requirement reached". Captured as FE-002; roles grow a `researcher`.
- **Rationale:** this is the user-specified usage (async, mobile-friendly, bounded overnight cost,
  GitHub as workspace+board+audit trail); it also demos the "agents raising issues other agents solve"
  emergent pattern from the research (MetaGPT SOP teams + Copilot-issue-to-PR spine + researcher).
- **Alternatives rejected:** synchronous day-time full-autonomy loop with no gates (user stays out, but
  wanted interview + "good" gate before kickoff); separate external board tool (use GitHub only).
- **Consequences / revisit when:** `kickoff: confirm` default is a hard safety gate; morning report is
  mandatory; `duration_hours` caps night spend. When p001 exists, the interview + morning report move
  to the mobile push channel.

### DEC-007 — p002 MVP engine: driver in stdlib Python, roles as generated opencode agents (2026-09-07)
- **Decision:** Engine = `scripts/driver.py` (argparse, subcommands handoff|clarify|run|report|cycle) +
  a thin stdlib `github_api.py` REST client; role agents are **generated** into each worktree's
  `.opencode/agent/` from canonical `prompts/<role>.md` (frontmatter table in driver). Config is
  `config/engine.json` (TOML/YAML avoided — stdlib only). Target repo is pluggable (`--repo owner/name`).
- **Rationale:** stdlib-only keeps the engine dependency-free; generated agents keep `prompts/` as a
  single improvable source of truth (RETRO edits prompts, not copies). `--dry-run` gives risk-free testing.
- **Alternatives rejected:** `gh` CLI dependency (not installed here); YAML/TOML config (no yaml in stdlib);
  hand-maintained agent files per checkout (drift risk with RETRO).
- **Consequences / revisit when:** the opencode agent frontmatter schema is the fragile part — must be
  verified live; if opencode `--agent` requires primary-mode agents, flip `mode: all` accordingly.

### DEC-005 — p002: the self* development engine, designed not built (2026-09-07)
- **Decision:** New active project `50-projects/p002-selfdev-engine`: a self-hostable engine where role
  agents (assembler, engineer, QA, reviewer, retro) drive a product through GitHub (issue→branch→PR),
  with a test-to-green gate and a retrospective loop that improves the engine's own briefs. User chose
  **design-doc-first** and **fresh scratch repo** as the first target. Blank scaffold renamed
  `p002-TEMPLATE` → `p000-TEMPLATE` to free the p002 number.
- **Rationale:** The final IDE (p001) is a large target; smallest proof of the core *self-test/
  think/complete* loop first. Design-doc-first per user; scratch repo avoids risk to real code early.
- **Alternatives rejected:** building directly (user chose design first); self-hosting the loop on the
  ide repo itself as first run (deferred); using SWE-bench as the initial eval substrate (heavy — MVP
  uses a small scratch task set instead).
- **Consequences / revisit when:** FE-001 spec + config drafted, prompts v1 placeholders. Code starts
  next session once prompts are written and scratch repo flow verified. If promises/drivers change, the
  driver may move from bash/Python to opencode-server API — that's also the p001 integration point.
