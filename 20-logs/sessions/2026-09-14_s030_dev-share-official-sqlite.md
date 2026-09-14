# Session s030 — Investigate: make dev fork read official main's sqlite

**Date:** 2026-09-14 (UTC)
**Project:** p003-opencode-fork (web/app)
**Branch:** `dev`

## Request (user)
> recall opencode fork webui — make current dev version read the same sqlite as official main version.

## What it means / diagnosis
The dev fork (web `:4447`) and the official main opencode (`:4445`) each keep their own SQLite DB under
`~/.local/share/opencode/`. The DB filename is derived from the build channel
(`packages/core/src/database/database.ts:path()`):
- channel `latest`/`beta`/`prod` (official main) → `opencode.db`
- any other channel → `opencode-<channel>.db`

Confirmed at runtime (open fds):
- **:4447 (dev fork)** → `opencode-mark-dev.db` (+ wal/shm). Built with `OPENCODE_CHANNEL=mark-dev`,
  version `0.0.0-mark-dev-202609130834`, exe
  `.../p003-opencode-fork/opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode`.
- **:4445 (official main)** → `opencode.db` (1.0 GB).

The separate channel is a **deliberate design decision**, recorded in
`p003-opencode-fork/scripts/build-linux.sh`:
> "Pin a distinctive channel so this fork never shares SQLite state with another opencode build on the
> same machine. Channel becomes the DB suffix (opencode-<channel>.db, see
> packages/core/src/database/database.ts)."

## Options considered for making them share `opencode.db`
1. **Code fix** `packages/core/src/database/database.ts:48-54` → add the fork channel to the
   ["latest","beta","prod"] set so it always resolves to `opencode.db`; then rebuild dev.
2. **Build fix** `scripts/build-linux.sh` → build with `OPENCODE_CHANNEL=latest` (drops `mark-dev`
   suffix); then rebuild + restart.

## Decision (user, via confirm prompt)
- Sharing approach: **"Just stop, don't change anything"** → NO code or build change.
- Process handling sub-question: was moot once no change is made.

**Outcome: aborted by user; no changes made. Reversal of the deliberate separate-DB design was
declined for now.** Both processes keep their own DB (`:4447` → opencode-mark-dev.db, `:4445` →
opencode.db).

## Follow-up
Reopening this someday means reversing DEL-<pending> (the separate-channel design intent). Risk to
document then: two live processes sharing one WAL SQLite file (locking + cross-build schema migrations).
