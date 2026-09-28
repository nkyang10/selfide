# Plan — desktop app auto-starts the web UI (FE-026, the desktop half of FE-024)

> **Status:** IMPLEMENTED, gates green, **NOT committed / NOT built / NOT deployed** — written and implemented
> 2026-09-28 (UTC), session **s080**. See `40-knowledge/decisions-log.md` → **DEC-055**.
> **Trigger:** the user reported *"we added a feature of auto start webui by the opencode.exe program (windows
> program) seems not working"*. s080 reproduced the whole path and found the feature **works** in the TUI and
> **does not exist** in the desktop app.
> **Scope the user chose:** **desktop only** — the TUI-path defects (erased confirmation, no hostname row) stay
> as they are, tracked in ide `FU-106`.

---

## 1. Diagnosis (all reproduced, not inferred)

| Question | Answer | Where |
|---|---|---|
| Does FE-024 work at all? | **Yes.** Bare `opencode` + `server.webui.autoStart: true` → `LISTEN 127.0.0.1:4499` held by the TUI's own pid; `GET /global/webui` → `{"configuredPort":4499,"runningPort":4499,"autoStart":true}` | s080 repro, isolated `XDG` home |
| Does the desktop app run FE-024? | **No.** It is wired into `cli/cmd/tui.ts:269` only. The desktop never runs the TUI command | — |
| What does the desktop start instead? | `SIDECAR_VERSION` is `v1` unless `OPENCODE_SIDECAR_V2=1` (and the installer sets neither that nor `OPENCODE_PORT`) → the in-process sidecar: `main/sidecar.ts:60` calls `Server.listen({port: <random free>, hostname: "127.0.0.1", password: randomUUID()})` | `main/index.ts:64`, `:350-379` |
| Could we just serve the page from that server? | **No, not cheaply.** `main/index.ts:123` sets `OPENCODE_DISABLE_EMBEDDED_WEB_UI=true` (so `server/shared/ui.ts:44-45` returns `null` → 404), **and** the bundle has no app in it: `packages/opencode/script/build-node.ts:29` stubs `files: { "opencode-web-ui.gen.ts": "" }`. Only `build.ts:189` embeds the real app. Un-setting the flag alone would serve a 404 page | `build-node.ts:29` |
| What did the user actually run? | **The installed desktop app**, on a build new enough to contain FE-024, viewing from the same PC | user answer, s080 |

## 2. Options considered

- **A — spawn the portable CLI (chosen).** The installer **already** ships a portable `opencode.exe` **with** the
  app embedded at `%LOCALAPPDATA%\Programs\@opencode-aidesktop\resources\opencode.exe`
  (`script/build-windows-installer.ps1:388-392`; it is what `launch-web.cmd` runs, and the path lookup already
  exists in `background-cli.ts:21-22`). Spawning it costs **no build change** and no risk to the Electron app.
- **B — embed the app into the desktop's own server bundle.** Mirror `build.ts:180-200` in `build-node.ts`,
  un-set the disable flag, add a second listener. No extra process, but the installer gains a second copy of the
  app, it overrides a deliberate upstream stub, and a second `Server.listen` clobbers the module-level
  `export let url` (`server/server.ts:71,89,180`) that `GET /global/webui` reads.
- **C — fix the TUI only.** Rejected by the user: they run the desktop app.

## 3. Design (A)

**Key move: the child decides, not the parent.** Reading `opencode.json(c)` (comments and all) inside Electron
would mean reimplementing `Config`'s file order and JSONC parsing, and then it would drift. Instead the desktop
spawns `opencode.exe web --autostart`, and the **CLI** applies the existing, unit-tested policy
(`cli/web-autostart.ts` `resolveAutoStart`/`autoStartWebServer`). Electron only resolves a path and a lifetime.

### 3.1 `packages/opencode/src/cli/cmd/web.ts` — a hidden `--autostart` mode

- New hidden yargs flag `autostart` (default `false`), so a human-typed `opencode web` is unchanged.
- When set, an early branch (before the existing banner/browser code) runs
  `WebuiAutostart.autoStartWebServer({...})` and then `Effect.never`:
  - `autoStart: config.server?.webui?.autoStart` — the opt-in, straight from the global config.
  - `port: opts.port || WebuiAutostart.suggestedPort` — `opts` already resolved `server.port` from the config
    (`cli/network.ts:76`); the fallback is the Admin default **4446**, not upstream's 4096.
  - `hostname: config.server?.hostname ?? (hasArg("--hostname") ? opts.hostname : "0.0.0.0")` — a bare
    `--autostart` asks for the **wildcard** (that is the point of the feature) and
    `resolveAutoStart` **downgrades it to `127.0.0.1` when no password is set**. An explicit `--hostname`
    still wins.
  - `secured: !!Flag.OPENCODE_SERVER_PASSWORD` — the same source `server/auth.ts` reads.
  - On `reason: "disabled"` → **return silently and exit 0** (that is the normal "user turned it off" case).
  - On `reason: "failed"` → log the port and hostname, so a clash is not invisible (the s073/FU-101 lesson).
  - On success → print `Web UI:` / `Network access:` / the unsecured warning, and **do not call `open()`**.
    Plain `web` opens a browser; a desktop app launching a browser tab on every start would be a regression.
- The existing body is untouched, so plain `opencode web` behaves exactly as before.

### 3.2 `packages/desktop/src/main/webui-autostart.ts` (new)

- `webuiCommandPath({isPackaged, resourcesPath, mainDir})` — mirrors `background-cli.ts:21-22`; win32 →
  `opencode.exe`, else `opencode`.
- `webuiChildEnv(env)` — copy, then **delete** `OPENCODE_DISABLE_EMBEDDED_WEB_UI` (else the child inherits the
  desktop's own opt-out and serves a 404) and `OPENCODE_CLIENT` (`"desktop"`; the child must behave like a
  terminal run). `XDG_STATE_HOME` is **kept**, so the child shares the desktop's database and the phone sees the
  same sessions the desktop shows. `OPENCODE_SERVER_PASSWORD` is inherited untouched — that is the password
  decision the user made.
- `startWebuiAutostart(logger)` — missing exe → one `logger.warn` and no spawn (never fail the app); otherwise
  `spawn(exe, ["web", "--autostart"], { env, stdio: "pipe" })`, stdout/stderr piped into the desktop log, an
  early exit logged with its code, and a returned `stop()` that kills it.

### 3.3 `packages/desktop/src/main/index.ts`

- After the sidecar is ready (`Fiber.await(loadingTask)`), fire `startWebuiAutostart`.
- `stopSidecars` also stops it, so `before-quit` / `will-quit` / `relaunch` take the child down.

### 3.4 Tests

- `packages/desktop/src/main/webui-autostart.test.ts` — the two pure helpers (path resolution per platform and
  packaging state; env scrubbing) in the existing `bun:test` style of `external-url.test.ts`.
- `packages/opencode/test/cli/web-autostart.test.ts` — unchanged: the policy it calls is already 9/9. The new
  thing worth pinning is the **precedence** (config `server.hostname` > explicit `--hostname` > wildcard request
  > loopback downgrade), so one case is added there for the default-wildcard request.

## 4. Risks, stated rather than hidden

- **Two processes, one SQLite file.** The desktop's server and the auto-started web server share the database
  (that is what makes the phone show the desktop's sessions). SQLite in WAL mode tolerates this, and the project
  has hit it before (ide `FU-043`/DEC-023, where sharing was declined for two *long-lived* servers). If
  `SQLITE_BUSY` ever shows up in the log, the fix is a dedicated port-only read path, not a silent revert.
- **The auto-started server outlives nothing** — it dies with the desktop app. A `service start` daemon would
  survive it, but that is a different product decision.
- **Windows-only verification.** The code is testable here; the real proof is the user's machine.

## 5. What was actually verified (and what was not)

**Verified here, from source (`bun src/index.ts web --autostart`, isolated `XDG` home, port 4498):**

| Case | Result |
|---|---|
| `autoStart: true`, password set | binds `0.0.0.0:4498`, prints `Web UI:` + 3 `Network access:` lines, keeps running |
| `autoStart: true`, **no** password (`env -u OPENCODE_SERVER_PASSWORD`) | binds **`127.0.0.1:4498`**, prints the unsecured warning, no network lines, keeps running |
| `autoStart: false` | **exit 0 immediately, no output, nothing bound** |

- Desktop side: 3/3 unit tests (path per platform/packaging state, env scrubbing, no mutation of the caller's env).
- `autostartHostname`: 3 new cases, `test/cli/web-autostart.test.ts` now **13/13**.
- Gates: `bun turbo typecheck` **30/30**; `bun typecheck` clean in `packages/opencode` and `packages/desktop`;
  oxlint **0 errors** on all 6 files (2 pre-existing warnings in `index.ts`, not in the new code).
- `bun test test/cli/` → 380 pass / 1 fail, and the failure is **pre-existing**: with every one of my changes
  stashed the same run gives 377 pass / **the same 1 snapshot failure** (`test/cli/cmd/tui/attention.test.ts`,
  a TUI sound/attention snapshot). Not mine, not touched.
- **Not verified:** the Windows launch. A real `opencode.exe web --autostart` child, the installer's
  `resources/opencode.exe` lookup on a packaged build, and the phone. That needs the user's machine — the
  checklist is in the session record.

## 6. Out of scope (recorded, not silently dropped)

- TUI path: the ~1 s confirmation window and the missing hostname row (ide `FU-106`).
- Making the desktop's own server serve the page (option B).
- A password row in the Admin tab; the password is `OPENCODE_SERVER_PASSWORD` in the environment.
