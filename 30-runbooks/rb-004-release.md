# rb-004 — OpenCode fork release (cut a beta/stable build)

> Companion to `40-knowledge/versioning-strategy.md` (DEC-042, supersedes DEC-037). Carries build gates + tags + notes.

## When

- A feature milestone is verified on `dev` and deserves a stable identifier.
- Upstream merged a significant baseline worth freezing behind a tag.

## Prereqs

- Fork repo at `50-projects/p003-opencode-fork/opencode`, on a clean `dev` tree.
- `bun` on PATH (`export PATH="$HOME/.bun/bin:$PATH"` if needed).
- `upstream/dev` fetched; decision made whether to sync first (see strategy §3.4).

## Steps

1. **Gate check** on the exact commit to release:
   ```bash
   bun run typecheck          # expect 30/30 tasks pass
   bun run --cwd packages/app build   # web UI builds
   bun run --cwd packages/opencode test --timeout 30000   # expect ~3600 pass, ignore known env/locale fails
   bun install --frozen-lockfile      # lockfile intact
   ```
2. **Optional sync** (only on the `dev` line, never rebase the fork counter):
   ```bash
   git fetch upstream && git merge --no-ff upstream/dev
   ```
3. **Cut the version** (via `packages/script/release.ts` — DEC-042 unified `1.<MAJOR>.<YYYYMMDDHHMMSS>`):
   ```bash
   # preview (no write) — prints 1.<MAJOR>.<UTC-ts> for each channel:
   bun packages/script/release.ts --channel dev --dry --json
   # first candidate: roll beta (increments MAJOR counter)
   bun packages/script/release.ts --channel beta --bump   # 1.<MAJOR+1>.<ts>
   # stable promotes (increments MAJOR counter again)
   bun packages/script/release.ts --channel stable --bump # 1.<MAJOR+1>.<ts>
   ```
   `.env` emitted by the tool always keeps `OPENCODE_CHANNEL=mark-dev` — never change it (SQLite DB suffix).
4. **Build + verify** (control-center helper wires release.ts → OPENCODE_VERSION):
   ```bash
   50-projects/p003-opencode-fork/scripts/build-linux.sh beta   # or dev (default)
   # confirm `/api/health` reports the new version on the deployed instance
   ```
5. **Tag & push**:
   ```bash
   git tag v<version>
   git push origin <release-branch> v<version>
   ```
6. **Log + announce**:
   - Update `10-status/current-state.md` (deployed version + PID), `20-logs/command-log.md`.
   - Record upstream divergence in the release notes (e.g. "carried: FE-0xx…", "vs upstream v1.x.y").

## Notes / known pitfalls

- Known 8 test failures at s054 are env/locale-driven (Chinese locale help-snapshots, umask file mode, missing `node`
  for azure, upstream install-message mismatch, `/status` 404 test) — do NOT block a release; open `20-logs/incidents/`
  only if a NEW failure appears.
- `OPENCODE_CHANNEL` MUST remain `mark-dev` (DB isolation). Fork channel/version lives in `OPENCODE_VERSION` only.
- Desktop packaging must run with `OPENCODE_VERSION` set (so `prepare.ts` + renderer `VITE_APP_VERSION` inherit the
  unified `1.<MAJOR>.<ts>`).
- First release after this runbook: confirm `/api/health`, webui Settings "v…", and desktop About all show the same
  `1.<MAJOR>.<ts>` before tagging.
