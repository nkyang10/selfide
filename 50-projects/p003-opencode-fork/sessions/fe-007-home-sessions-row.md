# FE-007 — Home Sessions-tab row: mobile-first multi-line card (s018)

2026-09-12 — implemented, typechecked, linted, unit-tested, built, deployed.
**Deployed** 0.0.0-dev-202609120534 (pid 305738) on http://192.168.1.249:4447/ (`testing/web-4447.log`).

## Goal
On the **home Sessions tab** (starting project/session picking page), refine the session row so it reads
well in a **mobile phone browser**: allow more than a single line per row and adopt a better row
structure for narrow viewports.

## Previous row (single-line strip) and its mobile problems
Before this change the row was a one-line horizontal flex with 4 columns:

```
[avatar] [project w-28 sm:w-40]  [title + prompt (all single-line truncate)]   [relative time w-16]
```

- The fixed **project column (112–160 px)** ate ~half of a ~360 px phone width, starving the title.
- Title and last-prompt were both `truncate` (single line), so long titles were cut and the prompt
  usually vanished entirely.
- Everything was crammed onto one line; nothing wrapped.

## New row (3-line mobile card) — semantics per line
```
   ┌avatar┐  Title (2-line clamp)                       [relative time top-right]
   │  ▸    │  ▸ project name (1-line, muted, folder icon)
   │       │  last-prompt preview (2-line clamp, faint; only when present)
```
- **Title** is the hero text: `flex-1`, clamped to **2 lines** (`-webkit-line-clamp:2` /
  `-webkit-box-orient:vertical`) so long titles wrap on mobile.
- **Relative time** moves to the **top-right**, top-aligned with the title row (width no longer
  reserves 64 px next to the text).
- **Project name** drops out of the fixed-width first column; it becomes a small muted **secondary
  line** under the title with the v2 **folder** icon, so it donates all its width back to the text and
  scales to any viewport. Single-line truncate.
- **Last prompt** (from FE-006 `sessionLastPrompt`) becomes a third line **clamped to 2 lines** so long
  previews wrap; only rendered when present.
- Row container switched from `items-center` to `items-start`; avatar top-aligned with the title line.

## Files
- `opencode/packages/app/src/pages/home/home-sessions-table.tsx` — `HomeSessionTableRow` markup only.
  No controller/schema change.

## Verification
- `bun run typecheck` (packages/app): pass.
- `bun x oxlint packages/app/src/pages/home/home-sessions-table.tsx`: 0 warnings / 0 errors.
- `bun run test:unit` (packages/app): 737 pass / 0 fail.
- Built with pinned bun **1.3.14** (DEC-015 — must not use 1.4.x) → `0.0.0-dev-202609120534`.
- Serve-check: binary grep finds new markup (`items-start justify-between gap-3`); server healthy, no
  errors in log. Login page active (FE-001), GET / → 401 redirect to /login as expected.

## Visual check on an actual phone
Not verified on a physical device this session. Suggested: open http://192.168.1.249:4447/ in the phone
browser, log in, go to the home **Sessions** tab, confirm long titles wrap to 2 lines, project name
shows under the title, and long last-prompt previews wrap to 2 lines.
