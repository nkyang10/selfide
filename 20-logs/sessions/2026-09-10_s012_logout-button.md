# Session s012 — Logout button on project selection page

- **Date:** 2026-09-10 (UTC)
- **Focus:** p003-opencode-fork FE-999
- **Goal:** Add a logout button ABOVE the settings button in the project selection (home) page sidebar

## Context

The opencode fork (p003) already has cookie-auth login (FE-001) and a `/logout` server endpoint
(`packages/opencode/src/server/shared/login.ts#logout`) that clears the auth cookie and 302-redirects to
`/login`. The project-selection page sidebar nav (`HomeUtilityNav` in `home-projects-view.tsx`) only had a
Settings and a Help button. No logout entry existed in the UI.

## Changes (all in `p003-opencode-fork/opencode/`)

1. `packages/ui/src/v2/components/icon.tsx` — added a `log-out` 16×16 icon (arrow out of a door) to the
   `icons` map.
2. `packages/app/src/pages/home/home-projects-view.tsx` — added a Logout button as the FIRST item in
   `HomeUtilityNav` (above Settings). On click it shows a `window.confirm` and, if confirmed, navigates
   to `/logout` (clears cookie + redirects to login page). Reuses `HomeProjectNavButton` styling.
3. `packages/app/src/i18n/en.ts` — added `sidebar.logout` and `sidebar.logoutConfirm` keys. Other locales
   fall back to English via the base-merge in language.tsx, so no need to touch 65 files.

## Verification

- `bun run --cwd packages/app typecheck` (tsgo -b): clean
- `bun run --cwd packages/ui typecheck` (tsgo --noEmit): clean
- `bunx oxlint` on the 3 touched files: 0 errors (4 pre-existing warnings)
- Repo-wide `bun run lint` has 1 pre-existing unrelated error in `.opencode/plugins/tui-smoke.tsx` (not ours).

## Evidence

- Diff paths above; git d/f in the nested fork repo pending user confirmation to build/commit.
