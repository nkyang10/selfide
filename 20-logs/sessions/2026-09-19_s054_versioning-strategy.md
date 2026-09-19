# s054 — Versioning strategy for future releases

**Date:** 2026-09-19 (UTC) **UTC timestamp:** 2026-09-19 08:30
**Trigger:** user asked to prepare a versioning strategy for future releases of the fork.
**Result:** ✅ STRATEGY WRITTEN (DEC-037) + release runbook.

## Summary

Analyzed the fork's current versioning then designed a forward strategy.

### Current state (as found)

- Fork `dev` was diverged: 36 commits ahead of `upstream/dev` (anomalyco/opencode), reconciled in s-trunk work:
  - `54df2c4` merged 59 upstream commits (0 conflicts).
  - `9ebb0b3` merged 3 Windows-build commits from `origin/dev` (0 conflicts).
  - Pushed `origin/dev` 7a43632..9ebb0b3. Typecheck 30/30, app build OK, core tests 3578/8 (8 = pre-existing env/locale/upstream issues).
- Versioning today: `package.json` version tracks upstream `1.18.31` (SemVer). At build time `script/build.ts` stamps
  `OPENCODE_VERSION` with `0.0.0-mark-dev-<timestamp>` (date-based). No changesets/lerna; bumps are manual.
- Existing tags: `v0.0.0-dev-<date>`, `v0.0.0-mark-dev-<date>` — date-based, not SemVer.

### Documents created

- `40-knowledge/versioning-strategy.md` — full strategy (DEC-037).
- `30-runbooks/rb-004-release.md` — step-by-step release runbook.
- `README.md` folder map + runbook index updated.

### Recommendations (summary; see DEC-037)

- Adopt **intel SemVer** `MAJOR.MINOR.PATCH-mark.<build>` at the package level; keep timestamp only as build metadata.
- Three channels: `dev` (date float), `beta`, `stable`. Only stable gets tagged SemVer `v<ver>`, pushed to `origin` release.
- Keep sync cadence with upstream noted. Rebasling of the ACP/system-prompt divergences assessed as low-conflict.

## Command log rows (s054)

| UTC time | Session | Target | Command | Exit | Result / note |
|---|---|---|---|---|---|
| 2026-09-19 08:15 | s054 | fork | git fetch upstream + merge upstream/dev (54df2c4) + origin/dev (9ebb0b3) + push | 0 | fork dev reconciled, in sync |
| 2026-09-19 08:20 | s054 | fork | bun typecheck / app build / core tests | 0 | 30/30, build OK, 3578/8 |
| 2026-09-19 08:30 | s054 | docs | wrote versioning-strategy.md + rb-004 + DEC-037 | 0 | created |

## Implementation deliverable (FU-058, partial)

`opencode/packages/script/release.ts` implemented + verified:

- Computes `MAJOR.MINOR.PATCH-fork.<N>[-dev|-beta.<M>]` from `packages/opencode/package.json` version.
- Emits `OPENCODE_VERSION` env consumed by `@opencode-ai/script` `Script.version` → compiled into binary.
- Modes: `--channel dev|beta|stable`, `--bump`, `--sync-upstream`, `--dry`, `--json`. Typecheck clean.
- `build-linux.sh [dev|beta|stable]` wired to derive `OPENCODE_VERSION` from the tool.

### Critical finding (overrides naive DEC-037)

`OPENCODE_CHANNEL` doubles as the SQLite DB filename suffix (`packages/core/src/database/database.ts`:
`opencode-<channel>.db`, with `latest|beta|prod` → shared `opencode.db`). The fork must **always** keep
`OPENCODE_CHANNEL=mark-dev` → `opencode-mark-dev.db`. Fork channel semantics (`dev`/`beta`/`stable`) moved into the
**version string only**. Shipping a build with channel `beta`/`latest` would silently point at a different/empty DB.

### Files

- Fork repo: `opencode/packages/script/release.ts` (new, uncommitted on `dev`, HEAD `cbfc738`).
- Control-center: `50-projects/p003-opencode-fork/scripts/build-linux.sh` (wired), docs updated.

## Close-out

- Strategy + tool implemented. Follow-up FU-058 open: first `beta.1` cut + `/api/health` verify + tag.
