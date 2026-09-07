# OpenCode Web-UI Landscape — deep dive (Level 4 research, 2026-09-07)

> Detailed comparative intel on the top opencode web UIs. Compiled from repo READMEs, source trees,
> and issue lists. This is the "crowd-sourced reference architecture" for p001 — study before forking.

## 1. siteboon/claudecodeui "CloudCLI" (13.6k★) — NOT an opencode UI

**Stack:** Node 22 + Express backend (`server/modules/*`), React 18 + Vite + react-router 6, Tailwind,
CodeMirror, xterm.js, `ws` websockets, JWT auth, better-sqlite3, Electron companion. AGPL-3.0.

**Architecture:** own Node server **spawns CLIs and wraps them**: Claude Code via `@anthropic-ai/claude-agent-sdk`,
Codex via `@openai/codex-sdk` or a supervised app-server JSON-RPC process, Cursor via child process + node-pty.
Streaming/tool/diffs over a custom **WebSocket transport**. Reads/writes `~/.claude`, `~/.codex` directly.
Has the **best open architecture docs**: `docs/architecture/01-websocket-transport.md`, `02-realtime-stream.md`,
`03-conversation-handoff.md` (30-45KB each), `04-message-store-and-lazy-loading.md`.

**Features:** chat streaming, file explorer/editor, git explorer (stage/commit/branch), xterm terminal,
browser-use, session mgmt, permission/approval UI, plugin system, MCP sync, i18n (7 langs),
push/desktop notifs, PWA (`sw.js`+manifest), mobile-responsive, multi-provider.

**Limitations / open bugs:** drives Claude/Cursor/Codex, **not opencode**. opencode = provider reference only (#1265).
iPhone Chrome refresh loop (#1269), background agents killed when CLI exits (#1268), history-pagination stall (#1264),
Codex permission default ignored (#1263).

**Deploy:** `npx @cloudcli-ai/cloudcli`, Docker sandboxes, hosted CloudCLI Cloud (€7/mo), Electron.

## 2. chriswritescode-dev/opencode-manager (871★) — most complete web UI

**Stack:** pnpm monorepo. Backend **Bun + Hono + Better Auth + SQLite** (18 migrations). Frontend React + Vite +
React Router + TanStack Query + Radix + Tailwind. Shared Zod. MIT.

**Architecture:** Bun backend **spawns and supervises `opencode` processes** (`services/opencode-single-server.ts` 55KB,
`opencode-supervisor.ts`); a **SSE bridge** (`routes/sse.ts`, `sse-writer.ts`) re-streams opencode events to the browser;
git-askpass + SSH-host-key IPC handlers; optional Docker sandbox for runs. `ocm` CLI attaches your local TUI via `/api/opencode-proxy`.

**Features:** multi-repo git (worktrees, branches, commits, unified diffs), chat SSE streaming, Plan/Build modes,
`@file` mentions, Mermaid, file browser/editor, **scheduled cron jobs**, MCP server mgmt + OAuth, providers/API keys,
skills, **push notifications (VAPID)**, TTS/STT, i18n, mobile-first **installable PWA**.

**Limitations:** polish-class issues (theme islands #323, cookie/CORS split-origin #321/322, no per-workspace global skills #302).
Heaviest install of the five.

**Deploy:** Docker compose (port 5003), Docker Hub image, RepoCloud 1-click, self-host.

## 3. hosenur/portal (797★) — leanest mobile-first baseline

**Stack:** Bun workspace. `apps/web`: React 19 + TanStack Router + Vite + **Nitro server** + Tailwind v4 + React Aria (IntentUI) + SWR/zustand. `@opencode-ai/sdk` 1.14.41, `@pierre/diffs` + `diff`. MIT.

**Architecture:** `openportal` CLI **spawns `opencode serve`** (port 4000), auto-discovers instances via lsof/netstat;
Nitro **proxies `/api/opencode/<port>/*`** using the SDK; SSE proxied at `/api/opencode/<port>/events`;
heavy client hooks `use-opencode-events.ts` (27KB) rebuild message state; zustand draft-store carries forks.

**Features:** realtime chat streaming, session create/delete/**fork/revert**/stop, `@file` mentions, model picker,
git integration, subagent view w/ parent nav, question-tool rendering, multi-instance mgmt, mobile-first responsive + theming.

**Limitations:** requires Bun (breaks under Node/pnpm-dlx #55); **no auth** (docs say use Tailscale/VPN; #50 asks tsnet);
Basic-Auth opencode servers break discovery (#53/54); model picker resets on tab refocus (#49); mobile code-block clipping (#51).

**Deploy:** `bunx openportal` / `npm i -g openportal`, self-host on VPS + Tailscale.

## 4. shuv1337/oc-web (74★, ARCHIVED → Latitudes-Dev/shuvcode)

**Stack:** TanStack Start + React + Bun, server-side API proxy (`server.ts`), Tailwind, PWA. MIT.

**Architecture:** browser never touches opencode directly — all traffic through `/api/*` proxy; SSE timelines;
`--external-server` attaches remote.

**Features:** mobile-first PWA, leader-key nav, session continuation, command-output panels, file preview w/ syntax highlight, model/agent/theme/MCP/LSP status surfaces.

**Limitations:** archived; no auth (Cloudflare Access/VPN). Successor: shuv.ai.

## 5. joelhooks/opencode-vibe (178★) — modern RSC/streaming approach

**Stack:** Bun monorepo: `apps/web` **Next.js 16 canary** (App Router/RSC, Tailwind v4, shadcn/Radix), `packages/core`
(Effect + effect-atom "world stream", zustand), `packages/react` hooks. `@opencode-ai/sdk`, Vercel AI SDK, shiki, `@xyflow/react` graph, `@pierre` diffs. MIT.

**Architecture:** auto-discovers running opencode via `lsof`; Next.js route **spawns `opencode serve --port X` detached**
per project (`api/opencode/servers/spawn`), **reverse-proxies full HTTP API + SSE** (`api/opencode/[port]/[[...path]]`,
`api/sse/[port]`); world-stream pub/sub pushes to UI.

**Features:** realtime streaming, SSE sync, slash commands, fuzzy `@` file refs, multi-server project switcher,
provider/model pages, context-usage meter, compaction indicator, chain-of-thought, tool cards, subagent view,
React-Flow canvas/node/edge views, artifact/web preview, PWA manifest + mobile guide.

**Limitations:** Next 16 canary "rough edges"; dependabot issues (proxy body-forwarding bugs fixed); no auth; solo/experimental.

## 6. Ecosystem — other opencode clients (from awesome-opencode)

- **Native/mobile:** CodeWalk (Flutter, all platforms) · OpenCode Mobile (dzianisv, Android/F-Droid, **approve tool calls from phone**) · P4OC (Android, Google Play, embedded terminal) · grapeot iOS (SwiftUI) · oc-remote (Android).
- **Desktop:** OpenWork (Cowork-like GUI) · OpenChamber (web+desktop, VS Code ext, git worktrees) · Deck (sandboxed cockpit + noVNC) · NextProb (Electron) · OpenAgent (control plane: Next.js + SwiftUI iOS).
- **Chat bridges:** Open Dispatch (Slack/Teams/Discord) · opencode-telegram-bot · MCP Voice Interface.
- **TUI:** Agent of Empires, agenttrace, oc-manager.

## Synthesis — what the winners share and what's missing

Common architecture: backend spawns `opencode serve`, single API + SSE bridge, thin browser client.
Missing everywhere: **mobile-first with auth + push that approves permissions/tool-calls from the phone**
(only the two Android apps do approvals today). Biggest unclaimed gap.
