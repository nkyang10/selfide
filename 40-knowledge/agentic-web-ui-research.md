# Agentic Web UI — Research (7-level deep dive, 2026-09-07)

> Compiled from 4 parallel research tracks (github API sweeps + deep dives on ~20 projects + UX literature).
> Purpose: field notes for building a **better agentic web for opencode, mobile-multitasking first**.

> Companions: `opencode-webui-landscape.md` (full Level-4 deep dives per project) ·
> `mobile-multitasking-acp.md` (Level-5 multitasking/ACP/native-mobile details) ·
> `opencode-server-api.md` (the server engineering interface).

## 1. Landscape — existing opencode web/mobile clients

> Full detail per project (architecture, features, open issues, deploy): `opencode-webui-landscape.md`.

| Project | ★ | Takeaway |
|---|---|---|
| siteboon/claudecodeui (CloudCLI) | 13.6k | Best arch docs (websocket transport, lazy pagination) + permission UI + PWA — but drives Claude/Cursor/Codex, **not opencode**, opencode only as provider |
| chriswritescode-dev/opencode-manager | 871 | Most complete web UI: **supervises opencode processes**, Better Auth, cron, VAPID push, Plan/Build, SSE bridge, Docker |
| hosenur/portal | 797 | **Leanest mobile-first** baseline: React19 + Nitro + `@opencode-ai/sdk`, session fork/revert; no auth |
| joelhooks/opencode-vibe | 178 | Next.js 16 + Effect "world stream", spawns a server per project, subagent graph; experimental |
| shuv1337/oc-web → Latitudes-Dev/shuvcode | 74 | TanStack Start proxy; archived, no auth |
| zn? stablyai/orca | 62k | Desktop ADE + mobile companion, push-on-finish, worktree splits |
| getpaseo/paseo | 16k | Daemon (WS :6767) + SDK + Expo mobile + relay; parallel agents |
| happier-dev/happier | 1.6k | **E2EE** native + web; global Inbox for approvals, pending/offline queue, session handoff |
| nimbalyst | 1.7k | Kanban + WYSIWYG diff approval + native iOS companion (swipe diff, tap approve) |
| agent-of-empires | 3.2k | tmux-backed agents = sleep/wake; dedicated structured phone view |
| agentrq | 1.1k | Human-in-loop task board over MCP; ACP gateway |
| zhukunpenglinyutong/desktop-cc-gui | 4.2k | Tauri multi-engine desktop (no mobile) |
| Native mobile | — | dzianisv/opencode-mobile (Android, approve-from-phone), grapeot swiftui iOS, crim50n/oc-remote (Android, richest: WS PTY, offline cache, wakelock), grinev/opencode-telegram-bot (zero open ports, outbound only) |
| ACP bridging | — | formulahendry/acp-ui (Tauri+Vue, stdio→wss via dev tunnels), beyond5959/ngent (Go stdio→HTTP/SSE) |

**Landscape conclusion:** the standard architecture for any custom UI = a backend that spawns/orchestrates
`opencode serve` and re-exposes a single API + SSE bridge; browser is a thin client. The unclaimed gap:
**a truly mobile-first (PWA) UI with auth + push that can approve permissions/tool-calls from the phone.**

## 2. Engineering facts that constrain the design

- opencode server = **REST + SSE only** (no WS/JSON-RPC); `GET /event` SSE stream; `/doc` OpenAPI 3.1; SDK `@opencode-ai/sdk`.
- opencode **implements ACP too** (`opencode acp`, stdio JSON-RPC, JSON-RPC 2.0). Browsers can't spawn stdio → ACP only via a bridge. **Not needed** for our single-harness UI.
- Auth: HTTP Basic (`OPENCODE_SERVER_PASSWORD`); official web is desktop-oriented + cluttered on mobile (#11828, #5126).
- Details → `opencode-server-api.md`.

## 3. UX patterns that make an agent UI "better" (vs raw terminal echo)

1. **Intent preview / plan gate** — plain-language plan before risky actions, `[Proceed][Edit][Handle myself]`.
2. **Autonomy dial** — per-task risk level (Observe→Plan→Confirm→Act) instead of global y/n.
3. **Collapsed tool-call trees** — one line per call, args/result folded, errors flagged (4h session ≈ 180+ calls).
4. **Step timeline Plan→Act→Review** — activity rail, not a flat log (Linear Agent: Activity|Guide|Diff|Submit|Preview).
5. **Inline diff chips + staging** — `+34/−18` per file, tap-to-open, explicit Submit-review gate.
6. **Interrupted-approval modal** — persistent, **queued**, survives network drop, answerable from another device.
7. **Streaming token/energy meter + cost panel** — live tok/s, context window, running $.
8. **Triage inbox / task queue** for multiple concurrent agents.
9. **Async handoff** — "Check in from your phone"; push only on **done** or **needs-decision**.
10. **Explainable rationale + audit & undo** — "because you said X, I did Y" + time-limited undo.

## 4. Where existing UIs fall short (the opportunity)

- Jules: no usable diff viewer, state only refreshes at todo boundaries, can't steer mid-run.
- Claude Code GUI: worktree isolation problems, "solving problems I don't have".
- opencode web: cluttered/overlapping on mobile, not touch-optimized, no push, no installability.
- Most 3rd-party opencode UIs: thin SSE chat wrappers — no plan gate, no queue, no notifications, no PWA.
- **Systemic gap: everything optimizes for "watch the agent work live" (desktop). Almost none optimize for async mobile multitasking.**

## 5. Mobile/PWA best practices (apply to an agent control panel)

- App shell + offline-first; cached session list in IndexedDB; Background Sync + foreground flush; explicit conflict resolution.
- Web Push + **Badging API**; push only on the two event classes (done / needs-decision).
- Bottom tab bar (3–5 destinations: Inbox, Sessions, Diffs, Settings); bottom sheets for approvals/diffs.
- Safe areas (`viewport-fit=cover`, `env(safe-area-inset-*)`); gestures: swipe approve, long-press inspect, pull-to-refresh.
- Keepalive vs NAT (`$/ping` patterns), reconnect-on-focus; offline read-only cache + batch catchup; biometric-gated sends.

## 6. Recommended MVP for p001 (mobile-multitasking web UI)

1. **Session control plane** — list/start/resume opencode sessions from phone (SSE live view). *Foundation.*
2. **Async notifications** — push + badge on task done / needs-decision only. *Killer feature.*
3. **Queued permission approvals** — approve/reject tool calls from phone (persisted queued modal).
4. **Panic controls** — pause / stop / take-over on any session from anywhere.
5. **Collapsed tool-call tree + inline diff chips; deep-link into diffs.**
6. **Plan gate + autonomy dial.**
7. **Offline shell** — cached session list + queued messages, conflict notice.
8. **Per-session token/cost meter.**
9. **Triage inbox / task queue** for multiple concurrent agents.

*Ordering rationale: 1–4 are cheap over the server's SSE stream and alone differentiate the product; 5–9 are polish.*

## Key sources

opencode docs (server/web/ecosystem/acp) · awesome-opencode/awesome-opencode · smashingmagazine.com agentic-UX · linear.app/ai · code.claude.com/docs/en/remote-control · agentclientprotocol.com · MDN PWA guides · ngGroup bottom-sheets · GitHub issues: anomalyco/opencode #11828, #5126.
