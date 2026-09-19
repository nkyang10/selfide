# Versioning Strategy — p003 opencode fork

> Status: ✅ DECIDED (DEC-037). Companion: `30-runbooks/rb-004-release.md` for the step-by-step.
> Scope: the fork at `50-projects/p003-opencode-fork/opencode`, upstream = `anomalyco/opencode` (`upstream/dev`),
> origin = `nkyang10/opencode` (`dev`).

## 1. Problem being solved

The fork currently ships builds stamped `0.0.0-mark-dev-<timestamp>` (date-only), while `package.json` still carries
upstream's `1.18.31`. Consequences:

- No way to tell *which feature branch / divergence level* a build contains — timestamps alone don't encode
  upstream-relative position or channel.
- No stable identifiers for rollouts, rollbacks, or cross-machine sync (a build can't be "known good").
- Upstream releases will keep advancing the `package.json` baseline, so the fork needs a bump policy.

## 2. Goals

1. **Unambiguous artifact identity** — every build must be traceable to (a) upstream base, (b) fork commit, (c) channel.
2. **Simple + human-writable** — no heavy release tooling; a one-line script or tag suffices.
3. **Channel-aware** — dev vs beta vs stable are explicit, not accidental.
4. **Zero-surprise sync** — merging upstream must never silently change the fork's own release number.

## 3. The strategy

### 3.1 Version number → **SemVer + fork marker** (intel SemVer)

Adopt **`MAJOR.MINOR.PATCH-fork.<N>`** at the package level:

    <upstream.MAJOR>.<upstream.MINOR>.<upstream.PATCH>-fork.<N>

Example: upstream is at `1.18.31`, this is the 12th fork release → `1.18.31-fork.12`.

- `MAJOR.MINOR.PATCH` always mirrors the **upstream baseline** (never our own invention).
- `-fork.<N>` is our fork release counter, **monotonic**: never reset, never reused.
- Timestamp becomes **build metadata** only: `1.18.31-fork.12+20260919-0830`.

### 3.2 Channel = suffix on the release line

Three channels, one monotonic counter:

| Channel | Version when published | Branch | Tag |
|---|---|---|---|
| `dev` | `1.18.31-fork.12-dev` (float, not released) | `dev` | — |
| `beta` | `1.18.31-fork.12-beta.<N>` | `release/beta` | `v1.18.31-fork.12-beta.<N>` |
| `stable` | `1.18.31-fork.12` | `release/stable` | `v1.18.31-fork.12` |

- The **fork.`<N>` build number increments once per release train** — beta.1, beta.2 → stable. No separate counters.
- `dev` never gets cut-numbered; it floats as `.dev` and is equivalent to "bleeding edge."

### 3.3 Where the version lives

- **Source of truth:** `package.json` (`version` field) in the fork repo — bumped by `packages/script/release.ts`,
  mirroring upstream MAJOR.MINOR.PATCH and adding `-fork.<N>`. Versions are kept in lockstep across
  `packages/opencode`, `packages/app`, `packages/desktop`.
- **Build-stamped value:** `OPENCODE_VERSION` env (defined in `release.ts` output) → picked up by
  `@opencode-ai/script` `Script.version` → compiled into the binary via `build.ts` as `OPENCODE_VERSION`.
- **CRITICAL — channel ≠ DB channel:** `OPENCODE_CHANNEL` doubles as the SQLite filename suffix
  (`opencode-<channel>.db`, `packages/core/src/database/database.ts`). For DB isolation the fork **must keep
  `OPENCODE_CHANNEL=mark-dev`** always (data lives in `opencode-mark-dev.db`). Fork release-channel semantics
  (`dev`/`beta`/`stable`) live **only in the version string** (`-dev`/`-beta.<M>`/bare), never in `OPENCODE_CHANNEL`.
  Shipping a build with `OPENCODE_CHANNEL=beta`/`latest` would silently point at a different/empty DB.
- **No hardcoding:** unknown places that print `0.0.0-dev-*` are to be drained to the single source. The fork's
  build helper `50-projects/p003-opencode-fork/scripts/build-linux.sh` now calls `release.ts` to produce
  `OPENCODE_VERSION` (`./scripts/build-linux.sh [dev|beta|stable]`).

### 3.4 Sync policy

- Sync upstream **on the `dev` line** (already the case). Merge `upstream/dev` → `dev`; keep the merge commits.
- **Never** `git rebase` the fork counter onto upstream — `fork.<N>` stays monotonic.
- When upstream bumps MAJOR/MINOR in `package.json`, drop the fork suffix and re-add `.fork.<N>` on the new base
  (e.g. upstream `1.19.0` → `1.19.0-fork.13`). The `<N>` never resets.
- Document upstream divergence in the release notes vs upstream tag (e.g. "carried: FE-0xx …").

### 3.5 Releasing (summary)

1. Freeze `dev`, run full gate (typecheck + app build + core tests) on the exact commit.
2. Create `release/stable` branch (or promote `beta`).
3. `bun run script/release.ts stable` → bumps `package.json`, stamps build, writes `CHANGELOG` entry.
4. Build artifacts, tag `v<version>`, push branch + tag to `origin`.
5. Update control-center `10-status/current-state.md` + `40-knowledge/decisions-log.md`.

## 4. Migration path (current → target)

No big bang. Order of steps:

1. ~~Add `script/release.ts` (bump + stamp + changelog skeleton) — FU-055.~~ **DONE (s054):**
   `packages/script/release.ts` implemented; verified across `dev`/`beta`/`stable` + 
   `--bump`/`--sync-upstream`/`--dry`/`--json`; typechecked.
2. **DONE (s054):** `build-linux.sh` wired to derive `OPENCODE_VERSION` from `release.ts`
   (`./scripts/build-linux.sh [dev|beta|stable]`), channel stays `mark-dev` for SQLite isolation.
3. Confirm an actual build stamps the fork version (next deploy) and is shown in `/api/health`.
4. First real cut: `beta.1`, verify in the UI health endpoint + sessions list, then promote to `stable`.
5. Retro-tag historical goodwill builds if ever needed (optional).

## 5. Alternatives rejected

- **Pure date versioning (status quo).** Rejected: no channel/divergence/rollback signal; kept at most as metadata.
- **Full SemVer on top of upstream (e.g. `18.x.0` fork-own MAJOR).** Rejected: conflates fork releases with upstream
  divergences; makes upstream tracking hard to read.
- **Git sha as the only identifier.** Rejected: same artifact from same sha can be beta or stable; no promotion story.
- **CalVer `MAJOR.YYYY.MM`.** Rejected: no incremental patch/rollback granularity, no upstream-relative clarity.
- **Changesets/lerna tooling.** Rejected: heavyweight for a single-maintainer fork; a 150-line script suffices.

## 6. Consequences / revisit when

- The fork counter `<N>` must be maintained by the release script only — never hand-edited twice.
- Test failures that are **env/locale-driven** (8 known at s054) must not block a cut; they are tracked separately.
- Revisit if: upstream adopts changesets AND we want upstream PRs auto-versioned; or if the fork ever needs to publish
  independently to a registry (then `-fork.X` → own MAJOR).

## 7. Decision record

### DEC-037 — Fork versioning: `MAJOR.MINOR.PATCH-fork.<N>` SemVer + channels (2026-09-19)
- **Decision:** Adopt intel SemVer `MAJOR.MINOR.PATCH-fork.<N>[-channel]`; upstream base mirrored in MAJOR.MINOR.PATCH,
  monotonic `fork.<N>` release counter, timestamp as build metadata; 3 channels `dev`/`beta`/`stable`; release gates =
  typecheck + app build + core tests; sync policy = merge upstream into `dev` only, never rebase the counter.
- **Rationale:** unambiguous artifact identity across machines/channels, upstream-trackable, scriptable, no tooling debt.
- **Alternatives rejected:** date-only, fork-own MAJOR, sha-only, CalVer, changesets (see §5).
- **Consequences / revisit when:** implement `script/release.ts` (FU-055); revisit if upstream adopts changesets or fork
  needs independent registry publishing.
