# Session s057 — Close DEC-033 re-apply enhancement

**Date:** 2026-09-19
**Project:** p003-opencode-fork
**Agent:** opencode controller

## Scope
User asked to pick up "previous skill list task" = re-apply the DEC-033 read-only
merge (fold `.claude/skills` + per-project skills into `/api/skill` as read-only
rows, `editable:false`, no edit/delete icons).

I reviewed current code (`packages/core/src/skill.ts`, `packages/schema/src/skill.ts`)
and confirmed the merge is **not** present — DEC-033 reverted it (uncommitted).

User then decided: **close this enhancement instead**, and open another task.

## Outcome
- Enhancement (read-only merge re-apply) **closed / deferred indefinitely** — fully
  aligned with DEC-033's original revert.
- No code changed. Baseline is clean: `Source = DirectorySource | UrlSource | EmbeddedSource`,
  `Info` has `enabled?` only (no `editable`), no `record` source, no merge/read-only guards.

## Follow-up
- Next user task to be opened separately ("I will open another").
- If the merge is ever revisited, reference DEC-033's re-apply checklist (schema →
  core → server discovery layer → SDK/OpenAPI regen → app UI) plus the
  per-location `SkillV2.Service` scope question.
