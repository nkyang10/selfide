# Mobile Multitasking & ACP — research notes (Level 5, 2026-09-07)

> Deep dive on multi-agent orchestration UX, the ACP protocol, native mobile opencode clients, and
> notification mechanisms. The "how do we do mobile multitasking right" reference for p001.

## 1. Multi-agent tools — the multitasking UX mechanisms

| Tool | ★ | Mechanism to steal |
|---|---|---|
| CloudCLI/claudecodeui | 13.6k | Session list + per-session chat tabs (not split panes); plugin system (task-queue, scheduler); REST API; responsive in real browsers; CloudCLI Cloud removes "machine must stay on" |
| agent-of-empires | 3.2k | Each agent = persistent **tmux session** (detach/reattach = sleep/wake, survives SSH drops); laptop = full dashboard/terminal/diffs, **phone = dedicated "structured view"**; status detection (running/waiting/idle/error); notifications; worktrees; `acp-worker` |
| happier-dev/happier | 1.6k | **Best-in-class multitasking**: global **Inbox** aggregating permission requests/AskUserQuestion/ExitPlanMode across sessions; **pending queue** (edit/reorder/drop while busy or offline); steering/interrupts; session **fork/replay/handoff between machines**; attach/follow live terminals; voice answers approvals; E2EE (TweetNaCl) + relay |
| agentrq | 1.1k | Human-in-loop **task board/kanban** + chat thread (not a streamer): cron tasks, event-driven workflows, tool-call history timeline, **send-delay/cancel**, in-browser STT; connects agents via MCP; ACP gateway bridges other agents |
| paseo | 16k | Daemon (WS :6767) + SDK + **Expo mobile** + Electron + CLI; parallel agents incl. opencode; worktrees; voice dictation; E2E relay w/ QR "Pair Device" |
| orca | 62k | Desktop ADE + mobile companion: monitor/steer, **push when agent finishes**, follow-ups; desktop has worktree splits, Ghostty-class terminal splits, annotate-AI-diff |
| desktop-cc-gui | 4.2k | Tauri multi-engine (Claude/Codex/Gemini/OpenCode/DeepSeek-Harness); queues follow-ups while busy; desktop only |
| nimbalyst | 1.7k | Session **kanban**; red/green WYSIWYG diff approval; native iOS companion: **swipe-through diffs, tap-to-approve, task queueing, push when agent waits**; sync via Cloudflare Worker (wss) |
| agentrq-style org | — | The "board" mental model (task/human-in-loop) vs the "stream" model (all others) — p001 should decide which to lead with |

## 2. ACP (Agent Client Protocol) — what it is, whether opencode supports it

- **What:** JSON-RPC 2.0 (LSP-analog) standardizing agent↔editor communication. **v1 stable, v2 draft.**
- **Transport:** stdio is the norm (spawn agent subprocess). **Streamable HTTP draft-only; WebSocket = community custom transport. No official remote spec.**
- **Agents implementing it:** Claude Agent, Codex, Gemini CLI, GitHub Copilot (preview), Cursor, **OpenCode**,
  Qwen, Kimi, Kiro, Junie, Cline, Goose, Pi, Mistral Vibe, Factory Droid, OpenHands, Augment, Hermes, OpenClaw + more.
- **OpenCode: YES** — `opencode acp` over stdio; full parity except `/undo`,`/redo` (repo now `anomalyco/opencode`).
- **Browser UI via ACP:** browsers can't spawn stdio → bridge stdio→network. References:
  - `beyond5959/ngent` (Go) wraps ACP agents into HTTP/SSE web service + embedded mobile UI + permission control.
  - `@rebornix/stdio-to-ws` + Microsoft Dev Tunnels → `wss://` (pattern used by `formulahendry/acp-ui`, Tauri+Vue, mobile, traffic monitor, `$/ping` keepalive, session resume on focus).
- **p001 decision (DEC-003):** one-harness UI → skip ACP, use opencode's native HTTP+SSE server API. ACP only matters if we later want multi-harness.

## 3. Native mobile opencode clients — how they reach the machine

| Client | Stack | Transport/how it reaches host | Notable |
|---|---|---|---|
| dzianisv/opencode-mobile | RN/Expo, Android (Play/F-Droid/APK) | Speaks opencode **HTTP+SSE directly**; LAN/Cloudflare Tunnel/ngrok/**Tailscale** | streaming chat, **diff viewer, tool-call approval**, biometrics, multi-server |
| grapeot/opencode_ios_client | SwiftUI iOS/iPadOS/visionOS, TestFlight | LAN, HTTPS+BasicAuth, or built-in **SSH tunnel (Citadel)** | native |
| crim50n/oc-remote | native Android (Material 3) | multi-server, SSE, **WebSocket PTY terminal**, on-device Termux runtime | **offline read-only cache**, wake-lock, reconnect backoff, MCP mgmt — richest |
| grinev/opencode-telegram-bot | Node/grammY | **outbound-only to Telegram, zero open ports** | sessions, /abort, /detach, /worktree, message queue, scheduled tasks |
| termly-cli | PTY-wrap of 23+ CLIs | E2EE central `wss://api.termly.dev` relay | mobile app "coming soon" |
| doza62/opencode-mobile | RN/Expo iOS/Android/Web | tunnel + QR | Expo push |

**Reach patterns:** LAN, Tailscale, Cloudflare/ngrok tunnel, SSH tunnel, or central encrypted relay. No consensus — pick by deployment target (FU-002/FU-006).

## 4. Notification mechanisms ("agent finished" on mobile)

AgentRQ/CloudCLI: none real. Telegram push (grinev) · Expo push (doza62) · native push (Orca/Nimbalyst) ·
Happier inbox + tap-to-session · OC-Remote toasts + background SSE with wake-lock · Termly push (v1.5) ·
web clients = SSE/WS + reconnect-on-focus (acp-ui). **For a PWA: Web Push + Badging API is the zero-native-build answer.**

## 5. Mobile agent-UI best practices (observed across all)

- Pinned live-status message with model + worktree + context.
- Hold-in-queue while busy/offline, editable before send (Happier; AgentRQ send-delay).
- **Structured phone view vs desktop terminal** (agent-of-empires) — a phone is not a text console.
- Red/green **swipe-through tap-to-approve diffs** (Nimbalyst, dzianisv).
- Inline approve/deny + **ordered interaction queue** (oc-remote).
- Foreground reattach via session/resume + `--persist` bridges; `$/ping` 25s keepalive vs NAT.
- Offline read-only cache + batch catchup (oc-remote, termly).
- **Biometric-gated sends** (dzianisv).

**Bottom line:** Happier (native, E2EE, inbox/queue UX) and Paseo (open daemon+SDK+web) are the closest full
references. For browser-first, Paseo-style daemon over WebSocket + opencode's own HTTP/SSE server API is simpler than ACP.
