# s031 — Global real-data web-research skill

- **Date (UTC):** 2026-09-14
- **User request:** "make the skill a global skill, help make the LLM very likely to utilize it
  because it lacks real-time info, and I would like it to get real data regardless of its knowledge."
- **Scope:** config / skills only. No fork code, no build, no deploy.

## What was done

1. **Diagnosed why Serper failed in agent runs** even though it worked in the terminal.
   - Key was at `~/.bashrc:137`, *after* the interactive-only guard
     (`case $- in *i*) ;; *) return;; esac`, lines 6-9).
   - The agent's bash tool runs a **non-interactive** shell → guard `return`s before the export →
     `SERPER_API_KEY` never set → `serper.py` exited 3 "env var not set".
   - Verified: `bash -ic` sees the key; `bash -c 'source ~/.bashrc'` does not.

2. **Fix A — `~/.bashrc`:** moved `export SERPER_API_KEY=…` to line 13 (above the guard) so
   non-interactive shells inherit it. Removed the duplicate at the old location. Single source of
   truth; no secret copied into the repo.

3. **Fix B — `serper.py`:** added `_load_key_from_bashrc()` + `_get_key()` so the script resolves
   the key in order: (1) `SERPER_API_KEY` env, (2) parse `SERPER_API_KEY="…"` from `~/.bashrc` /
   `~/.profile`. This makes it work no matter how the shell is spawned (env var always wins).
   - Verified: `env -u SERPER_API_KEY python3 serper.py "…"` → real results, exit 0.
   - Verified: env var still wins when set (no regression).

4. **Global skill:** created `~/.config/opencode/skills/web-research/` (SKILL.md + storage/serper.py)
   so it loads in **every** project, not just `ide` / `gdx`. Synced the improved SKILL.md back to the
   project copy (`.opencode/skills/web-research/SKILL.md`).

5. **Rewrote SKILL.md** with an **aggressive, trigger-heavy description**:
   - "Use PROACTIVELY and by default for ANY question that needs real, current, or external data —
     the LLM's training is stale and must NOT be trusted for facts."
   - Enumerates trigger signals: versions, prices, latest/newest, dates/years, who/what/when/where,
     news, scores, install commands, CLI flags, API/library usage, debugging, comparisons, factual claims.
   - Enumerates trigger keywords: search, look up, find out, research, check, verify, what is,
     latest, current, how to, install, compare, release, docs, etc.
   - "Do NOT answer from memory when the answer could be outdated — search first, then answer."
   - Carve-out: skip only for pure codebase questions (read files) or pure math/logic.
   - Serper primary (self-loads key); SearXNG demoted to optional self-hosted fallback;
     raw `websearch`/`webfetch` as last resort.
   - Quality rules: always state the as-of date; cite sources; separate verified from inferred.

## Verification

- `cd /tmp && env -u SERPER_API_KEY python3 ~/.config/opencode/skills/web-research/storage/serper.py
  "latest opencode version" --fresh month` → **real results** (opencode v1.18.30), key self-loaded.
- Global dir listing confirms `web-research` present under `~/.config/opencode/skills/`.
- Frontmatter description keyword density confirmed (21 trigger-keyword hits).

## Evidence / files

- `~/.bashrc` — export moved to line 13 (above interactive guard).
- `.opencode/skills/web-research/storage/serper.py` — key self-load added.
- `~/.config/opencode/skills/web-research/SKILL.md` — global, aggressive description.
- `.opencode/skills/web-research/SKILL.md` — project copy synced (now redundant).
- `40-knowledge/decisions-log.md` — DEC-024 (key self-load) + DEC-025 (global skill).
- `10-status/open-followups.md` — FU-044 resolved.
- `20-logs/command-log.md` — s031 rows appended.

## Notes / revisit

- Workspace copies (`ide`, `gdx`) of `web-research` are now redundant; the global copy is
  authoritative. If a project needs a custom variant, the local one overrides the global.
- The aggressive description may over-trigger on trivial codebase questions; the "Do NOT trigger"
  carve-out (pure codebase / pure math) is the guard. Watch for over-eagerness.
