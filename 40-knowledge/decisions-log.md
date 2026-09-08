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
- **Consequences / revisit when:** opencode agent `permission` must be **block-style YAML** (inline `{...}`
  was rejected by opencode's schema validator — verified live 2026-09-07); agents use `mode: all` so
  `opencode run --agent` can drive them; re-verify on opencode upgrades.

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

### DEC-008 — Engine is deployed inside the selfide repo as a subfolder (2026-09-07)
- **Decision:** The p002 engine ships as `50-projects/p002-selfdev-engine/` inside `nkyang10/selfide`
  (not its own repo). User chose "push into selfide (subfolder)" over a dedicated public/private repo.
- **Rationale:** keeps the control-center single-repo model; the engine's self-improvement loop can
  still operate on its own subfolder via branch/PR.
- **Alternatives rejected:** dedicated `nkyang10/selfdev-engine` repo (public/private) — offered, not chosen.
- **Consequences / revisit when:** if the engine gains independent consumers, split it out then (git subtree).

### DEC-009 — Live-run findings: opencode agent path, git ref namespace, GitHub 5xx (2026-09-07)
- **Decision:** Keep three hard-won rules in the driver: (1) always pass **absolute** `--dir` to opencode
  subprocesses (relative `.` fails agent loading when exec'd without a shell → "Unexpected server error");
  (2) task branches are **flat** `engine/<rid>-tN` (a `engine/<rid>/tN` sub-branch conflicts with the
  `engine/<rid>` ref in git's namespace); (3) the GitHub REST client **retries on 5xx** (observed a
  transient `500` on create_pr that succeeded minutes later).
- **Rationale:** all three were discovered during the first live run — each caused a real abort, once
  against DNS-flaky and slow GitHub connectivity.
- **Alternatives rejected:** treating those as environment noise (they're reproducible: repro showed
  relative-dir fails 6/6 when python-exec'd); dot-nested task branch names.
- **Consequences:** next cycle should self-complete the ship phase without manual help.

### DEC-010 — p003: opencode fork project, vendored clone + own Linux build (2026-09-08)
- **Decision:** New active project `50-projects/p003-opencode-fork`: the **upstream opencode source is
  vendored** as a git-ignored nested clone at `p003/opencode/`, we build our own binary on this machine
  (Bun 1.4.2 in `~/.bun`; `scripts/build-linux.sh`), and every future modification to opencode itself is
  developed here, then optionally upstreamed as a PR. The cloned repo is **not** tracked by the ide repo.
- **Rationale:** the mbot end-goal (p001/p002) will eventually need changes inside opencode (server API,
  auth, SSE, permissions). Having a validated from-source build (aarch64) makes patches cheap to test
  locally instead of waiting for upstream releases.
- **Alternatives rejected:** relying on prebuilt opencode binaries only (cannot carry local patches);
  `git submodule` (nested plain clone is simpler; history is upstream-owned).
- **Consequences / revisit when:** keep the clone shallow (`--depth 1`); re-run `build-linux.sh` after
  pulling upstream. Watch upstream rename/`dev`-branch instability. Build host is aarch64 → binary is
  `opencode-linux-arm64`. **Update (same day):** GitHub fork exists at `nkyang10/opencode`; vendored
  clone remotes = `origin` (fork) + `upstream` (original). API fork failed — user created it via the
  GitHub app (fine-grained PAT lacked fork permission). Re-point pushes at origin; unshallow before first PR.

### DEC-011 — FE-001: login landing page with cookie auth instead of the raw Basic prompt (2026-09-08)
- **Decision:** When the server has a password configured, an unauthenticated **browser** request to any
  path gets a served **login landing page** (401 HTML, `?next` preserved) instead of the browser's Basic
  dialog. `POST /login` validates against `ServerAuth` and sets an `oc_creds` cookie (`base64(user:pass)`,
  `HttpOnly; SameSite=Lax; Path=/`; `Max-Age=1y` when **remember-me** is ticked, session cookie otherwise);
  both the UI router gate and the JSON API gate translate that cookie into Basic credentials. `GET /logout`
  clears it. No password configured → behavior unchanged (open server).
- **Rationale:** requested by user for iOS "Add to Home Screen" shortcuts: a server-set cookie persists in
  WKWebView where app localStorage/headers can be unreliable; a real login page gives a typical
  fail/retry/redirect-back flow. Cookie is passed automatically on every subrequest (SPA shell + SSE/API).
- **Alternatives rejected:** client-side-only login (localStorage) — dies on iOS shortcut scope; keeping
  the native Basic prompt — ugly, no remember-me, breaks redirect-back; token-in-URL (existing
  `auth_token`) — leaks in logs/history.
- **Consequences / revisit when:** `oc_creds` is base64 (not armored) — same trust as Basic on a LAN;
  don't expose 0.0.0.0 outside a trusted network. Raw router routes got no request-time
  `ServerAuth.Config` (Effect service-error) — resolved by resolving config in the router builder and
  passing it into the handler. Re-check upstream merge conflict risk: `packages/server` and
  `packages/opencode` auth files will conflict if upstream refactors auth (likely — it's experimental).

### DEC-010 — Engine repo layer moves to a local Gitea (2026-09-08)
- **Decision:** The p002 engine now targets a self-hosted **Gitea** (http://192.168.1.162:3300, gitea 1.27.3,
  user `mark`). Repos migrated from GitHub by import: `mark/cloud-pos-system` (full git history; issues not
  imported) and `mark/selfide`. Engine adapter: `ENGINE_GITEA=1` + `GITEA_TOKEN` (~/.gitea-engine-token) +
  `ENGINE_GITEA_BASE` + `ENGINE_GIT_ROOT`; API differences handled (label name→id, PR head without owner
  prefix, merge via POST `{"Do":"merge"}`, DELETE branches, base URL + token auth).
- **Rationale:** GitHub `POST /pulls` was returning 500 (empty body) persistently on this account (inc-001);
  a local Gitea removes that dependency and the network flakiness, and keeps PR/review semantics.
- **Alternatives rejected:** continuing on GitHub (blocked); plain `direct_push` only (loses PR semantics
  long-term); migrating to GHES self-host (heavier than Gitea).
- **Consequences / revisit when:** engine runs double as remote GH (default) or Gitea (`ENGINE_GITEA=1`).
  Git notes: `git <owner>` default config is currently GitHub; launch scripts set GITEA env. GitHub remote
  repos remain authoritative for the ide control center; Gitea selfide is a second mirror.
