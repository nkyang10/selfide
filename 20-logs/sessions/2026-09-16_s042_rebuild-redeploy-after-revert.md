# Session s042 — Rebuild + redeploy :4447 after syncQuestions revert

**Date:** 2026-09-16 (UTC)
**Session number:** s042
**Trigger:** Manual test of pre-revert server required after trial fix e64131e reverted in source.

## Context
- Trial fix `e64131e` (`fix(app): foreground resync also rebuilds pending-question dock`) was reverted cleanly in source (working tree == `e64131e~1` for the 3 syncQuestions files; typecheck passes).
- Running server on :4447 (PID 3073522) still serves the pre-revert build (binary mtime 10:11, still contains `syncQuestions`).

## Goal
Rebuild binary, kill old server, redeploy via `run-web.sh 4447`, confirm served bundle no longer contains `syncQuestions`.

## Steps / Results
- Verified revert in source first: `git diff e64131e~1 -- packages/app/src/context/directory-sync.ts packages/app/src/context/directory-sync.test.ts packages/app/src/pages/directory-layout.tsx --stat` → **empty** (working tree == pre-fix). greps for `syncQuestions` in source: none.
- Rebuilt via `bash scripts/build-linux.sh` (pinned bun 1.3.14 toolchain) → **`0.0.0-mark-dev-202609160420`** (184 MB, mtime 12:20). `strings` check: NO `syncQuestions`.
- Killed old server **PID 3073522** (was serving 10:11 binary) → port 4447 freed.
- Restarted with `OPENCODE_SERVER_PASSWORD=hahahaha OPENCODE_CHANNEL=mark-dev ./scripts/run-web.sh 4447` → **new PID 3139056**, binding 0.0.0.0:4447, started 12:20, using new binary. `[opencode-kickoff]` plugin loaded in log.
- Confirmed served bundle over HTTP (auth `opencode:hahahaha`, `/assets/index--IaTatx8.js`, 2,760,467 bytes, http 200): grep for `syncQuestions` AND `sessionPendingQuestions` → **both ABSENT**.

## Evidence
- Binary: `opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode` (mtime 12:20, ver `0.0.0-mark-dev-202609160420`)
- Logs: `testing/web-4447.log`
- Served bundle sample: `/tmp/opencode/served.js`
- root `/` → 401 (login active, Basic auth), `/login` works

## Handoff / Follow-ups
- **Ready for manual test** — served code now matches reverted source.
- FU-050 (decision-dock re-sync) fix is NO LONGER live. User to decide whether a proper fix is wanted back.
