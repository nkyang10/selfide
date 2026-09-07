# Logging Policy

## What must be logged

Every command the agent executes — or that changes this folder's structure — gets one row in
`20-logs/command-log.md`. Read-only diagnostics count too. Success and failure both count.

## Entry format (fixed)

```markdown
| UTC time | Session | Target | Command | Exit | Result / note |
|---|---|---|---|---|---|
| 2026-09-07 08:00 | s001 | folder | `mkdir -p …/ide/{00-env,…}` | 0 | Control-center skeleton created |
```

Rules:
- **Append-only.** Never edit or delete old rows. Mistakes get a corrective row.
- Timestamps in **UTC**, 24h (`YYYY-MM-DD HH:MM`).
- `Target`: `dev-station` (local shell), `node-01`/`node-02` (DGX), `mobile`, or `folder` (this project tree).
- Truncate long output; keep enough to reconstruct what happened.
- Never log secrets (tokens, passwords). Redact.

## Session records

One file per working session: `20-logs/sessions/<YYYY-MM-DD>_s<NNN>_<slug>.md`.
Contents: goal → actions taken → results/evidence → follow-ups created.
Session numbers are global and monotonically increasing (s001, s002, …).

## Incidents

Anything that breaks, fails unexpectedly, or requires recovery gets
`20-logs/incidents/inc-<NNN>.md`: timeline, impact, root cause, resolution, prevention.
Link incidents from the session record and from `10-status/open-followups.md` if user action is needed.

## Retention & rotation

- `command-log.md` is the live log. When it passes ~500 lines, move the older half to
  `90-archive/command-log-<YYYY-MM>.md`, leave a pointer line at top of the live file.
- Nothing in `20-logs/` is ever deleted outright.
