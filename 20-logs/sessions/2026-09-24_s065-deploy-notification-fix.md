# s065 — Deploy-notification fix (FE-015): version uniqueness + reconnect detection

- **Date:** 2026-09-24
- **Session:** s065
- **Focus:** "opencode fork why i didn't get deploy notification from ajax update"

## Report

User asked why the FE-015 server-update Refresh toast didn't fire after an AJAX-driven deploy.
Investigation across the fork's app + release tooling surfaced the mechanism and two root causes.

### Root-cause analysis (FE-015 deploy Refresh toast)
- Toast fires in `packages/app/src/components/server-update-refresh.tsx` only on a **health-version diff**
  (`/api/health` → `{healthy, version}`, handler `server/routes/.../global.ts:67`). An AJAX/SSE update
  alone never triggers it; it needs `health.version` to change between polls.
- Dev channel version came from `packages/script/release.ts` `devDateVersion()` → `1.0.YYYYMMDD-N` where
  `N` is a **gitignored, machine-local** counter (`packages/script/state/dev-version.json`). On a build
  on another machine (or a same-day counter reuse), `N` resets/coincides → identical version → no toast.
- The old component also compared **version only**, so a redeploy that doesn't change the version string
  never prompted a refresh even though the server clearly restarted.

### Fixes applied (uncommitted in fork `dev`)
1. **Global version uniqueness** — `release.ts` dev channel now emits `1.0.YYYYMMDD-N-HHHH` where `HHHH` is
   a time-millis + entropy suffix from a new `buildUniqueSuffix()`. Every build is unique even if the
   per-day counter resets or another machine starts at `-01`. Updated the `--bump`-incompatible error
   string to match.
2. **Reconnect detection** — `ServerUpdateRefresh` now tracks per-server `{version, up}`. It toasts not
   only on a version diff but also when a previously-seen healthy server drops and recovers (deploy
   restart), even with the same version. Baseline first poll never toasts.

## Verification
- `tsgo -b` app: clean (exit 0).
- `bun build` app production bundle: success (built in ~15 s).
- `bun build release.ts`: OK (syntax/imports).
- Suffix uniqueness probe: 5000 distinct versions even with counter pinned at `01` (parallel/multi-machine
  simulation); well-formed `1.0.YYYYMMDD-N-HHHH`.

## Results / evidence
- Modified: `packages/script/release.ts`, `packages/app/src/components/server-update-refresh.tsx`
  (inner fork repo, uncommitted).
- Fork README FE-015 summary updated (outer `ide` repo).

## Follow-ups
- FU-s065: commit + push both files to fork `origin/dev`; rebuild + redeploy :4447; verify toast on a
  same-day redeploy and on an unchanged-version restart. (owner: agent/user)
