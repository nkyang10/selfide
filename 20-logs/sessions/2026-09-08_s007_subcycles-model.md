# Session s007 — p002: refined cycle model (sub-cycles N.1 for half-done work)

- **Date:** 2026-09-08 (UTC)
- **Goal (user spec):** refine "no retry" — cycles keep flowing; half-done engineer work is finished by a
  small cycle (`3.1`, `3.2`, …) that runs before the next cycle; never-started work rolls to the next main
  cycle; an engineer's load per cycle is "as much as it can do".

## Changes (`p002-selfdev-engine/scripts/driver.py`)
1. `--cycle` is now a **string** ("3" or "3.1"); `cmd_run` computes `cyc`, `base_cycle`, `sub_cycle`.
2. Worker bookkeeping unifies per base cycle: `workers-{base_cycle}.jsonl` with statuses **done** / **half**
   (shared by a main cycle + all its sub-cycles).
3. Engineer loop (already sequential): a task over its budget → status **half**; worktree + task branch +
   opencode session are preserved; drive continues to the next task (no park). Success → done (merge+push,
   branch deleted).
4. **Sub-cycle run** (`--cycle 3.1`): skips assembler+researcher; processes ONLY the half tasks (session
   resume via `_last_session_id`); then QA → review → design → ship for whatever finished.
5. Per-cycle engineer wall budget `engineer.cycle_time_secs` (default 12h) → later tasks roll to next main
   cycle unstarted.
6. `marathon`: new `--max-sub` (default 5); after each main cycle, flushes half tasks via `N.1…N.k`
   (re-checking `_half_tasks`), then proceeds. Hard-failing a main/sub cycle still stops for the product.
7. `_park_cycle` removed (no parking except assembler-abort which keeps stopping).

## Status
- Compiles + `--help` OK; `_half_tasks` logic unit-tested.
- Cycle-3 is finishing on the OLD binary (marathon pid 1948563, t1 done 15:06Z). The new flow activates
  on the next marathon spawn.

## Evidence
- DEC-012 recorded; command-log rows; `20-logs/sessions/2026-09-08_s007_*.md`.
