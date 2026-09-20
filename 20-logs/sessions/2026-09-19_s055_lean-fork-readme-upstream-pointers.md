# s055 — Lean fork README: strip upstream dup, point to upstream, highlight differences

**Date:** 2026-09-19 (UTC) **UTC timestamp:** 2026-09-19 09:08
**Trigger:** user asked to remove duplicate content that is just upstream info from the readme/other docs,
reference users to upstream, and highlight the differences/improvements from upstream.
**Result:** ✅ DONE — 24 files changed (net −2,587 lines), **committed `cbfc738` + pushed to `origin/dev`**
(user asked).

## Scope (confirmed with user via question)

- **README.md:** rewrite as a short fork README (not keep-full-upstream + diff).
- **21 translated `README.<lang>.md`:** replace with a short pointer to the English README + upstream
  (not delete, not full translation).
- **Other inherited docs:** "professional practice of forking a public project" (user's words) → keep
  functional docs, add fork/upstream notices where informational, preserve attribution (LICENSE).

## What was changed (24 files, +207 / −2,794)

- **`README.md`** — full rewrite. Now: MarkCode logo + tagline ("A mobile-first fork of opencode"), a
  **"This is a fork"** callout pointing to upstream for install/CLI/desktop/integrations/plugins/docs, a
  **"What's different from upstream"** section (the fork's real deltas), **"Install & run"** (upstream
  standard install + MarkCode web-UI flag + self-built aarch64 binary build), **"Upstream"** links, and a
  **License** note (MIT, © opencode authors). Removed: upstream install/quickstart/CLI/desktop/integrations/
  services/plugins/funding/build/contributors sections, the Discord/npm/build badges, and the language-links
  block.
- **21 × `README.<lang>.md`** — each replaced with an identical 5-line pointer: "MarkCode is a mobile-first
  fork of opencode → see English README.md → upstream opencode.ai".
- **`CONTRIBUTING.md`** — added a **Fork notice** block after the title (this repo = MarkCode fork; PRs to
  `nkyang10/opencode` dev; upstream → `anomalyco/opencode`).
- **`SECURITY.md`** — added a **Fork notice** block (policy inherited from upstream; fork issues → fork
  maintainers).

## What was deliberately NOT changed (professional-fork practice)

- **`AGENTS.md`** — already fork-aware (has a "## This fork" section, correct `nkyang10/opencode` origin);
  functional for the build. Left as-is.
- **`CONTEXT.md`** — accurate upstream technical reference ("OpenCode Session Runtime"); still correct in
  the fork. Left as-is.
- **`STATS.md` + `script/stats.ts`** — `STATS.md` is **generated** by `script/stats.ts` (line 126
  `const file = "STATS.md"`) and is pure upstream opencode download stats (2025-06→2026-01). Left as-is
  (removing could affect forked tooling; it's generated data, not a prose doc). **Flagged to user** as a
  candidate for removal if desired.
- **`LICENSE`** — kept (MIT, © opencode). Attribution preserved — correct for a fork.

## The "differences from upstream" now highlighted (source: p003 project record)

Mobile-first UI (Sessions cards FE-007, last-prompt subtitle FE-006, folder explorer on mobile FE-004,
drag-down menu FE-009, draft-tab context menu FE-012, Zag.js TreeView picker FE-013) · Auth (login page +
cookie auth FE-001) · Reliability (foreground re-sync FE-003, project-selector crash fix FE-002, slim
live-reply FE-011) · Dev tooling (DEV dropdown FE-014, refresh toast FE-015) · Build (self-built Linux
aarch64 binary) · plus the MarkCode rebrand (s053, commit f094279).

## Verification

- `git diff --stat`: 24 files; README.md 179 chg; each translation −134; CONTRIBUTING +5; SECURITY +4.
- README.md anchor `#whats-different-from-upstream` matches its `##` heading (line 27).
- All 21 pointers byte-identical (md5 unique count = 1); no upstream "Quick start" markers left in them.
- Assets referenced exist (logo SVGs, screenshot.png, LICENSE).

## Committed + pushed (user requested)

- Committed `cbfc738` "docs: lean fork README — point to upstream, highlight MarkCode differences"
  (24 files, 207+/2794−) and pushed to `origin/dev` (`f094279..cbfc738`). Pre-push typecheck 30/30.
- Only the 24 doc files were staged; s054's untracked `packages/script/release.ts` was intentionally left
  out (belongs to the versioning work, FU-058).

## Remaining follow-up

- **FU-060:** decide on `STATS.md`/`script/stats.ts` (remove vs keep vs pointer) — left as-is here.
