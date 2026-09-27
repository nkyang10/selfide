# s076 — FE-023 Admin settings (server-global) + FE-024 exe web auto-start — CODE COMPLETE, gates green, NOT built/deployed

- **Date:** 2026-09-27 (UTC)
- **Owner:** agent (user: mark)
- **Trigger:** user — "so continue?" after the s074 plan and the s075 rejection of s072.
- **Baseline:** fork `dev` = `cb67c4a`; the checkout also carries the **parallel session s073** WIP
  (`packages/app` timeline + `packages/ui` locales) — disjoint from every file below, and **not** mine.
- **Outcome:** ✅ FE-023 + FE-024 implemented across **12 code files + 62 locale files**, every gate green.
  **Not committed, not built, not deployed** — the live :4447 (pid 3654762) still runs the old binary, so the
  Admin tab and the new route exist only in source. Live verification + build is FU-093.

## What was built

Plan: `50-projects/p003-opencode-fork/notes/plan-admin-settings.md`. Two features, one coherent slice.

### FE-023 — Admin tab (server-global settings in the config file)

| Layer | File | What |
|---|---|---|
| schema | `packages/core/src/v1/config/server.ts` | new `server.webui.autoStart` (a `Webui` struct declared **before** `Server` — module-level TDZ) |
| route | `packages/opencode/src/server/webui.ts` (new) | `Webui.DefaultPort = 4446`, the port the Admin tab offers as the default |
| route | `.../httpapi/groups/global.ts` | `GET /global/webui` with a `GlobalWebui` schema (configuredPort / defaultPort / runningPort / runningHostname / autoStart / restartRequired) |
| route | `.../httpapi/handlers/global.ts` | the handler: **global** config only, running values from `Server.url` via a *deferred* dynamic import (avoids an import cycle with `server/server.ts`) |
| test | `.../httpapi-exercise/index.ts` | scenario for the new route (the `test:httpapi` gate fails on unexercised routes) |
| app | `packages/app/src/utils/server.ts` | `WebuiStatus` + `fetchWebuiStatus` — direct call, same Basic-auth pattern as `fetchProjectDirectories` |
| app | `packages/app/src/components/settings-v2/admin.tsx` (new) | the tab body: auto-start switch, port input + explicit **Save**, status line |
| app | `settings-v2/dialog-settings-v2.tsx` | `TabsV2.Trigger value="admin"` + `TabsV2.Content` (the category list is literal JSX, so a tab is exactly these two) |
| app | `settings-v2/settings-v2.css` | `.settings-v2-note` (the status line) |
| i18n | `packages/app/src/i18n/*.ts` | 14 new keys × **62 locales**, English source text (the FU-026/FE-019 pattern; AGENTS.md forbids inventing translations), inserted after `settings.models.title` by script, then `prettier` |
| docs | `packages/web/src/content/docs/config.mdx` | documents `webui.autoStart` |

### FE-024 — the exe starts the web UI

- `packages/opencode/src/cli/web-autostart.ts` (new) — `resolveAutoStart()` (the policy, pure) +
  `autoStartWebServer()` (binds and reports) + `networkURLs()`.
- `packages/opencode/src/cli/tui/worker.ts` — new `webuiAutoStart` RPC: reads the global config, resolves
  `port = --port || server.port || 4446`, binds through the worker's own listener ref (so `shutdown` stops it
  and the `--port` path keeps priority), and swallows failures with a log so a busy port cannot kill the TUI.
- `packages/opencode/src/cli/cmd/tui.ts` — calls the RPC after the transport is built and prints the URL +
  network URLs (and the "unsecured" warning) before the TUI takes the screen.
- `packages/opencode/test/cli/web-autostart.test.ts` (new) — 9 tests pinning the policy.

## Decisions taken (the plan's open questions)

- **D1 4446** — resolved the way s075 decided: **no** `Server.DefaultPort`. The compiled-in default stays
  upstream's 4096; **4446 is the value the Admin port row offers** (`Webui.DefaultPort`) and the value
  auto-start uses when the config sets none. Nothing in the *program* changed its default, so `web`/`serve`
  behaviour for anyone who never opens the Admin tab is untouched. DEC-050 as written (a config-schema default)
  was **not** implemented — see "Correction" below.
- **D2 v2-only** — the v1 settings page is dead code (toggle past its sunset, `useSettingsDialog()` hard-codes
  v2). Documented as a deliberate deviation in the fork `AGENTS.md` so a future agent does not "fix" it.
- **D3 auto-start default off** — `server.webui.autoStart` must be exactly `true`; unset means no listener.
  An upgrade never silently starts growing a socket.
- **D4 wildcard gated on a password** — `resolveAutoStart` refuses `0.0.0.0`/`::` when
  `OPENCODE_SERVER_PASSWORD` is unset, falls back to `127.0.0.1` and sets `downgraded`, which the TUI prints as
  a warning. (`web --hostname 0.0.0.0` unsecured already warns, but auto-start must not do that silently.)
- **D5 authenticated = admin** — no user/role model exists; the tab adds no privilege. Stated in the code and
  the docs rather than inventing an authz layer.
- **D6 busy-port honesty** — the status line distinguishes three states: running on the configured port /
  "restart to apply X" / "not set in the config file, running on Y".

## Traps hit (and how they were handled)

1. **`Webui` used before declaration** in the schema file — a module-level `const` referenced by an earlier
   `Schema.Struct` call is a TDZ error. Declared the struct first.
2. **Import cycle**: `server/server.ts` → `httpapi/server.ts` → routes → `server/server.ts`. The handler reads
   `Server.url` through `Effect.promise(() => import("@/server/server"))` (deferred), like the RSS route's
   comment about capturing services at layer-construction time.
3. **`Rpc.client.call` is not awaited inside the type**: `call` returns `Promise<ReturnType<T[M]>>`, so an
   `async` method types as `Promise<Promise<X>>`. Using `.then(result => result.started)` failed typecheck;
   `const result = await client.call(...)` is the correct form.
4. **`AppRuntime` has no `ServerAuth.Config`** in its requirements, so yielding it broke the worker's effect
   (`Type 'Config' is not assignable to type 'Service'`). The password check reads the same env flag the auth
   header uses (`Flag.OPENCODE_SERVER_PASSWORD`) — same meaning, no new requirement.
5. **The generated SDK types predate `server.webui`**, so the auto-start patch needed one cast with an
   `oxlint-disable-next-line` and a comment. The server schema accepted the key immediately; the SDK is
   regenerated separately (FU-092).
6. **A config write disposes every instance** (`handlers/global.ts:78-82`) → the port row saves on an explicit
   **Save** button, never on blur; and each patch sends **only the changed leaf** because arrays are replaced.
7. oxlint: the first pass had 1 warning on my own line (an unsafe `as Config`); the final pass is **0 warnings /
   0 errors on every new file** (the 8 remaining warnings across the touched set are all on pre-existing lines).

## Gates (all run from the package dirs, per the repo rules)

- `bun turbo typecheck` (repo root) → **30/30 successful**.
- app `bun run test:unit` → **774 pass / 0 fail** (111 files), including i18n **parity 5/5, 979 assertions**
  (all 62 locales carry the 14 new keys).
- `bun test test/cli/web-autostart.test.ts` → **9 pass / 0 fail**.
- `bun run script/httpapi-exercise.ts --mode coverage` → `global.webui` **PASS**; the run still ends with
  **3 pre-existing MISS** (`/api/skill/{name}` DELETE/POST, `/api/skill/{name}/enabled` — the FE-049 skills
  endpoints were added in s049 without exercise scenarios, so `test:httpapi` was already red before this work).
  Tracked as FU-094.
- oxlint on the 13 touched source/test files → **0 errors**; my new files are warning-free.
- The test file assertion `expect(result.url).toBe("http://0.0.0.0:4446")` first failed on a missing trailing
  slash — `URL.toString()` normalises it; fixed in the test, not in the code.

## Not done / next

- **No build, no deploy.** The web UI is embedded in the binary (`packages/opencode/script/build.ts`), so
  neither the Admin tab nor the route can be seen until `scripts/deploy-web-4447.sh --detach` runs — and that
  kills the listener this session is served by. FU-093, needs the user's OK.
- **No live check yet.** After a deploy, the things unit tests cannot see: the tab renders, saving the port
  writes `opencode.jsonc` **with comments intact**, the status line says "restart to apply", and the auto-start
  actually binds (test by setting `server.webui.autoStart: true` and starting a TUI/`opencode` with and without
  a password).
- **Not committed.** FU-093 also covers the commit; the s073 WIP must be staged around.
