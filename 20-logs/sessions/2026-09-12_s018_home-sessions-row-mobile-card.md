# s018 — FE-007: Home Sessions-tab row redesigned as mobile-first multi-line card (2026-09-12)

## Scope
On the starting project/session picking page (home **Sessions** tab), redesign the session row so it
works well in a mobile browser and supports more than a single line per row. The user asked to "learn
from our perspective" and suggest a better row structure.

## Changes
- `opencode/packages/app/src/pages/home/home-sessions-table.tsx` — `HomeSessionTableRow` markup only.

New row structure (3-line stacked card, `items-start`):
1. **Title** (`flex-1`, **2-line clamp**) + **relative time top-right** (no fixed 64px width next to text).
2. **Project name** (previously a fixed `w-28 sm:w-40` column) → small muted **line under the title**
   with the v2 **folder icon**; single-line truncate.
3. **Last prompt** (FE-006 `sessionLastPrompt`) → third line, **2-line clamp**, only when present.

Container switch `items-center` → `items-start`; avatar top-aligned with title line.

## Verification
- `bun run typecheck` (packages/app): pass.
- `bun x oxlint .../home-sessions-table.tsx`: 0 warnings / 0 errors.
- `bun run test:unit` (packages/app): 737 pass / 0 fail.
- Built with pinned bun **1.3.14** (DEC-015) → binary `0.0.0-dev-202609120534`.
- Deployed: killed old pid 248812, started new pid **305738** on `http://192.168.1.249:4447/`
  (`testing/web-4447.log`, no errors). Login page active (FE-001).
- Grepped binary for new markup (`items-start justify-between gap-3`): present → change is compiled in.

## Deliverables
- p003 session note: `50-projects/p003-opencode-fork/sessions/fe-007-home-sessions-row.md`
- Deployed build live at http://192.168.1.249:4447/ (pid 305738; version 0.0.0-dev-202609120534).

## Follow-ups
- Visual check on a physical phone (FU-028 area) to confirm wrapping/readability.
