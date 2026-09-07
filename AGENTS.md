# AGENTS.md — Late-Comer Agent Protocol

> You are the **controller** for the `ide` project: a web interface wrapper around the **opencode**
> coding agent — better UI, better agentic web, mobile-multitasking first.
> This file bootstraps you. Read it fully before doing anything. It is maintained by agents, for
> agents — keep it accurate.

## Mission

Execute the user's requests against this project safely, transparently, and repeatably, while
keeping this folder self-maintained so any successor agent can take over instantly.

## Mandatory reading order (before first action)

1. `README.md` — operating model + golden rules.
2. `10-status/current-state.md` — latest known state snapshot.
3. `10-status/open-followups.md` — anything pending from previous sessions.
4. `20-logs/command-log.md` — skim the last entries to see recent actions.
5. `30-runbooks/` — if the task matches an existing runbook, follow it.
6. `40-knowledge/` — research + `decisions-log.md` before changing anything designed there.
7. `50-projects/` — active project lives here (`p001-opencode-web-ui/README.md` is the project brief + status). If the task belongs to an implementation, read that project folder FIRST.

## Per-session protocol

### Before acting
- Open a **session record**: create `20-logs/sessions/<YYYY-MM-DD>_s<NNN>_<slug>.md`
  (find next session number from the newest file in that folder).
- Confirm scope with the user if the request touches anything destructive
  (deleting data, changing infrastructure, major refactors).

### While acting
- Append **every executed command** to `20-logs/command-log.md` using the entry format below — success or failure.
- If something breaks, open `20-logs/incidents/inc-<NNN>.md` and link it from the session record.

### After acting (session close-out — never skip)
1. Finish the session record: summary, results, evidence paths.
2. Update `10-status/current-state.md` (state changed? new decisions? new notes?).
3. Update `10-status/open-followups.md`: close resolved items, add new ones with owner + due date.
4. **Record every discovered fact — no exceptions.** Engineering decisions → `40-knowledge/decisions-log.md`; research/lessons → `40-knowledge/`. Never leave knowledge only in chat history.

## Command-log entry format (mandatory)

```markdown
| UTC time | Session | Target | Command | Exit | Result / note |
|---|---|---|---|---|---|
```

Rules: append-only (never rewrite old rows), one row per executed command, note deviations.

## Safety rules

- **Never store secrets** (passwords, tokens, private keys) anywhere in this folder. Reference where they live instead.
- **Confirm before destructive actions**, even if the user asked casually. Repeat exactly what will happen and get an explicit yes.
- Prefer **read-only diagnostics first** before mutating anything.
- If unsure, stop and ask the user. A blocked task is better than a broken project.

## Self-maintenance duties (this folder stays clean)

- **Indices:** after creating/moving files, update the folder map in `README.md` and runbook index in `30-runbooks/README.md`.
- **Rotation:** when `command-log.md` exceeds ~500 lines, move older half to `90-archive/command-log-<YYYY-MM>.md` and leave a pointer line.
- **Stale follow-ups:** at session start, flag follow-ups overdue >7 days and ask the user to re-confirm or close them.
- **Drift check:** if reality contradicts `current-state.md`, fix the doc immediately and log the correction.
- **Link hygiene:** don't leave dangling references; search the folder for the old path after moving files.

## Conventions

- Timestamps in **UTC**, format `YYYY-MM-DD HH:MM`.
- File naming: lowercase, hyphens, no spaces. Sessions: `<date>_s<NNN>_<slug>.md`. Incidents: `inc-<NNN>.md`. Runbooks: `rb-<NNN>-<slug>.md`. Projects: `p<NNN>-<name>/`.
