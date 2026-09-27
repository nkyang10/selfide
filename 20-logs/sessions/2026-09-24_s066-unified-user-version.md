# s066 — Unified user-facing version (webui + desktop wrapper)

**Date:** 2026-09-24 (UTC) **Timestamp:** 2026-09-24 14:30
**Trigger:** user asked to locate + unify the version number shown by the WebUI and the desktop wrapper to a single string `1.<MAJOR>.<UTC-deploy-ts>` (e.g. `1.1.20260924214900`), across ALL channels.
**Result:** ✅ IMPLEMENTED (unified grammar + webui/desktop injection) + docs updated.

## Scope

The fork has three version-bearing surfaces: **engine** (core binary, `/api/health`), **webui** (`packages/app`, Settings "v…"), and **desktop wrapper** (`app.getVersion()` → About/updater/logging). All three read from a shared `release.ts` stamp, but only the engine was actually receiving a date-versioned build; webui + desktop still showed the stale upstream `1.18.31`.

Goal: make webui + desktop wrapper (the two user-facing surfaces) show ONE unified version, timestamp = deploy/package time, for dev/beta/stable.

## Decisions (user-confirmed)

- Grammar: `1.<MAJOR>.<YYYYMMDDHHMMSS>` — `1` = web-wrapper major, `<MAJOR>` = fork/feature major counter, 14-digit UTC deploy time. Example: `1.1.20260924214900`.
- Applies to **all** channels (dev, beta, stable) — supersedes DEC-037's `-fork.<N>` scheme for the version string.
- `OPENCODE_CHANNEL` stays `mark-dev` (SQLite DB suffix) — unchanged.
- Plan-only confirmed first, then implementation approved.

## Version-number inventory (as found)

| Surface | Location | Before |
|---|---|---|
| Engine | `packages/opencode/package.json` → `OPENCODE_VERSION` → `core/src/installation/version.ts` → `/api/health` | `1.18.31` repo; dev build stamped `1.0.YYYYMMDD-N-HHHH` |
| WebUI | `packages/app/src/entry.tsx:123` `pkg.version` | `1.18.31` (stale) |
| Desktop | `packages/desktop/package.json` → `prepare.ts` → `app.getVersion()` | `1.18.31` (stale) |

## Implementation

1. **`opencode/packages/script/release.ts`** — simplified version generation to a single unified grammar for all channels: `1.<MAJOR>.<YYYYMMDDHHMMSS UTC>`. `readForkMajor` only trusts `<MAJOR>` when the current version matches `^1\.(\d+)\.\d{14}$` (else falls back to 1). Writes lockstep to all three package.json (PKG_PATHS). Emits `OPENCODE_VERSION` env consumed by build.ts → engine. Per-day counter state file removed.
2. **`opencode/packages/app/src/entry.tsx`** — `platform.version` (Settings "v…") now prefers injected `import.meta.env.VITE_APP_VERSION`, falling back to `pkg.version` (`||` so empty string also falls back). Same for the Sentry release fallback.
3. **`opencode/packages/opencode/script/build.ts`** — passes `VITE_APP_VERSION=${Script.version}` when building the embedded app, so the deployed WebUI shows the same version as the engine (`/api/health`).
4. **`opencode/packages/desktop/electron.vite.config.ts`** — renderer `define` injects `import.meta.env.VITE_APP_VERSION` from `OPENCODE_VERSION` so the WebUI-inside-desktop shows the unified version. Desktop wrapper `app.getVersion()` (About/updater) still flows via `prepare.ts` = `Script.version` (needs `OPENCODE_VERSION` set when packaging).

## Verified

- typecheck (app, opencode, desktop) all clean; `release.ts` bundles.
- `release.ts --channel dev --json` → `1.1.<ts>`; `--bump` on stable → major increments (`1.1`→`1.2`).
- App built with `VITE_APP_VERSION`; bundle contains the injected string.

## Command log rows (s066)

| UTC time | Session | Target | Command | Exit | Result / note |
|---|---|---|---|---|---|
| 2026-09-24 14:30 | s066 | docs | opened session s066 | 0 | created |
| 2026-09-24 14:35 | s066 | edit | release.ts → unified `1.<MAJOR>.<14-digit-ts>` all channels | 0 | implemented |
| 2026-09-24 14:40 | s066 | verify | typecheck + dry-run release.ts --json | 0 | clean |
| 2026-09-24 14:45 | s066 | docs | update decisions-log, versioning-strategy, runbook, current-state | 0 | supersede DEC-037 |

## Close-out

- **Result:** unified `1.<MAJOR>.<UTC-ts>` implemented for webui + desktop + engine (DEC-042), verified, docs updated. **Code uncommitted** — see FU-073 (commit/push) and FU-074 (desktop packaging must set `OPENCODE_VERSION`).
- **Docs updated:** `40-knowledge/decisions-log.md` (DEC-042), `40-knowledge/versioning-strategy.md` (rewritten for DEC-042), `30-runbooks/rb-004-release.md`, `10-status/current-state.md` (new top entry), `10-status/open-followups.md` (FU-073, FU-074), `20-logs/command-log.md` (s066 rows).
- **Next:** commit + push the 4 changed files; add/document desktop packaging with `OPENCODE_VERSION`; then deploy and visually confirm webui Settings "v…" == `/api/health` == desktop About.
