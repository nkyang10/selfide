# s032 — Kickoff "pre-install" plugin (auto-creates global skills + seeds a starter skill)

- **Date (UTC):** 2026-09-14
- **User request:** "make skill auto-created as a kickoff of some pre-install skill that make
  opencode useful" — i.e. the global skill(s) should be **auto-created at opencode kickoff** so
  opencode is useful out of the box and the skills dir self-heals (opencode scans `~/.config/opencode/skills/`
  but never creates it — DEC-026).

## Approach

Used the **cleanest user-space kickoff hook** available in the fork: the **external plugin**
loader. It auto-loads `<config-dir>/{plugin,plugins}/*.{ts,js}` on every start — no fork rebuild,
no shared-source change.

### Source basis (p003 fork, `packages/`)
- `core/src/config/plugin/external.ts:58-70` — globs `{plugin,plugins}/*.{ts,js}` per configured dir
  and loads each as a plugin.
- `opencode/src/plugin/loader.ts` — legacy loader: resolve target → `import(entry)` → hand module to
  the caller's `finish`.
- `opencode/src/plugin/index.ts:88-124` — the **v1 plugin contract**: `export default` a **function**
  (`isServerPlugin = typeof value === "function"`), called `server(input, options)`; its return value
  becomes the plugin's hooks. `getLegacyPlugins` iterates module exports.
- `plugin/src/index.ts:56-66` — `PluginInput = { client, project, directory, worktree,
  experimental_workspace, serverUrl, $ }`. `$` = BunShell; `directory` = project dir.

So a function that does its work and `return {}` is the correct, supported shape.

## What the plugin does (idempotent + best-effort, never throws, never overwrites user files)

`~/.config/opencode/plugin/kickoff.ts` on **every opencode start**:
1. `mkdir -p ~/.config/opencode/skills/` — makes the global skill location **self-healing**
   (opencode itself only creates the base `~/.config/opencode/`, not the `skills/` subdir).
2. Seeds `~/.config/opencode/skills/starter-kit/SKILL.md` if absent — a "make opencode useful out of
   the box" onboarding skill: (a) real-data-first web research (Serper, self-loading key), (b) repo
   orientation, (c) safe defaults (read-only first, confirm destructive, log, record decisions),
   (d) verify.
3. Promotes the `web-research` skill (serper.py + SKILL.md) into the global dir if a source copy
   exists under `~/Desktop/{ide,gdx}/.opencode/skills/web-research` and the global copy is missing —
   so the real-data pipeline works in EVERY project.

## Verification

- **Load + invoke** (bun, simulating `server(input)`):
  - run 1: `skills dir: ok | starter-kit: created | web-research: present`
  - run 2 (idempotency): `skills dir: ok | starter-kit: present | web-research: present` — no overwrite.
- **Real loader proof**: started a fresh `opencode serve --port 4498` (official 1.18.23 binary), then
  `curl -u opencode:testpass http://127.0.0.1:4498/skill` → returned **`customize-opencode`**,
  **`web-research`**, and **`starter-kit`**. This proves the running loader picked up
  `~/.config/opencode/plugin/kickoff.ts` AND that the seeded skill is registered in the skill registry.
- **Cleanup**: test servers killed (0 remaining); production :4447 confirmed alive (unauth `/` → 401,
  auth gate intact).

## Files / evidence

- `~/.config/opencode/plugin/kickoff.ts` — the plugin (source of truth).
- `~/.config/opencode/skills/starter-kit/SKILL.md` — seeded by the plugin (starter kit).
- `~/.config/opencode/skills/web-research/` — global real-data skill (from s031).
- `40-knowledge/decisions-log.md` — **DEC-027**.
- `10-status/open-followups.md` — **FU-045** (resolved).
- `20-logs/command-log.md` — s032 rows.

## Remove anytime

- Remove the seeded skill: `rm -rf ~/.config/opencode/skills/starter-kit/` (plugin re-creates it next
  start unless you also remove the plugin).
- Remove the whole kickoff behavior: `rm ~/.config/opencode/plugin/kickoff.ts`.

## Notes / revisit

- The plugin runs for **both** the v1 runtime (the running :4447 fork) and the v2 `effect` runtime
  (the loader path in `external.ts`), so it works on official opencode and this fork alike.
- The starter-kit content is generic onboarding; if the user wants it project-specific, move the
  skill into the project's `.opencode/skills/` instead (a local copy overrides the global one).
