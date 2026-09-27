# s074 — PLAN: FE-023 admin settings (server-global) + FE-024 exe web auto-start

- **Date:** 2026-09-27 (UTC)
- **Owner:** agent (user: mark)
- **Trigger:** user — "new big enhancement / new setting in v2 for admin setting, admin setting is global setting
  for all user / admin setting -> our existing setting in opencode.ai / admin setting -> webui server -> enable /
  disable auto start / admin setting -> webui server -> webui port (default 4446) / all future admin setting save in
  opencode.json / opencode.jsonc / in opencode windows exe start, auto start webui with port from any domain
  access / also the global skill we have before? / u open agent thread to plan these how to arrange."
- **Outcome:** 📋 **PLAN ONLY** — 3 research threads (settings-v2 UI · server config write path · Windows/exe +
  global skills), scope questions answered by the user, plan written to
  `50-projects/p003-opencode-fork/notes/plan-admin-settings.md`. **No feature code written.** FE-022 was already
  taken by the parallel session s073, so these are **FE-023** / **FE-024**.

## User's scope decisions (asked, answered)

1. Admin **port** default = **4446** ("as you typed") — conflicts with s072/DEC-049's code default 4447, so
   **D1** in the plan asks for a one-word confirmation before flipping `Server.DefaultPort` to 4446.
2. Admin surface = **server-side `opencode.json` editor** (a new Admin section in settings v2 whose rows read/write
   the global config; existing per-user settings stay where they are). "our existing setting in opencode.ai" is
   therefore read as *the existing documented global config keys*, not a docs link.
3. Windows exe start = **the exe starts the web server itself, bound to 0.0.0.0** on the configured port (no
   boot/login autostart entry).
4. All future admin settings persist in `opencode.json` / `opencode.jsonc`.

## Method

Three `explore` subagents ran in parallel (research only, no edits, no builds):
1. **Settings-v2 surface** — how the dialog/categories/rows are built, per-user vs server storage, every direct
   `fetch` in the app, the v1/v2 dual-surface rule, i18n + parity, and what breaks when a 6th tab is added.
2. **Server config** — load/merge precedence, the `server` schema, whether any write path exists, the HTTP-API
   + client-generation conventions, the auth/multi-user reality, the port/hostname runtime chain, auto-start
   feasibility.
3. **Windows/exe + global skills** — the installer scripts and every artifact/command line, what `opencode.exe`
   does with no args, `packages/cli`'s daemon, the desktop sidecars, the install/upgrade path, existing autostart
   mechanisms, the local deploy scripts, and a factual audit of `~/.config/opencode/skills` + `plugin/kickoff.ts`.

## Headline findings (detail + file:line evidence in the plan doc)

- **A global-config write path already exists** — `PATCH /global/config` → `Config.updateGlobal`
  (`config/config.ts:656-680`), JSONC-comment-preserving, and the app already calls it
  (`context/server-sync.tsx:704-715`). So "all admin settings live in `opencode.json(c)`" is nearly free.
- **A new config key must be declared** in `packages/core/src/v1/config/server.ts` (decoding drops undeclared
  keys), and **only the global config** is read for the port (`cli/network.ts:58`, cached `Duration.infinity`).
- **A port change cannot apply live today**: `web.ts`/`serve.ts` discard the `Listener`, there is no config
  watcher on the global dir and no SIGHUP handler. The only re-listen precedent is the TUI worker RPC
  (`cli/tui/worker.ts:54-58`).
- **Writing the global config disposes all instances** (`handlers/global.ts:80`) — user-visible; the UI must not
  save on blur.
- **No users/roles exist** — one shared `OPENCODE_SERVER_PASSWORD`; every authenticated browser can already
  `PATCH /global/config`, `dispose` and `upgrade`. The Admin tab adds no new privilege (D5).
- **v1 settings are dead code** (the v1↔v2 toggle is past its sunset, `context/settings.tsx:64`, and
  `useSettingsDialog()` hard-codes v2) — so "v2 only" is defensible if recorded (D2).
- **A no-arg `opencode.exe` opens the TUI, not a web server**, and the TUI binds no port unless
  `--port/--hostname/--mdns` is given. There is **no** autostart/boot mechanism anywhere in the repo. So
  "start the web UI with the exe" is a small runtime change in the TUI worker, not an installer change.
- **`web --hostname 0.0.0.0` without a password exposes an unauthenticated agent to the LAN** → the plan makes
  0.0.0.0 conditional on a password being set (D4).
- **Global skills are alive**: `~/.config/opencode/skills/{starter-kit,web-research}` + `plugin/kickoff.ts`
  (idempotent, re-seeds at every start; the live :4447 log shows it running). Caveats: the identical workspace
  copy in `ide/.opencode/skills/web-research` triggers a `duplicate skill name` warning, `gdx`'s copy is older,
  and a new/edited skill needs a server restart (no watcher) except via the TUI's `SIGUSR2` reload.

## Deliverables

- `50-projects/p003-opencode-fork/notes/plan-admin-settings.md` — the arrangement: config shape
  (`server.port` + new `server.webui.autoStart`), why a second `webui.port` would be a second source of truth,
  the one new read-only route (`GET /webui` → effective + applied port, `restartRequired`), the UI sketch, the
  6 phases (P0 port default → P1 schema → P2 route → P3 tab+rows+i18n → P4 auto-start → P5 optional live
  re-listen → P6 docs), per-phase files and gates, the "verify live, unit tests can't see this" note, 6 open
  questions (D1–D6) and an effort estimate, plus 6 pieces of unrelated housekeeping found on the way.
- Follow-ups FU-089…FU-091 in `10-status/open-followups.md`; s072's FU-086 is unchanged (that port change is now
  gated on D1).
