# opencode Server API — engineering interface for custom UIs

> Source of truth: https://opencode.ai/docs/server · OpenAPI spec at `http://<host>:<port>/doc`
> and committed at `packages/sdk/openapi.json` in the opencode repo. Compiled 2026-09-07 from
> docs + repo + community usage. Verify exact shapes against `/doc` before coding.

## Server mode

Every `opencode` run starts a headless HTTP server (the TUI is just a client). `opencode serve` runs it standalone.

- **Protocol: HTTP REST + SSE only.** No WebSocket, no JSON-RPC. Streaming = SSE.
- Default `--hostname 127.0.0.1 --port 4096`; flags `--cors <origin>` (repeatable), `--mdns`, `--mdns-domain` (default `opencode.local`).
- `opencode --port 4096 --hostname X` lets a TUI attach; `opencode attach http://host:4096` too.
- Server impl: `packages/server` (Hono).

## Key endpoints

| Endpoint | Purpose |
|---|---|
| `GET /global/health` | `{healthy, version}` |
| `GET /global/event` (SSE) | global events |
| `GET /project`, `/project/current`, `/path` | workspace context |
| `GET|PATCH /config`, `GET /config/providers` | config + providers |
| `GET /provider`, `/provider/auth` | providers/auth |
| `GET|POST /session` · `GET|PATCH|DELETE /session/:id` | session CRUD |
| `POST /session/:id/init\|fork\|abort\|share\|summarize\|revert\|unrevert` | session actions |
| `GET /session/:id/children\|todo\|diff` | subagents, todo, diff |
| `GET\|POST /session/:id/message` · `GET /session/:id/message/:id` | chat core |
| `POST /session/:id/prompt_async` | fire-and-forget prompt |
| `POST /session/:id/command` · `/session/:id/shell` | slash commands / shell |
| `GET /find?pattern=` · `/find/file?query=` · `/find/symbol?query=` | search |
| `GET /file?path=` · `/file/content?path=` · `/file/status` | files |
| `GET /command` `/agent` `/lsp` `/formatter` `/mcp` | registry |
| `GET /event` (SSE) | event stream — first event `server.connected` |
| `POST /tui/append-prompt\|submit-prompt\|execute-command\|show-toast\|open-*`; `GET /tui/control/next`; `POST /tui/control/response` | drive a running TUI |

Message POST body: `{messageID?, model?, agent?, noReply?, system?, tools?, parts}`; parts are typed
(`text`, `tool`, `step-start`, …). `noReply:true` injects context without triggering an AI turn.

## Event types (SSE)

`server.connected`, `session.created|updated|idle|status|compacted|deleted|diff|error`,
`message.updated|removed`, `part.updated|part.removed`, `permission.asked|replied`,
`tool.execute.before|after`, `command.executed`, `file.edited|watcher.updated`,
`todo.updated`, `lsp.updated|lsp.client.diagnostics`, `shell.env`, `installation.updated`,
`tui.prompt.append|command.execute|toast.show`.

## Official SDK (npm)

- **`@opencode-ai/sdk`** (MIT) — type-safe client generated from the OpenAPI spec.
  `createOpencode({...})` spawns server+client; `createOpencodeClient({baseUrl})` connects to a running instance.
  Subpath exports: `.`, `./v2`, `./client`, `./server`.
- **`@opencode-ai/plugin`** — plugin typings (`Plugin`, `tool()`, hooks).
- **`@opencode-ai/script`** — CLI scripting.

```ts
import { createOpencodeClient } from "@opencode-ai/sdk"
const client = createOpencodeClient({ baseUrl: "http://localhost:4096" })
const session = await client.session.create({ body: { title: "x" } })
for await (const { type, properties } of (await client.event.subscribe()).stream) { … }
```

## Official web app

`opencode web` — SolidJS built-in UI (`packages/app`, `packages/web`, `packages/ui`, `packages/desktop` Electron).
Same server flags + SSE; `server` block in `opencode.json` (`{port,hostname,mdns,cors}`).
**Desktop-oriented; mobile view cluttered/overlapping (issue #11828), mobile-friendly UI requested (#5126) — the gap this project fills.**

## Auth

`OPENCODE_SERVER_PASSWORD` (username default `opencode`, overridable via `OPENCODE_SERVER_USERNAME`)
→ **HTTP Basic auth** for both `serve` and `web`. Without it localhost is unsecured; docs warn to set it
for network exposure. No token/API-key scheme. (→ FU-003: our UI can add its own auth layer.)

## Plugins cannot serve HTTP

Plugins (`.opencode/plugins/` or npm in `opencode.json` `plugin:`) export hooks (`event`, `tool`, `auth`,
`provider`, `chat.*`, `tool.execute.before/after`, `permission.ask`, `shell.env`, …).
**There is no HTTP-route/server hook** — a custom UI must be a separate process connecting over HTTP/SSE.
Plugins do receive `client` and `serverUrl` and can define custom tools.

## How community UIs connect (proven patterns)

- **chris-tse/opencode-web** — `opencode serve` + `EventSource`.
- **hosenur/portal** — spawns opencode server (:4000), Nitro **proxy + `@opencode-ai/sdk`**; SSE proxied.
- **joelhooks/opencode-vibe** — Next.js 16 route spawns `opencode serve` detached per project, reverse-proxies full API + SSE; auto-discovers via `lsof`.
- **oc-web / shuvcode** — TanStack Start + Bun proxy; browser never touches opencode directly.
- **opencode-manager** — Bun backend **spawns/supervises `opencode` processes**, SSE bridge to browser, its own auth (Better Auth).

**Takeaway:** the standard architecture = backend spawns/orchestrates `opencode serve`, exposes a
single API surface + SSE bridge, browser is just a thin client.

## Projects, directories and plain folders (verified on the fork, 2026-09-26)

The single most counter-intuitive part of the server model, and the cause of FE-020. Verified by reading
`packages/core/src/project.ts` + `packages/opencode/src/project/project.ts` **and** by measuring the live
fork on :4447 (see `20-logs/sessions/2026-09-26_s069_fe-020-plain-folder-projects.md`).

**A project is a git identity, not a folder path.** `ProjectV2.resolve(directory)`:
`git.repo.discover(directory)` → no repo ⇒ `{id: "global", directory: <fs root>, vcs: undefined}`; repo found ⇒
`id = hash(remote url)` → else the id cached in `<git-common-dir>/opencode` → else **the first root commit
sha**. Measured: a prepared folder's project id was literally its commit sha. So:

| directory | server record |
|---|---|
| a git repo (any depth) | its own row in `project`; a subdirectory becomes a `sandboxes` entry + a `project_directory` row |
| **no repo** (and a repo with no commits) | collapses into the **one** shared `global` row, whose `worktree` is a placeholder (`/`, or the last directory resolved) |
| anything | every opened directory is recorded in `project_directory` (`project_id`, `directory`, `time_created`) — since FE-020/DEC-045 this includes the global project, so a plain folder is still remembered |

**The recorded `project_directory.directory` is the directory that was *asked for*, not `ProjectV2.resolve`'s
`directory` field.** For a directory without a repository that field is the filesystem root, so recording it
would collapse every plain folder into a single `("/", global)` row. A repository records its own worktree
(its subdirectories are the `sandboxes` entries). Rule in `fromDirectory`: `data.vcs ? data.directory :
directory`. Guarded by a test in `packages/opencode/test/project/project.test.ts`.

**Consequences to design around:**
- `GET /project` lists **project identities**, so a folder without a repository has no row and cannot appear
  there. `GET /project/{projectID}/directories` lists the directories of one project — for `global` those are
  exactly the plain working folders, newest first (`desc(time_created), asc(directory)`). That pair is what the
  app's project list is built from.
- `POST /project/git/init?directory=X` (`git init`) does **not** give a folder an identity: no remote and no
  root commit ⇒ still `global`. Worse, on a non-repo directory it **repoints the global project's own
  `worktree`** at that folder.
- The running server caches the resolved identity per directory (`InstanceState`), so a change that would alter
  the id (e.g. the folder's first commit) only lands on a fresh resolution — a restart, not a refetch.
- A directory reaching the server is what records it: any workspace-routed call with
  `?directory=X` (e.g. `/project/current`) opens the instance and runs `fromDirectory`.
- Events: `project.updated` (per project row) and `project.directories.updated` (a new directory row) are both
  emitted on the **global** stream (`directory: "global"`), which is the branch clients refetch on.
- Sessions in a non-repo directory belong to the `global` project; `fromDirectory` re-points them if the
  directory later gets its own id.
