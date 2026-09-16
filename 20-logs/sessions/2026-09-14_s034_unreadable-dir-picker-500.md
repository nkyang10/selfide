# Session s034 — FU-047: picker browsing to unreadable root dirs 500s the server

- **Date:** 2026-09-14 (UTC)
- **Branch:** `dev` (p003-opencode-fork)
- **Why:** FU-047 on-device retest. Browsing the folder picker (Zag TreeView) to the filesystem
  root and opening **root-owned, unsearchable directories** produced hard 500s in the browser console:
  `GET /file?path=&directory=/lost+found 500` and `GET /file?path=&directory=/root 500`.

## Diagnosis (root cause)

- Reproduced locally over the LAN with auth (`opencode:hahahaha`): `directory=/root` and
  `directory=/lost+found` → **500**, while `/etc`, `/tmp`, `/var/log`, `/home/mark` → 200.
- The 500 was **not specific to `/file`**: `/config`, `/session`, and `/event` also 500'd with
  `directory=/root`. Only endpoints that ignore routing (`/oai/models`) stayed up. So the die was in
  shared location/project resolution, not the `file.list` fallback (file.ts:100-123).
- Surfaced the masked `UnknownError` by temporarily logging `Cause.pretty` in
  `middleware/error.ts` (reverted after). Real defect:
  `PlatformError: PermissionDenied: FileSystem.access (/root/opencode.jsonc)` → `EACCES`.
- Chain: `config` service → `Location.Service` → `Project.resolve` (project.ts:110) →
  `git.repo.discover` (git.ts:184) → `FSUtil.up` (fs-util.ts:168). `up` probed `join(dir, target)`
  (`.git` / `opencode.jsonc` / ...) with **raw `fs.exists`**, which yields `PlatformError:
  PermissionDenied` when the parent dir is root-owned and not traversable by the server user (`mark`).
  That typed `PlatformError` crossed a `.orDie` boundary (config load), becoming a **defect** (die) →
  HTTP 500 with a fresh masked ref each call.

## Fix

- **`packages/core/src/fs-util.ts` — `FileSystem.up`**: probe targets with `existsSafe(search)` (the
  already-defined helper that returns `false` on **any** error incl. `PermissionDenied`) instead of
  raw `fs.exists`. An unreadable path is now treated as "not present" so an `up`-walk never defects
  from an inaccessible parent. This is the narrowest, shared fixpoint — it covers `.git`,
  `opencode.jsonc`, and any other up-probe across project/location/git discovery.
- Also hardened `Project.resolve` (project.ts) to degrade `git.repo.discover` failure to the global
  project via `Effect.catchCause` — kept as defense-in-depth; the `up` change is the operative one.

## Verification

- New regression test `packages/opencode/test/server/httpapi-file-unreadable-dir.test.ts`:
  `file.list` for `/root`, `/lost+found` (EACCES), plus `/etc`, `/home/mark`, at `path` `""`, `"."`,
  `"sub"` — **12/12 expect 200** (was 500).
- Full httpapi suite: **215 pass / 0 fail / 2 skip** (`httpapi-file`, `httpapi-config`, etc.).
  Core `config` + `util` tests: **77/77**. Core + opencode `typecheck` (`tsgo --noEmit`) clean.
- **Built + deployed** `0.0.0-mark-dev-202609140421` (PID 1690566, :4447, password login preserved).
  Live over LAN (auth): `/file?path=&directory=/root` → **200**, `/lost+found` → **200** (was 500);
  `/config?directory=/root` and `/session?directory=/root` → **200** (were 500); `/etc` and
  `/home/mark` still 200; unauth `/` = 401, `/login` = 200 (login page intact).

## Notes / follow-ups

- Unreadable (EACCES) root dirs now return **empty listings**, not 401/403 — the picker shows them
  as empty folders instead of breaking the whole request. No on-device retest performed here; user
  should re-run the FU-047 picker browse of `/lost+found` / `/root` from the phone/desktop.
- `/event` is an SSE stream (never returns a body); not part of the bug path — excluded from curl checks.
- Temp `console.error` in `middleware/error.ts` used for diagnosis was **removed**.
