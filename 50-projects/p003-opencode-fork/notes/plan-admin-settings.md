# Plan — FE-023 Admin settings (server-global) + FE-024 web-UI auto-start from the exe

> **Status:** PLAN ONLY — no code written for FE-023/024. Prepared 2026-09-27 (UTC), session **s074**.
> **Scope decided by the user:** a new **Admin** section in the **settings-v2** dialog; its rows read/write the
> **server-side global `opencode.json` / `opencode.jsonc`** (shared by all users); first rows are
> *webui server → enable/disable auto start* and *webui server → webui port (default 4446)*; on
> `opencode.exe` start the web UI comes up on the configured port, reachable from any domain.
> **Feature ids:** FE-022 was taken by the parallel session s073, so these are **FE-023** (admin settings) and
> **FE-024** (exe web auto-start).

---

## 0. Executive summary

The good news: **most of the hard part already exists.**

| What we need | Reality in the fork |
|---|---|
| "All future admin settings save in `opencode.json` / `opencode.jsonc`" | ✅ There is already a global-config **write** endpoint the web UI uses today: `PATCH /global/config` → `Config.updateGlobal` (`packages/opencode/src/config/config.ts:656-680`), which patches the **first existing** of `~/.config/opencode/{opencode.jsonc, opencode.json, config.json}` and **preserves comments** when the file is `.jsonc` (`patchJsonc`, `:150-162`). The app calls it via `serverSync().updateConfig` (`packages/app/src/context/server-sync.tsx:704-715`), used today for `shell` and `disabled_providers`. |
| "A new Admin section in settings v2" | ✅ The v2 category list is hand-written JSX (`settings-v2/dialog-settings-v2.tsx:56-89`): one `TabsV2.Trigger` + one `TabsV2.Content` adds a tab. Rows use `SettingsRowV2` + `Switch` (`@opencode-ai/ui/v2/switch-v2`) + `TextInputV2`. |
| "Global setting for all users" | ✅ Semantically free: the config file *is* process-global, read by every instance, and a write already broadcasts (it disposes all instances). ⚠️ But there is **no user/role model at all** — see D5. |
| "webui port" | ✅ `server.port` already exists in the config schema and is already honoured **at startup**. What is missing is (a) a UI row, (b) an *apply* path (a port change needs a restart), (c) a default that is 4446 — delivered as a **config-schema default** (DEC-050), *not* by editing the server's port-fallback constant (that approach was tried in s072 and **rejected**). |
| "enable/disable auto start" | ❌ Nothing exists. No `autostart` concept anywhere in the repo; a no-arg `opencode.exe` opens the **TUI**, which binds **no** port (`cli/cmd/tui.ts:73,233-249`). Needs new code (FE-024) — but the TUI worker already has a `server` RPC that listens (`cli/tui/worker.ts:54-58`), which is the cheap insertion point. |

**Total: ~2 new config keys, 1 new settings tab, 1 new runtime module, no protocol redesign, no new auth
system.** The only genuinely new machinery is "make a saved port take effect" (restart-vs-relisten) and the
exe auto-start.

---

## 1. Facts that shape the design (from the three research threads)

### 1.1 Config: load, precedence, write

- **Live config system for `web`/`serve`** is `packages/opencode/src/config/config.ts` (the "v1" config).
  `Config.Service` → `get` / `getGlobal` / `update` / `updateGlobal` / `invalidate` (`:125-136`).
- **Precedence** (`config.ts:328-612`): remote `.well-known` → **global dir** → `OPENCODE_CONFIG` → project
  `opencode.json(c)` → `.opencode/` dirs → `OPENCODE_CONFIG_CONTENT` → account/org config → managed dir
  (`/etc/opencode`, `%ProgramData%\opencode`) → macOS MDM. **CLI args are not part of the merge** — they are
  applied afterwards in `cli/network.ts`.
- **Merge** is a deep merge, source wins; arrays are **replaced** except `instructions` (`:42-52`).
- **The `server` namespace** is `packages/core/src/v1/config/server.ts:6-18`:
  `port?: PositiveInt`, `hostname?`, `mdns?`, `mdnsDomain?`, `cors?: string[]` — mounted at
  `packages/core/src/v1/config/config.ts:38-40`. **No defaults in the schema**; defaults live in the yargs table.
- ⚠️ **A key that is not declared in the schema is silently dropped** — decoding uses
  `onExcessProperty: "ignore"` (`config/parse.ts:40-44`) and the PATCH payload is `ConfigV1.Info`. So a new
  admin key **must** be added to `ConfigServerV1.Server` or it can never be written or read.
- ⚠️ **Only the GLOBAL config is read for the network options**: `resolveNetworkOptions` calls
  `cfg.getGlobal()` (`cli/network.ts:58`) and the result is process-cached with `Duration.infinity`
  (`config.ts:295-303`), invalidated only by `Config.invalidate()`. A project-level `server.port` is ignored.
- ⚠️ **Write hazards** (both matter for the admin rows):
  - Comment preservation only happens when the resolved file ends in **`.jsonc`** (`config.ts:663-676`);
    a plain `opencode.json` gets `JSON.stringify`-clobbered.
  - `Global.Path.config` **ignores `OPENCODE_CONFIG_DIR`** while `ConfigPaths.directories` *reads* it
    (`config/paths.ts:39`) → with that env var set, a write lands in the XDG dir while reads prefer the env dir,
    so the write appears to do nothing.
  - **Arrays are replaced, not merged** → the admin UI must PATCH **only the changed leaf**, never the whole
    `server` object (or `server.cors` would be overwritten).

### 1.2 Ports: what actually happens at runtime

```
opencode web | serve | acp
  → resolveNetworkOptions(args)            cli/network.ts:56-80   ( --port > config.server.port > yargs default 0 )
  → Server.listen(opts)                    server/server.ts:78
  → startWithPortFallback(opts)            server/server.ts:122-127   ( port 0 → try DefaultPort, else any free port )
  → NodeHttpServer.layer({ port, host })   server/server.ts:219
```

- `web.ts` / `serve.ts` **throw the `Listener` away** (only `server.port` is printed), so today nothing can
  re-bind the socket. There is **no config-file watcher** for the global dir
  (`packages/core/src/filesystem/watcher.ts` watches only `location.directory` + `.git`) and **no SIGHUP**
  handler anywhere. ⇒ **A saved port change cannot take effect without either a process restart or new
  re-listen code.**
- The **only** place that already re-listens is the TUI worker RPC: `cli/tui/worker.ts:54-58`
  (`if (server) await server.stop(true); server = await Server.listen(input)`). That is the template.
- `DefaultPort` / a fork constant in `server/server.ts` was tried in s072 and **rejected + reverted** (DEC-049).
  The port is resolved by `startWithPortFallback` from `port === 0`; the 4446 default goes into the **config
  schema** instead, so this file stays untouched (see §2.1 and DEC-050).

### 1.3 Auth: there are no users, only one shared password

- `server/auth.ts:17-20`: the entire auth config is `OPENCODE_SERVER_PASSWORD` + `OPENCODE_SERVER_USERNAME`.
  `authorized()` is plain string equality (`:28-34`). **No roles, no sessions, no per-user records.**
- A repo-wide grep for `role` / `isAdmin` / `admin` in the server packages returns only LLM message roles.
- ⇒ **Every authenticated browser is already a full admin today**: it can `PATCH /global/config`,
  `PATCH /config` (which writes into arbitrary project dirs), `POST /global/dispose`, `POST /global/upgrade`.
  The Admin tab therefore introduces **no new privilege** — it only makes existing power visible. See **D5**.

### 1.4 Settings v2 surface

- Category list = literal JSX in `settings-v2/dialog-settings-v2.tsx:56-89` (2 groups: *Desktop*, *Server*;
  tabs `general`, `shortcuts`, `servers`, `providers`, `models`), each `TabsV2.Trigger value=…` +
  a matching `TabsV2.Content value=…` (`:90-104`). Selection is a signal seeded from the `defaultValue` prop (`:29`).
- Row primitives: `SettingsRowV2` (`settings-v2/parts/row.tsx:10`), `SettingsListV2` (`parts/list.tsx:4`),
  `Switch` (`@opencode-ai/ui/v2/switch-v2`), `TextInputV2`, `ButtonV2`. Sections are
  `div.settings-v2-section` + `h3.settings-v2-section-title` + `SettingsListV2`.
- Best write-a-setting precedents: `settings-v2/providers.tsx:97-118` (optimistic set → `updateConfig` →
  success/error toast → rollback on failure) and `settings-v2/general-controllers.ts:52-73` (shell, fire-and-forget).
- The read-only-fetch precedent for a non-SDK route: the RSS row (`settings-v2/general.tsx:446-485`,
  `fetch("/api/rss/url", { credentials: "same-origin" })`).
- i18n: 62 locale files (`packages/app/src/i18n/*.ts`), `en.ts` is the typed source
  (`language.t` is typed against `keyof Dictionary` ⇒ a missing key is a **typecheck error**), and
  `packages/app/src/i18n/parity.test.ts` **fails** unless every key exists in all 61 non-English locales.
  Cheap precedent: English text in every locale (the RSS keys; `zh` translated).
- ⚠️ **v1 is effectively dead code**: the "New interface designs" sunset date passed
  (`context/settings.tsx:64` = 2026-09-14), so `oldInterfaceRetired()` is true, the v1↔v2 toggle is not
  rendered, and `useSettingsDialog()` hard-codes v2 (`settings-dialog.tsx:20`). The repo's documented rule
  (`AGENTS.md:41-61`, from the RSS gap) still says "keep both in sync" → see **D2**.

### 1.5 Windows / exe / startup

- The packaged `opencode.exe` is built by `packages/opencode/script/build.ts` from this checkout and embedded
  with this checkout's `packages/app`; the same binary is copied to `package-dist/opencode.exe`,
  `desktop/resources/opencode.exe` and the NSIS installer. **No-arg launch = the TUI**
  (`cli/cmd/tui.ts:73` `command: "$0 [project]"`), which binds **no** port unless `--port`/`--hostname`/`--mdns`
  is passed (`:233-249`); otherwise it talks to the worker over an in-process RPC bridge
  (`http://opencode.internal`).
- **There is no auto-start / boot mechanism anywhere in the repo** (no `HKCU\…\Run`, no `schtasks`, no systemd
  unit, no launchd plist, no `app.setLoginItemSettings`). The only "spawn a server and find it again" machinery
  is `packages/cli`'s registration-file daemon (`services/daemon.ts`, `server.json` + password file) — and its
  `serve` starts at a hard-coded **4096** and increments (`commands/handlers/serve.ts:30-37`), ignoring both
  `config.server.port` and `DefaultPort`.
- The install script (root `install`, `curl … | bash`) installs to `~/.opencode/bin`, edits shell rc files and
  prints no URL/port and registers nothing. The upgrade path (`installation/index.ts:162-201`) downloads the
  fork's release asset from `nkyang10/opencode`.
- The current Linux story is external shell scripts (`fork-root/scripts/run-web.sh 4447` →
  `web --port 4447 --hostname 0.0.0.0`), plus a desktop launcher that embeds the password in plaintext.
- ⚠️ `web --hostname 0.0.0.0` **without** a password prints "server is unsecured" and exposes the agent to the
  whole LAN (`cli/cmd/web.ts:41-43`). Any auto-start feature must decide its policy → **D4**.

### 1.6 The global skills (the user's side question)

Yes, they are still there and working:

- `~/.config/opencode/skills/starter-kit/SKILL.md` (2026-09-14) and
  `~/.config/opencode/skills/web-research/SKILL.md` + `storage/serper.py` (2026-09-14).
- `~/.config/opencode/plugin/kickoff.ts` re-creates the dir and seeds `starter-kit` at every start
  (`ensureSkillsDir` `:98-105`, `seedStarterKit` `:107-117`, `promoteWebResearch` `:119-137`, entrypoint
  `:139-153`); fully idempotent, registers no hooks. The live :4447 log shows
  `[opencode-kickoff] skills dir: ok | starter-kit: present | web-research: present`.
- Discovery: `packages/opencode/src/skill/index.ts:21-25,186-227` — `~/.claude/skills`, `~/.agents/skills`,
  every config dir's `{skill,skills}/**/SKILL.md` (config dirs come from `config/paths.ts:23-41`, which includes
  `Global.Path.config` = `~/.config/opencode`), plus explicit `skills.paths` / `skills.urls`.
- ⚠️ Three findings worth acting on separately:
  1. `/home/mark/Desktop/ide/.opencode/skills/web-research/` is **md5-identical** to the global copy, so every
     session in this workspace scans both and logs `duplicate skill name` (last-writer-wins,
     `skill/index.ts:125-139`). The `gdx` copy is **older/different** (5629 B vs 6700 B).
  2. **Editing or adding a global skill needs a server restart** — discovery is `InstanceState`-memoised per
     directory with no watcher (`skill/index.ts:259-287`, `effect/instance-state.ts:30-50`). The only hot path is
     the TUI's `SIGUSR2` → `reload` → `Config.invalidate()` + dispose instances (`tui.ts:216-219`, `worker.ts:63-71`).
  3. On the v2 plugin loader the `kickoff` plugin's shape likely doesn't match `PluginModule`
     (`core/src/config/plugin/external.ts:15-30`) and is swallowed by `Effect.ignoreCause` (`:87`) — the v1
     loader is what actually runs it.

---

## 2. Proposed design

### 2.1 Config shape (the "all future admin settings" home)

```jsonc
// ~/.config/opencode/opencode.jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "server": {
    // port: 4446   ← the Admin "webui port" row edits THIS. Unset now means 4446
    //                (config-schema default, DEC-050); an explicit --port still wins;
    //                a busy 4446 still falls back to a free port.
    "hostname": "0.0.0.0",     // ← existing; admin may get a row later
    "webui": {
      "autoStart": true        // ← NEW: start the web UI when the exe starts
    }
  }
}
```

**Why the port row maps to the existing `server.port` and not a new `webui.port`:** `server.port` is already the
key the runtime honours. A second `webui.port` would be a second source of truth that silently disagrees with
`--port` and with `server.port`. The nested `webui` object is where *new* admin-only keys accumulate
(`autoStart`, later `hostname`, `mdns`, `cors`…).

**How "default 4446" is delivered (DEC-050, replacing the rejected DEC-049):** a **default on the schema field**
in `packages/core/src/v1/config/server.ts` —

```ts
port: Schema.optional(PositiveInt).pipe(Schema.withDefault(() => 4446))   // fork default; upstream has none
```

`resolveNetworkOptionsNoConfig` already prefers `config?.server?.port` (`cli/network.ts:69`), so an unset value
decodes to 4446 and the listener gets it. Consequences: `server/server.ts` and `cli/network.ts` are **not**
touched (smaller upstream-merge surface), the Admin row can show 4446 *honestly*, and the published JSON schema
/ docs will state 4446 as the default. **Check before implementing:** confirm the exact `Schema.withDefault`
usage against an existing defaulted field in this schema tree (`packages/core/src/v1/config/*.ts`) so the
OpenAPI/JSON-schema output stays correct, and confirm that a defaulted `port` does not leak into a
`GET /config` response in a way that surprises existing clients (it will make the effective port visible — which
is what we want, but it is a behaviour change for API consumers).

**Change list (server side):**
- `packages/core/src/v1/config/server.ts` — add the **4446 default** for `port` (DEC-050) and
  `webui: Schema.optional(Schema.Struct({ autoStart: Schema.optional(Schema.Boolean) }))`
  (annotated, documented — this file is the OpenAPI/JSON-schema source, so the docs site picks it up).
- `packages/web/src/content/docs/config.mdx` (+ per-locale copies) — document the default and the new key.
- No client regeneration needed for a schema addition: the generated client types come from the HTTP contract
  (`packages/client`), and `ConfigV1.Info` is already part of the `PATCH /global/config` payload. A **typecheck**
  is enough. (Verified: `packages/sdk/openapi.json` is produced by `bun dev generate`; only *endpoint* changes
  force a regen.)

### 2.2 Read/write path for the rows

- **Read** saved values from the config the app already has: `serverSync().data.config` (fetched by
  `context/global-sync/bootstrap.ts:114-121` via `sdk.global.config.get()`).
- **Write** with the existing mutation: `serverSync().updateConfig({ server: { webui: { autoStart } } })` /
  `…({ server: { port } })` — **only the changed leaf**, so `server.cors` etc. are never clobbered.
  Pattern to copy: `settings-v2/providers.tsx:97-118` (optimistic set → await → success/error toast → rollback).
- **The one thing the app cannot know by itself** is the *effective* port (config ?? `DefaultPort`) and the
  *currently applied* port. So FE-023 adds **one small read-only endpoint**:
  `GET /webui` (raw router route, auth-gated like `/api/rss/url` and `/api/push/*`) returning
  `{ port: number, hostname: string, url: string, autoStart: boolean, restartRequired: boolean }`.
  Consumed by a hand-written helper in `packages/app/src/utils/server.ts` — the documented precedent for a route
  outside the generated client is `fetchProjectDirectories` (`server.ts:64-96`). This avoids an SDK regeneration
  inside the same change; a typed client can come later.
- ⚠️ Expected side effect to design around: `PATCH /global/config` **disposes every open instance** when the value
  actually changes (`handlers/global.ts:78-82` → `disposeAllInstancesAndEmitGlobalDisposed`). For the
  auto-start toggle that is harmless-ish; for a port row it means live tabs bounce. The row copy must say so, and
  the "Apply" action should be explicit rather than on-blur.

### 2.3 Applying a port change (the real work)

Two options; **recommend A now, B as a follow-up**:

- **A. "Saved — restart to apply" (cheap, honest).** The row saves `server.port` and the Admin tab shows
  `restartRequired` (saved ≠ applied, from `GET /webui`) with a copy line: *"restart opencode to serve on 4446"*.
  Zero runtime risk. Matches how the fork is actually operated today (external `deploy-web-4447.sh`).
- **B. Live re-listen (nicer, more code).** Keep a module-level `Listener` in `server/server.ts`
  (`export let active: Listener | undefined`, set in `listenEffect`, cleared in `makeStop`), and add
  `POST /webui/restart` that re-resolves the network options from the (just-invalidated) global config and does
  the `stop(true)` → `listen` dance copied from `cli/tui/worker.ts:54-58`. Caveats to design around: the socket
  the request arrives on is the one being closed (`stop(true)` force-closes live websockets,
  `server.ts:191-202`), so the response must be flushed first / the client must tolerate a dropped connection;
  and `Config.getGlobal()` is `Duration.infinity`-cached, so the route must call `Config.invalidate()` first.

### 2.4 FE-024 — exe auto-start (the web UI comes up with the exe)

New module `packages/opencode/src/cli/web-autostart.ts`:

```
export async function maybeAutoStartWebServer(input: { hostname?: string })  // name TBD per fork style
```

- Reads the **global** config once. If `server.webui.autoStart` is `true` → `Server.listen({ hostname, port })`
  and keep the returned `Listener` in a module-level ref (so it can be re-bound later by 2.3-B).
- **Where it is called:** the **TUI worker bootstrap** (`cli/tui/worker.ts`), right after the server app is
  constructed. That single insertion point covers the no-arg `opencode.exe` (the TUI is `$0`), and it reuses the
  worker's existing `server` RPC. `opencode web` / `serve` already listen, so they do not call it.
  `opencode run` / `acp`: **not** auto-started (avoid surprising listeners); a `--web-autostart` /
  `--no-web-autostart` pair overrides the config either way.
- **Hostname policy (D4):** bind `0.0.0.0` only when a server password is configured; otherwise bind
  `127.0.0.1` and print the existing "server is unsecured" warning. That satisfies "reachable from any domain"
  without turning an unauthenticated agent into a LAN-wide service. The chosen hostname is printed with the
  network URLs, reusing `getNetworkIPs()` from `cli/cmd/web.ts:10-30`.
- Prints one line: `Web UI: http://<ip>:<port>  (auto-start; change in Settings ▸ Admin)`.

### 2.5 UI shape (settings v2)

`settings-v2/dialog-settings-v2.tsx`: add to the **Server** group

```tsx
<TabsV2.Trigger value="admin">
  <Icon name="shield" />
  {language.t("settings.tab.admin")}
</TabsV2.Trigger>
```
plus `<TabsV2.Content value="admin" class="settings-v2-panel"><SettingsAdminV2 /></TabsV2.Content>`.

New `settings-v2/admin.tsx` (v2-only unless D2 says otherwise):

```
┌ Web UI server ─────────────────────────────────────────────┐
│ Auto start        [switch]   Start the web UI when the     │
│                              opencode app starts           │
│ Port              [ 4446 ]   TCP port for the web UI       │
│                              (needs a restart to apply)    │
│ ⓘ Saved 4446 · running 4447 — restart opencode to apply.   │
└─────────────────────────────────────────────────────────────┘
```

- i18n keys: `settings.tab.admin`, `settings.admin.section.webui`,
  `settings.admin.row.autoStart.{title,description}`, `settings.admin.row.port.{title,description,invalid,placeholder}`,
  `settings.admin.row.restartRequired` — added to `en.ts` **and all 61 locales** (English source text, `zh`
  translated) or `parity.test.ts` fails. 6 tabs instead of 5: on narrow screens the strip scrolls
  (`settings-v2.css:214-249` already hides icons in horizontal mode for exactly this reason) — acceptable.
- Keep the `div[data-action="settings-…"]` wrapper convention: the e2e suite locates rows by `data-action`
  (`e2e/regression/remote-session-settings.spec.ts:24,42,63`). No test asserts the tab count, but
  `context/command.test.ts:20` pins the command-id list, so **do not add a new palette command** in this change.

---

## 3. Phasing, files, and gates

| Phase | Content | Files | Gate |
|---|---|---|---|
| **P0** | ~~Port default → 4446 in the server fallback~~ **CANCELLED** — the `Server.DefaultPort` approach was tried in s072 and **rejected + reverted**; the default now moves to P1's config schema (DEC-050). Nothing to do. | — | — |
| **P1** (schema) | `server.port` **default 4446** (DEC-050) + `server.webui.autoStart` in the config schema + docs | `packages/core/src/v1/config/server.ts`, `packages/web/src/content/docs/config.mdx` (+ locales) | `bun typecheck` (core), config unit tests, `bun dev serve` with no flags and no config → listens on **4446** |
| **P1** (schema) | `server.webui.autoStart` in the config schema + docs | `packages/core/src/v1/config/server.ts`, `packages/web/src/content/docs/config.mdx` (+ locales) | `bun typecheck` (core), config unit tests |
| **P2** (read) | `GET /webui` (effective + applied port, hostname, autoStart, restartRequired) + app helper | `packages/opencode/src/server/routes/instance/httpapi/…` (group+handler) or a raw route beside `rssUrlRoute`, `packages/app/src/utils/server.ts` | `bun run test:httpapi` **must gain a scenario** (`test/server/httpapi-exercise/index.ts`, `--fail-on-missing`), typecheck |
| **P3** (UI) | Admin tab + 2 rows + i18n ×62 | `settings-v2/dialog-settings-v2.tsx`, new `settings-v2/admin.tsx`, `settings-v2/parts/*` if needed, `i18n/*.ts` | app `typecheck`, `bun run test:unit` (parity green), oxlint 0 errors |
| **P4** (runtime) | FE-024 auto-start in the TUI worker + hostname policy + `--web-autostart/--no-web-autostart` | new `cli/web-autostart.ts`, `cli/tui/worker.ts`, `cli/cmd/tui.ts`, maybe `cli/network.ts` | typecheck; manual: exe/TUI with `autoStart` on/off; unsecured-hostname case |
| **P5** (optional) | Live re-listen so a port change applies without a restart (2.3-B) | `server/server.ts`, `cli/tui/worker.ts`, a `POST /webui/restart` route | httpapi scenario; live test: change port in the UI, server rebinds |
| **P6** | Docs: fork `AGENTS.md` "This fork" section, p003 README FE-023/024, `docs/` | — | — |

**Verification that unit tests cannot do** (learned from s036/s069): after P3/P4, run the real thing —
`deploy-web-4447.sh --detach`, then Playwright against the live server: the Admin tab renders, toggling
auto-start writes `opencode.jsonc` **with comments intact**, the port row validates, the restart-required hint
appears, and killing/restarting the binary lands on the configured port.

---

## 4. Open questions (need the user's call)

- ~~**D1 — port default (blocks P0).**~~ **✅ RESOLVED (s075) — and not the way s072 tried it.** The user
  rejected s072's `Server.DefaultPort = 4447` and the whole change was reverted (DEC-049 marked rejected), so
  `server/server.ts` keeps upstream's literal 4096. The requirement "default 4446" is delivered in the **config
  layer** instead (**DEC-050**): a schema default of 4446 on `ConfigServerV1.Server.port`, which
  `resolveNetworkOptionsNoConfig` already honours. `--port` still wins, a busy 4446 still falls back to a free
  port, and 4447 remains only the explicit local deploy port. **P0 is cancelled; the work moved into P1.**
- **D2 — v2-only, or both surfaces?** You said "in v2". The repo rule (from the RSS gap) says keep v1 and v2 in
  sync, but **v1 is dead code** (its toggle is past its sunset date and `useSettingsDialog()` hard-codes v2).
  Recommendation: **v2 only**, and record the deviation in the fork `AGENTS.md` so a future agent does not
  "fix" it by editing dead code.
- **D3 — auto-start default: on or off?** Writing `autoStart: true` into a user's config on upgrade is a
  behaviour change; leaving it unset must mean *something*. Recommendation: **unset = off** (opt-in), so no
  existing install suddenly opens a listening socket.
- **D4 — 0.0.0.0 without a password.** Recommendation: bind `0.0.0.0` **only** when a server password is set;
  otherwise `127.0.0.1` + the existing "unsecured" warning. (Alternative: allow it and warn loudly.)
- **D5 — who is an admin?** There is no user model: anyone with the shared password can already rewrite the
  global config, dispose instances and trigger an upgrade. Recommendation: accept **"authenticated = admin"**
  now and say so in the tab's description; a real role would mean inventing a user store (out of scope).
- **D6 — port row semantics on a busy port.** If the configured port is taken, the server silently falls back to
  a random port (`startWithPortFallback`). Should the Admin tab surface that ("4446 busy → running on 41234")?
  Recommendation: yes, it is exactly the kind of thing that otherwise wastes an hour.

---

## 5. Effort estimate

P0 **cancelled** (rejected) · P1 ≈ 45 min (schema default + new key + docs) · P2 ≈ 1.5 h (route + exercise
scenario + client helper) · P3 ≈ 2–3 h (tab, two rows, 62 locales, unit tests) · P4 ≈ 2 h (auto-start + hostname
policy + a real Windows/Linux check) · P5 ≈ 3 h (optional). **P1–P4 ≈ one focused session;** P5 separate.

## 6. Housekeeping found along the way (not part of this feature)

1. `ide/.opencode/skills/web-research` duplicates the global copy → `duplicate skill name` warning in every
   session here; `gdx`'s copy is an older version. Removing the workspace duplicates is safe (global is
   authoritative, DEC-025/FU-044).
2. `~/Desktop/MarkCode-4447.desktop` and `~/Desktop/opencode-web.desktop` carry a **plaintext server password**
   in world-readable files — move it to a `chmod 600` file that the launcher sources, or to the keychain.
3. `packages/desktop/src/main/background-cli.ts:44` calls `opencode-cli service get password`, but
   `packages/cli/src/commands/commands.ts:30-42` defines no `get` subcommand (only `password`) — latent bug on
   the `OPENCODE_SIDECAR_V2=1` path.
4. `packages/cli`'s `serve` starts at a hard-coded 4096 and ignores `config.server.port` / `DefaultPort`.
5. `package-dist/deploy-log-dir.txt` and `launch-web.cmd` on this checkout still point at the build machine's
   `C:\Users\MY\Desktop\Development\opencode\logs\deploy`; `deploy-log-dir.txt` is actively read by
   `Global.logDirectory()`.
6. The inotify instance budget is nearly exhausted on this machine (97 open vs `max_user_instances=128`), which
   is why some `packages/opencode` server tests fail with ENOSPC — unrelated to any feature, but it will keep
   producing false failures.
