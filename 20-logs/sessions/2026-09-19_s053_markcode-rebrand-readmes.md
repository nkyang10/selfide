# s053 — Rebrand fork READMEs: OpenCode → MarkCode (all language variants)

**Date:** 2026-09-19 (UTC) **UTC timestamp:** 2026-09-19 08:35
**Trigger:** user asked to update "the md/doc that will commit to GitHub" so the project name is
**MarkCode** (official name), i.e. change "opencode" → "MarkCode".
**Result:** ✅ DONE — edits applied, verified, **committed `f094279` + pushed to `origin/dev`** (user asked).

## Scope decision (confirmed with user via question)

- **Rename scope:** *Branding only.* Change product-name mentions (logo alt, tagline prose, headings,
  "OpenCode includes…", "configure OpenCode", "Building on OpenCode", "the OpenCode team") to `MarkCode`.
  **Keep** functional references unchanged: install commands, URLs (`opencode.ai`), the npm package
  (`opencode-ai`), GitHub repo (`anomalyco/opencode`), CLI commands, and example names
  (`opencode-dashboard`, `opencode-mobile`).
- **Files:** **all** language READMEs in the fork (not just `README.md`).

## Key finding (why the edit is safe)

In every `README*.md` the casing cleanly separates the two:
- `OpenCode` (capital O) **only** appears as the **product name** (prose, headings, alt text).
- `opencode` (lowercase) **only** appears as **functional** refs (URLs, `opencode-ai`,
  `anomalyco/opencode`, CLI commands, example names).

So a **case-sensitive** `OpenCode` → `MarkCode` rename touches only branding and cannot break any
install/link/package reference. No Chinese/Cyrillic-script renderings of the brand existed — the name
is kept in Latin script in all translations.

## What was changed

- 22 files: `README.md` + 21 translated `README.<lang>.md` in
  `50-projects/p003-opencode-fork/opencode/`.
- 177 insertions / 177 deletions (8 name mentions per file; `zh` had 6 — its translation omits the
  brand in a couple of sections; `bs`/`uk`/`zht` had 9).
- Changed: logo `alt="OpenCode logo"` → `alt="MarkCode logo"`; screenshot alt
  `OpenCode Terminal UI` → `MarkCode Terminal UI`; "OpenCode is also available as a desktop
  application" → "MarkCode …"; "OpenCode includes two built-in agents" → "MarkCode …"; "configure
  OpenCode" → "configure MarkCode"; "contributing to OpenCode" → "contributing to MarkCode";
  "### Building on OpenCode" → "### Building on MarkCode"; "the OpenCode team" → "the MarkCode team".
- **Preserved (unchanged):** every `https://opencode.ai…` URL, `github.com/anomalyco/opencode…`,
  `npm i -g opencode-ai@latest`, `curl … opencode.ai/install`, `scoop install opencode`,
  `choco install opencode`, `brew install opencode`, `npx opencode-ai`, `opencode auth login`,
  `opencode --version`, `bun create opencode`, and the example names `opencode`/`opencode-dashboard`/
  `opencode-mobile`.

## Evidence

- `grep -rn "OpenCode" README*.md` → **no matches** (all product-name mentions renamed).
- `grep -rc "opencode" README*.md` → 28 per file (functional refs intact).
- `grep -rc "MarkCode" README*.md` → 8 per file (6 in `zh`, 9 in `bs`/`uk`/`zht`).
- `git diff README.md` + `git diff README.zh.md` reviewed line-by-line: only name mentions changed.
- Fork working tree: 22 files modified, nothing else.

## Committed + pushed (user requested)

- Committed `f094279` "docs: rebrand OpenCode → MarkCode in READMEs (all languages)" (22 files,
  177+/177-) and pushed to `origin/dev` (`https://github.com/nkyang10/opencode.git`).
- Note: the fork's husky **pre-push** hook runs `bun turbo typecheck`; `bun` is not on the default git-hook
  PATH. Fix: push with `PATH="$HOME/.bun/bin:$PATH"` (bun lives at `~/.bun/bin/bun`, v1.4.2 vs expected
  1.3.14 — a benign warning). Typecheck passed 30/30 (all cached). Push: `9ebb0b3..f094279 dev -> dev`.

## Out of scope (user chose READMEs only)

- Product-name mentions in **other** committed docs (e.g. `CONTRIBUTING.md`, `AGENTS.md`, `CONTEXT.md`)
  still say OpenCode. If the brand should extend there, re-apply the same casing rule per file.
