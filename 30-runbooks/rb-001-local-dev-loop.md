# RB-001: Local dev loop (web UI ↔ opencode serve)

**Risk level:** low
**Applies to:** dev-station
**Prerequisites:** `opencode` CLI installed; project p001 cloned/bootstrapped

## When to use
Every time you iterate on the web UI: run opencode's server, run the UI dev server, open the PWA, verify streaming.

## Procedure
1. Start an opencode server (headless) for the UI to talk to:
   ```bash
   opencode serve --port 4096 --hostname 127.0.0.1
   ```
2. Verify the API is up: `curl http://127.0.0.1:4096/global/health` → `{"healthy":true,…}`
   and the OpenAPI spec at `http://127.0.0.1:4096/doc`.
3. Start the web UI dev server (see `50-projects/p001-opencode-web-ui/README.md`).
4. Open the UI in a desktop browser, then in a phone/tablet browser on the same LAN
   (or via Tailscale) to exercise the mobile path.
5. Watch the SSE stream: `curl -N http://127.0.0.1:4096/event` → expect `server.connected` first.

## Verify success
- Health endpoint 200; UI shows live session list; sending a message streams parts in real time.

## Rollback
- Kill the dev servers (`Ctrl-C` / kill PID). Nothing persistent is touched.

## Log
Append every step's result to `20-logs/command-log.md`; update `10-status/current-state.md`.
