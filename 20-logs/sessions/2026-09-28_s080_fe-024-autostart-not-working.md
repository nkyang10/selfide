# s080 — "auto start webui from opencode.exe seems not working" (FE-024)

- **Date:** 2026-09-28 (UTC)
- **User report:** *"opencode frok project, we added a feature of auto start webui by the opencode.exe program
  (windows program) seems not working"*
- **Scope:** diagnose. No code changed in the fork this session (0 edits, 0 commits).

## What FE-024 is

`server.webui.autoStart` (Admin tab) → a bare `opencode` (the TUI) binds the web server at startup, in the
**TUI worker** (`cli/tui/worker.ts` `webuiAutoStart` RPC), so no second process is spawned. Policy is pure and
unit-tested (`cli/web-autostart.ts` `resolveAutoStart`, 9/9). Code landed in `d78e8f4` (2026-09-28 00:58 +0800);
the silent-failure fix in `75e5c77` (09:33). It was **never run end-to-end by a human** — FU-093 was closed on gates
(typecheck / unit / policy tests) plus a route scenario, not on a live start.

## What I proved, on this box, with the built Linux binary (same `packages/opencode` source)

Isolated instance: `XDG_{CONFIG,DATA,CACHE,STATE}_HOME=/tmp/opencode/fe024`, `OPENCODE_SERVER_PASSWORD` set, run in
`tmux` (a TUI needs a TTY), global config `{"server":{"port":4499,"webui":{"autoStart":true}}}`.

1. **The feature works.** Bare `opencode` → `LISTEN 127.0.0.1:4499` (pid of the TUI process itself, `fd=26`), and
   `GET /global/webui` → `{"configuredPort":4499,"runningPort":4499,"autoStart":true}`. So the wiring, the config
   read, the RPC and the bind are all correct in the current source/binary.
2. **But it binds `127.0.0.1`, not the LAN — and there is no way to change that from the UI.** With
   `server.hostname: "0.0.0.0"` added to the same config, it binds `0.0.0.0:4499` and `http://192.168.100.11:4499/`
   answers **200**. The module comment states the intent ("the default hostname is the wildcard address"), but
   `cli/tui/worker.ts:78` passes `global.server?.hostname ?? input.hostname`, and `input.hostname` is yargs'
   `127.0.0.1` default (`cli/network.ts:14`) — because `tui.ts:233` calls `resolveNetworkOptionsNoConfig(args)`
   **without** the config argument, and the Admin tab has only two rows (auto-start switch + port), no hostname row.
   Net: the feature the user asked for in s074 ("comes up on the configured port, **reachable from any domain**")
   comes up **localhost-only** unless the user hand-edits `server.hostname` into the global config. From a phone or
   a second PC this is indistinguishable from "not working".
3. **Success and failure are both invisible.** The `Web UI: …` / `Network access: …` lines are printed at
   `tui.ts:272-292`, *before* the TUI takes the screen. Captured panes: at **t=3s** the four lines are on screen;
   at **t=4s** the screen is blank; from t=5s it is the logo splash. So the whole confirmation — including the
   "unsecured" warning and the `reason: "failed"` danger line — lives ~1 second. A successful start is announced
   and immediately erased; a failed bind is erased too. Nothing is written to the log on success.
4. **A Windows binary older than 2026-09-28 00:58 cannot contain any of this.** The installer stamps
   `OPENCODE_VERSION=0.0.0-windows-<yyyyMMddHHmm>` when `-Version` is not passed
   (`script/build-windows-installer.ps1:194-197`), so the user's exe self-reports its build minute and can be
   compared with the two commit times above.
5. **The TUI-only scope matters on Windows.** The installer also ships a desktop app + `opencode-cli.exe`
   background CLI and a `launch-web.cmd` that runs `opencode.exe web --port 4446 --hostname 127.0.0.1`
   (`build-windows-installer.ps1:396-403`). If the "opencode.exe program" the user started is the *desktop* app (or
   the `web` launcher), FE-024 never runs — it is wired into `cli/cmd/tui.ts` only. And if something else already
   holds the port, the bind throws and the result is the erased `failed` line.

## Not bugs (my own probes first looked like them)

- `GET /global/webui` reporting `autoStart:false` while the file said `true` — **my race**: I fired the GET and the
  `PATCH /global/config` in the same parallel tool batch, and the GET read the post-patch value. Re-run
  sequentially: `autoStart:true`. The FE-023 status route is correct.
- `PATCH /global/config` round-trip: correct — it deep-merges, adds `$schema` to a `.json` file, and left
  `server.port` alone when only the `webui` leaf was sent (the "patch only the changed leaf" rule holds).

## The user's answers (they settled the case)

1. **The installed desktop app** — not the TUI, not `launch-web.cmd`. → FE-024 was never implemented for that
   entry point. **Root cause.**
2. Their build is **new enough** to contain FE-024.
3. Same-PC browser.
4. Reachability wanted: **phone / other LAN devices**.
5. **方案A** — reuse is impossible cheaply: `build-node.ts:29` stubs the embedded UI to an *empty* file, so the
   desktop's own server cannot serve the page without a packaging change. So: the desktop spawns the portable
   `opencode.exe` the installer already ships, as `web --autostart`. **Scope chosen: desktop only** — the two
   TUI-path defects stay (FU-106). Password: `OPENCODE_SERVER_PASSWORD` if set.

## What I then implemented (FE-026 / DEC-055, uncommitted, not built, not deployed)

- `packages/opencode/src/cli/cmd/web.ts` — hidden `--autostart`: applies the existing policy, prints the URL and
  network URLs, logs a failed bind, exits 0 silently when disabled, and **never opens a browser**.
- `packages/opencode/src/cli/web-autostart.ts` — `autostartHostname` (I wrote the flag/config precedence
  **backwards** first and fixed it; it is now a tested pure function).
- `packages/desktop/src/main/webui-autostart.ts` (new) + `main/index.ts` wiring (start after the sidecar is
  ready, stopped by `stopSidecars`). Electron-free module so the helpers are unit-testable — the first version
  imported `electron` and the test failed on `Export named 'app' not found`.
- Gates: `bun turbo typecheck` **30/30**; `packages/opencode` + `packages/desktop` typecheck clean; oxlint
  **0 errors**; `test/cli/` 380 pass with **1 pre-existing snapshot failure** (proved pre-existing by re-running
  the whole directory with all my changes stashed: 377 pass, same failure, in `attention.test.ts`).
- Live checks from source on an isolated config, port 4498: secured → `0.0.0.0` + network URLs; **no password →
  `127.0.0.1` + the unsecured warning**; `autoStart:false` → exit 0, nothing printed, nothing bound. One honest
  correction mid-run: my first "unsecured" run bound `0.0.0.0` because **this agent's own shell exports
  `OPENCODE_SERVER_PASSWORD`** — the code was right and my test environment was not; re-run with `env -u`.

## What the user must do to verify it (Windows)

1. Rebuild the installer (`script\build-windows-installer.cmd`) and install it.
2. Set `server.webui.autoStart: true` in the Admin tab (or the global config) — it is opt-in.
3. For phone access, set `OPENCODE_SERVER_PASSWORD` in the Windows environment **before** launching the app;
   without it the web UI binds `127.0.0.1` only, by policy.
4. Start the app, then open `http://<pc-lan-ip>:4446` (or the configured `server.port`) and log in as
   `opencode` / that password.
5. The log to read either way is the desktop's `main.log`; look for `starting web ui auto-start` and
   `Web UI:`. `web ui auto-start skipped: portable CLI not found` means the installer's `resources/opencode.exe`
   is missing — that is a packaging problem, not a config one.

## Cleanup

Scratch home `/tmp/opencode/fe024` removed, all three `tmux` sessions killed, live :4447 (pid 233322) never
touched.

## Evidence

- `50-projects/p003-opencode-fork/opencode/packages/opencode/src/cli/web-autostart.ts`
- `…/src/cli/tui/worker.ts:64-100` (`webuiAutoStart` RPC)
- `…/src/cli/cmd/tui.ts:233` (config-less network resolution) and `:265-292` (the erased print)
- `…/src/cli/network.ts:12-15` (hostname default `127.0.0.1`)
- `…/packages/app/src/components/settings-v2/admin.tsx` (two rows only — no hostname)
- `…/script/build-windows-installer.ps1:194-197`, `:396-403`
