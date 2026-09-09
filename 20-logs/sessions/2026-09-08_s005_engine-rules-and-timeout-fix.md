# Session s005 — p002 engine: timeout fix + rule change (1 role, no retry, park & product)

- **Date:** 2026-09-08 (UTC)
- **Goal (user spec):** diagnose why the cloud-pos cycle-2 engineers kept timing out, fix it, and adopt
  3 operating rules: (1) each role runs at most 1 agent; (2) no agent retries — everything stateful,
  cycle = start → result → next cycle; (3) a task that exceeds its timeout reports to the product and
  the run parks (waiting-product) until the product arranges the next cycle.
- **Status:** ✅ code done + verified; marathon restarted with new code (stateful resume of cycle 2).

## Diagnosis (why cycle-2 timed out)

- All 4–5 cycle-2 engineers + researcher were killed at exactly the 3600s `p.wait` watchdog (`rc=-1`),
  in two waves: t1/t2 04:05, t3/t4 05:05, t5 06:05 (spawned 1h apart).
- Root cause: the DGX LLM gateway was degraded 02:45–03:56Z — 32 completions took **3–15 min each**
  (gateway `logs/20260908.jsonl`: 12.8m, 15.4m, 7–10m…), exactly the window cycle-2 was running, with
  4 engineers + 1 researcher + the Gitea box (.162) + another box (.189) all thrashing the single GB10
  vLLM. Each task needs dozens of sequential LLM calls → far beyond 1h.
- Secondary bugs found: driver killed with SIGKILL and never `wait()`ed (zombie `[opencode]` defuncts);
  child stdout buffering made run logs look empty (SIGKILL drops the buffer).

## Code changes (`p002-selfdev-engine/scripts/driver.py`)

1. **`_terminate()`** — SIGTERM (grace 15s) → SIGKILL → always `p.wait()`; used in all timeout paths.
2. **Watchdogs** — engineer/researcher timeout configurable (`timeout_secs`), default 3600 → **7200s**.
3. **`run_agent`** — single attempt (removed the retry loop); non-zero exit is final, recorded by caller.
4. **One role one agent** — researcher runs **before** engineers (blocking, `run_agent`); engineers run
   strictly sequential, one worktree at a time; each finished task is merged + pushed immediately so
   state survives; `max_parallel` effectively 1.
5. **Stateful resume** — `workers-<cycle>.jsonl` records let a re-run skip already-done tasks
   (`done_ids`); `_phase()` skip-done unchanged.
6. **Park on timeout** — new `_park_cycle()`: posts to the epic board, sets `cycleN-waiting-product`,
   `sys.exit`s non-zero. Marathon loop: removed all retry/backoff/ship-only-resume; a failed/parked
   cycle posts `⛔ marathon stopped … awaits product` and stops.
7. Removed now-dead `_ship_only_pending()`.

## Actions

- Restarted marathon with new code: `marathon --run 20260908-0233 --start 2 --max 30 --min-gap 0
  --repo mark/cloud-pos-system` (pid 1722974, Gitea env via `scripts/engine-env-gitea.sh`).
  Verified stateful resume: `RESUME: 1 phase(s) already done ['assembler']` → cycle 2 continuing.
- Old processes (marathon 1535857, cycle-2 driver 1570581, orphan agents 1572483/1647817/1692502) killed.

## Evidence

- Gateway latency: `/tmp/opencode/gw_dur.txt`, `~/Desktop/UP-STORE/gateway-deploy/logs/20260908.jsonl` (DGX).
- Run state: `ENGINE_STATE/runs/20260908-0233/{trail.md,workers-2.jsonl,state-2.json}`.

## Follow-ups created / closed

- FU-016 (validate fixed ship path) → carried; cycle-2 resume under new rules is the live probe.
- NEW FU-02x: decide whether QA/reviewer/designer timeouts should ALSO park (currently only
  engineer/researcher park).

## s005 addendum 2 — worker ACTIVITY invisibility + model pinning (same session)

**User report:** "DGX DeepSeek is working, I just can't see your worker activity." Diagnosis:

1. **Confirmed the engine DOES use the local gateway** — gateway log lines have
   `model=general`, `model_upstream=deepseek-ai/DeepSeek-V4-Flash-0731`; the researcher / any role agent
   sends 130k–215k-token requests into vLLM. (The earlier "zero large prompts today" was a parse bug on
   my side: `prompt_tokens` is top-level, not under a `usage` key.)
2. **Root cause of "no visible activity":** `opencode run --format json` block-buffers its stdout when
   the destination is a file → run logs (`agent-researcher-2.log` etc.) stayed at 0 bytes for the whole
   hour while the agent was actually working; SIGKILL (old code) dropped the buffer entirely.
3. **Fix:** spawn each role agent through `stdbuf -o0 script -qefc '<cmd>' /dev/null` — the child gets a
   PTY (opencode streams JSONL line-wise) and `script` writes unbuffered to the run log. Verified live:
   179KB/90s growth, 34 events (step_start/step_finish/text/tool_use). My earlier Python `pty` reader had
   a 64KB-drain-per-second bug and `--agent`-with-`pty` produced nothing → replaced.
4. **Model pinning:** `config/engine.json` `"model": "dgx/general"` (was `""` → opencode default, which
   could route to the external `opencode-go` provider in `~/.local/share/opencode/auth.json`). Because
   `agent_cmd` appends `-m cfg["model"]`, every role now deterministically hits the local DGX gateway.
5. **`_terminate`** now signals the whole process group (`os.killpg`, agents run `start_new_session=True`)
   — required now that `script` spawns a grandchild.
6. Also found + fixed: the researcher ran with the **default agent** because `materialize_agents` planted
   briefs only in the repo worktree, not in `res_dir`; now `materialize_agents(cfg, res_dir)` runs too
   ("agent researcher not found" warning gone).

## s005 addendum 3 — research persisted to repo + Gitea wiki (same session)

- **Gap:** `ENGINE_RESEARCH.md` was never committed — it only lived in the temp `res_dir` + a truncated
  board comment. Fixed: driver now copies it into `ENGINE_STATE/RESEARCH/<run>.md`, commits + pushes on
  the engine branch; backfilled cycle-2 (9bb0e50).
- **Wiki:** Gitea wiki is git-backed (`{repo}.wiki.git`). `.wiki.git` clone returns 500 until the wiki is
  initialized — create a page via `POST /api/v1/repos/{repo}/wiki/new` first. Driver now publishes each
  run's findings as a wiki page (`gh.add_wiki_page`, non-fatal). Live: `20260908-0233-researcher` +
  `_Sidebar` on mark/cloud-pos-system wiki.


