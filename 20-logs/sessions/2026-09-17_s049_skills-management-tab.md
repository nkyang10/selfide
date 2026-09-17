# Session s049 — Skills management tab

**Date:** 2026-09-17
**Project:** p003-opencode-fork
**Agent:** opencode controller

## Scope
New web-UI feature: add a "Skills" tab to the home page that lists all skills
(name + location links) and per-row action icons: edit, copy-to-clipboard,
enable/disable, delete. Sorted alphanumerically by name.

Design decisions (confirmed with user):
- **Full feature**: list + all four actions (edit/delete/enable all have server write endpoints).
- **Edit** = inline editor embedded in the Skills tab (not a separate route).
- **Enable/disable** = marker-file rename: disable renames `<dir>/SKILL.md` →
  `<dir>/.SKILL.md.disabled` (and back), so discovery pattern `**/SKILL.md` skips it.

## Architecture findings (this fork)
- Two skill services exist:
  1. `core/skill` (`SkillV2`) — source-based; `GET /api/skill` via `SkillGroup`
     (protocol) + `SkillHandler` (server). This is what the v2 SDK exposes.
  2. `opencode/src/skill` (`Skill.Service`) — disk-discovery (`.opencode/skills`,
     `.claude/skills`, `.agents/skills`, project skills, built-in). This is the
     real agent skill source the user manages.
- The web UI SDK (`v2.skill`) currently hits `SkillV2` via `/api/skill`.
- For management we extend the **protocol `SkillGroup`** with write endpoints and
  wire the handler to the real disk service.

## Files touched
Server/core:
- `packages/schema/src/skill.ts` — add `enabled?: boolean` to `SkillV2.Info`.
- `packages/core/src/skill.ts` — disabled-marker detection, new `update` / `setEnabled` / `remove`
  methods + `InvalidError`; extension of the `SkillV2` service interface.
- `packages/protocol/src/groups/skill.ts` — new endpoints `skill.update` (POST /api/skill/:name),
  `skill.setEnabled` (POST /api/skill/:name/enabled), `skill.remove` (DELETE /api/skill/:name),
  with `error: [InvalidRequestError, UnknownError]`.
- `packages/server/src/handlers/skill.ts` — implement new handlers with `Effect.mapError` mapping
  to protocol errors.
- `packages/client` + `packages/sdk/js` — regenerated clients to expose the new endpoints.
- `packages/core/test/skill.test.ts` — updated expectations for `enabled: true`; added an `it.live`
  test covering update/enable/disable/remove on real disk.

App (web UI):
- `packages/app/src/pages/home.tsx` — added third "Skills" tab via `Switch/Match`.
- `packages/app/src/pages/home/home-skills-controller.tsx` (new) — `useQuery` list + mutations.
- `packages/app/src/pages/home/home-skills.tsx` (new) — skill rows (name + location) with edit /
  copy / toggle-enable / delete actions + inline text editor.
- `packages/app/src/i18n/en.ts` + all ~61 app locale files — `home.skills.*` strings (en+fallback;
  parity test green).

## Commands
see 20-logs/command-log.md

## Outcome
Implemented and verified:
- `get`/`update`/`setEnabled`/`remove` on `SkillV2` (core service) operate directly on disk
  (SKILL.md files). Disabled skills are renamed to `<dir>/.SKILL.md.disabled`; they still surface
  in the list (with `enabled:false`) and can be re-enabled. `list()` discovers both active and
  disabled files.
- Protocol + server handlers wired; both the effect client (`@opencode-ai/client`) and the
  hey-api SDK (`@opencode-ai/sdk`) regenerated; app typecheck/build pass.
- Note: management scope == whatever `GET /api/skill` returns (SkillV2 directory sources:
  `.opencode/skills` + configured skills dirs), which is the existing web-API surface (a
  *different* skill system from the agent's `@/skill` disk discovery). The tab does NOT touch
  `.claude/skills` / per-project SKILL.md discovery.
- `packages/opencode` typecheck fails ONLY on pre-existing WIP in `src/installation/index.ts`
  (not touched by this work).

## Follow-up session (same date): merge exploration + REVERT
After FU-056 shipped (committed `fefa8eb`, `f21cdd9`, pushed to origin/dev, live on :4447 build
`0.0.0-mark-dev-202609170400`), the user asked to **merge all agent-skill discovery into
`/api/skill`** but show skills from other agent systems (`.claude/skills`, project dirs) as
**read-only** (hide icons, no modification). Trial added (all **uncommitted**):
- `packages/schema/src/skill.ts`: `Info.editable?`, `RecordSource` in `Source` union.
- `packages/core/src/skill.ts`: `record` load handling, read-only guards on
  update/setEnabled/remove, `mergeReadonly(infos)` (sig `Effect<void, never, Scope>`).
- `packages/opencode/src/server/routes/instance/httpapi/server.ts`: `skillDiscoveryMergeLayer`
  (L192-199) wired into `serverRoutes` (L183) via `Layer.provideMerge(Skill.node)`.

Blocking finding: schema changes ripple into the **generated SDK** — `SkillV2Source`
(`packages/sdk/js/src/v2/gen/types.gen.ts:3036` = Directory | Url | Embedded, no `record`) gates
`SkillDraft.source` in `packages/plugin/src/v2/effect/skill.ts`, so core typecheck failed on
`host.ts:214` (a "should-be-stale" SDK regen dependency), plus test file mismatches
(`test/config/skill.test.ts:39`, `test/plugin/skill.test.ts:15`, `test/tool-skill.test.ts:61`
missing `mergeReadonly` mock). Also unresolved scope risk: `SkillV2.Service` is a location node
resolved in a static startup layer.

**User re-scoped** ("original feature is only about view + edit skill.md") → reverted:
`git checkout -- packages/core/src/skill.ts packages/schema/src/skill.ts
packages/opencode/src/server/routes/instance/httpapi/server.ts`. Tree clean. Verified after revert:
core typecheck (forced) clean, skill tests 4/4, i18n parity 5/5 (979 expects), home tests 6/6,
live `/api/skill` GET returns `customize-opencode`. No redeploy needed (tree == deployed baseline).
Entirety recorded in `40-knowledge/decisions-log.md` DEC-033; nothing merge-related remains in code.

## Follow-ups
- LOCALE PARITY — DONE, see FU-056: `home.skills.*` keys parity across ~61 locales verified green
  (5 pass / 979 expects).
- Revisit DEC-033 if user later wants `.claude/skills`/project skills surfaced read-only on the
  tab: re-apply merge machinery + SDK/OpenAPI regen.
