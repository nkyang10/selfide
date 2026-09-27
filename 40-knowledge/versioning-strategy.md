# Versioning Strategy — p003 opencode fork

> Status: ✅ DECIDED (DEC-042, supersedes DEC-037). Companion: `30-runbooks/rb-004-release.md` for the step-by-step.
> Scope: the fork at `50-projects/p003-opencode-fork/opencode`, upstream = `anomalyco/opencode` (`upstream/dev`),
> origin = `nkyang10/opencode` (`dev`).

## 1. Problem being solved

The fork ships builds with a single **unified, user-facing version** shown identically by the WebUI, the desktop
wrapper, and the engine. Before DEC-042, only the engine received a date-versioned build while the webui and
desktop wrapper still reported the stale upstream `1.18.31`, so the three surfaces disagreed.

## 2. Goals

1. **One version string across surfaces** — the version a user sees in the WebUI Settings "v…", the desktop About
   dialog, and the engine `/api/health` must be the same value.
2. **Deploy/package-time rooted** — the time part is the UTC moment of webui deploy or desktop packaging.
3. **Channel-aware** — dev / beta / stable are explicit, not accidental.
4. **Zero-surprise sync** — merging upstream or changing DB channel must never silently interfere.

## 3. The strategy

### 3.1 Version number → **unified `1.<MAJOR>.<YYYYMMDDHHMMSS>`**

   1.<MAJOR>.<YYYYMMDDHHMMSS>    (UTC)

Example: major 1, deployed at `2026-09-24 21:49:00 UTC` → `1.1.20260924214900`.

- `1` = web-wrapper product major (fixed for now).
- `<MAJOR>` = fork/feature major counter. Increments once per stable/beta cut via `release.ts --bump`. Starts at 1;
  falls back to 1 if the current version is not already in this format.
- `<YYYYMMDDHHMMSS>` = 14-digit **UTC** deploy/package time (`new Date()` at build). This is what makes every
  build unique, which also drives the server-update-refresh reconnect detection (FE-015).

Same grammar for all three channels; only the MAJOR counter and timestamp vary.

| Channel | Version example | Notes |
|---|---|---|
| `dev` | `1.1.20260924214900` | floats until a cut bumps MAJOR |
| `beta` | `1.2.20260924214900` | `--bump` incremented MAJOR |
| `stable` | `1.3.20260924214900` | `--bump` incremented MAJOR |

### 3.2 Where the version lives (single source + injection)

- **Source of truth:** `packages/script/release.ts` computes `1.<MAJOR>.<ts>` and keeps
  `packages/opencode`, `packages/app`, `packages/desktop` `package.json` versions in lockstep (PKG_PATHS).
- **Engine:** `release.ts` emits `OPENCODE_VERSION` env → `build.ts` compiles it into the binary
  (`core/src/installation/version.ts`) → served at `/api/health.healthy.version`.
- **WebUI:** `packages/app/src/entry.tsx` `platform.version` prefers injected `import.meta.env.VITE_APP_VERSION`,
  falling back to `pkg.version`. `build.ts` passes `VITE_APP_VERSION=${Script.version}` when building the embedded
  app, so the deployed WebUI = engine version.
- **Desktop wrapper:** `packages/desktop/electron.vite.config.ts` renderer `define`s
  `import.meta.env.VITE_APP_VERSION` from `OPENCODE_VERSION`; the wrapper's `app.getVersion()` (About/updater)
  flows via `prepare.ts` = `Script.version`. **Desktop packaging must run with `OPENCODE_VERSION` set** to inherit
  the unified value.
- **No hardcoding:** any place that printed a hardcoded/dev version string is drained to this single source.

### 3.3 CRITICAL — channel ≠ DB channel

`OPENCODE_CHANNEL` doubles as the SQLite filename suffix (`opencode-<channel>.db`,
`packages/core/src/database/database.ts`). For DB isolation the fork **must keep `OPENCODE_CHANNEL=mark-dev`**
always (data lives in `opencode-mark-dev.db`). Fork release-channel semantics (`dev`/`beta`/`stable`) live
**only in the MAJOR counter / tag**, never in `OPENCODE_CHANNEL`. Shipping with `OPENCODE_CHANNEL=beta`/`latest`
would silently point at a different/empty DB.

The build helper `50-projects/p003-opencode-fork/scripts/build-linux.sh [dev|beta|stable]` calls `release.ts` and
sets `OPENCODE_VERSION` + `OPENCODE_CHANNEL=mark-dev`.

### 3.4 Sync / release policy (summary)

- Sync upstream on the `dev` line; merge commits, don't rebase.
- `--bump` (stable/beta) increments MAJOR. Upstream MAJOR/MINOR/PATCH is no longer mirrored (use release notes to
  track upstream divergence).
- Tag when published: `v<version>`.

## 4. Implementation status

1. **DONE (s054/s065/s066):** `packages/script/release.ts` unified grammar + `--bump`/`--json`/`--dry`.
2. **DONE (s066):** `build-linux.sh` wires `OPENCODE_VERSION` from `release.ts`; channel stays `mark-dev`.
3. **DONE (s066):** WebUI injection (`entry.tsx` + `build.ts` VITE_APP_VERSION).
4. **DONE (s066):** Desktop renderer injection (`electron.vite.config.ts`); wrapper version via `prepare.ts`.

## 5. Alternatives rejected

- Pure date versioning (no MAJOR counter, no rollback signal).
- Integer SemVer mirroring upstream (`1.18.31-fork.N`) — DEC-037: conflated surfaces show stale values; dropped.
- Git sha as the only identifier — no channel/promotion story.
- CalVer / changesets tooling — heavyweight for a single-maintainer fork.

## 6. Consequences / revisit when

- Desktop packaging must set `OPENCODE_VERSION`; otherwise it falls back to a non-unified string.
- Upstream base is not visible in the version — track divergence in release notes.
- Revisit if the fork needs to publish independently to a registry (would need strict SemVer + tags).

## 7. Decision record

- **DEC-042 (s066)** — Unified user-facing version `1.<MAJOR>.<UTC-deploy-ts>` for webui + desktop + engine, all
  channels; supersedes DEC-037's `-fork.<N>` version string. `OPENCODE_CHANNEL=mark-dev` invariant preserved.
  See `decisions-log.md`.
- **DEC-037 (s054)** — SUPERSEDED by DEC-042 for the version string. Kept the critical `OPENCODE_CHANNEL` DB
  isolation finding.
