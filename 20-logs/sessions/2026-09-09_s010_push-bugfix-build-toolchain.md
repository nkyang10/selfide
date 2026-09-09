# s010 — FE-005 push endpoints 500 fix + build toolchain pin

- **Date:** 2026-09-09 (UTC)
- **Project:** p003-opencode-fork (server = `packages/opencode`, scripts in `50-projects/p003-opencode-fork/scripts/`)
- **Resumes:** s009 — tunnel URL delivered; user then reported `GET /api/reference?...` → 500 `UnknownError`
- **Type:** bugfix (deployed twice)
- **Status:** COMPLETE

## Result

Two distinct defects found and fixed; redeployed on :4447; same ephemeral tunnel URL still serving.

### Bug 1 — compiled binary crashed on every v2 endpoint (`/api/reference` et al.)
- Reproduced: every location-scoped v2 endpoint (`/api/reference`, `/api/agent`, `/api/model`,
  `/api/fs/list`, ...) 500s on :4447 with `TypeError: undefined is not an object (evaluating 'a.name')`
  in `effect` schema/app-node `resolve`/`recur` inside `LayerNode` `hoist`/`compile`.
- Isolated by building a **pristine upstream `ecbc6cc`** worktree → identical crash. So NOT a fork regression.
- Running the server **from source** (`bun run ./src/index.ts web`) → 200 for all those endpoints.
- Root cause: **local bun 1.4.2 compiler** embeds a broken app-node/schema graph. Repo pins the official
  toolchain `bun@1.3.14` (`packageManager`); rebuilding the single-file binary with bun 1.3.14 fixes all
  endpoints (verified `/api/reference|agent|model|location|command|provider|fs/list|integration|session*`
  → 200).
- **Fix:** `scripts/build-linux.sh` now downloads/uses the pinned bun 1.3.14
  (`~/.cache/opencode-build/bun-1.3.14`), inferring OS/arch from `uname`. Upstream `build.ts` left untouched
  (a temporary `NO_MINIFY` diagnostic edit was reverted).

### Bug 2 — `@opencode/Push` service unresolvable → push endpoints 500 (FE-005 was never live)
- `GET /api/push/pubkey`/`POST /subscribe|unsubscribe` returned `500 Service not found: @opencode/Push`
  when authenticated (s009 only ever tested the unauthenticated 401 gate, so this was invisible).
- Root cause: `route.ts` requested `Push.Service` inside **request-time** handler effects; raw
  `HttpRouter` handlers have no service environment. Working routes (login/SPA) resolve services at
  **router-construction time** inside `HttpRouter.use`'s `Effect.gen`.
- **Fix (`40b1633`):** resolve `Push.Service` once while the router layer is built, capture into handler
  closures. Verified from source AND in the deployed binary: `/api/push/pubkey` 200 (VAPID key), unauth 401;
  subscribe/unsubscribe 200 `{ok:true}`.

## Verification
- Server typecheck clean; `packages/opencode` full suite `LANG=C` → 3527 pass / 22 skip / 45 fail; all 45 are
  pre-existing environmental failures (ACP/CLI-TUI/plugin/network/locale — none touch push/httpapi; the 2
  `project-copy` locale failures pass with `LANG=C`).
- Deployed binary restarted on :4447 (pid 2485843, `0.0.0-dev-202609090736`, rebuilt with bun 1.3.14):
  login 200, `/sw.js` 200, manifest 200, `/` 401, unauth pubkey 401, auth: pubkey/reference/agent/model/
  fs-list/integration/session/session-active all 200, subscribe/unsubscribe 200.
- Tunnel `https://surgeon-waiver-bell-imagination.trycloudflare.com` (pid unchanged) re-verified end-to-end:
  login 302, pubkey 200, reference 200, `/sw.js` 200. :4445 official binary untouched.

## Artifacts
- Commit `40b1633` pushed to `origin/dev` (`fix(server): resolve Push.Service at router build ...`).
- `scripts/build-linux.sh` toolchain pin (ide repo, uncommitted with this session's doc updates).
- push state cleared back to `[]` (test subs removed) in `~/.local/state/opencode/push/subscriptions.json`.

## Next
- iPhone field test (FU-025 still open): add tunnel URL to Home Screen → login `hahahaha` → Settings →
  General → System notifications → "Background notifications" → run a session to completion → expect OS
  notification deep-linking to the session.
- Stable HTTPS (named CF tunnel / Tailscale) still optional; SW cache-control decision still open on the
  real origin.

## Addendum (same session) — web mobile "Thinking" row stuck
- **Symptom:** on web mobile, prompts submit and responses complete, but the "Thinking" row never dismisses.
- **Root cause (narrowed by empirical reproduction, not theory):** drove the live tunnel UI with Playwright
  (installed chromium-headless-shell) and instrumented the pipeline (probes at RX/EMIT/store/timeline). The
  app's live event stream is **entirely silent through the quick Cloudflare tunnel**: `curl` to
  `/global/event` via the tunnel returns 200 + `text/event-stream` headers but **zero body bytes** for
  25+s (identity + gzip, HTTP/1 + HTTP/2, quic + http2 cloudflared protocols) while the same endpoint on
  localhost streams instantly. Cloudflare quick tunnels buffer the SSE body. So on the iPhone the app got
  message content only via refetches — and never got `session.status idle`, leaving the store `busy`
  forever. (The earlier "suspension loses idle" theory was real too, but the tunnel buffering is the
  dominant path — no suspension needed.)
- **Fix (`d1389e2` + `3e46b18`, deployed):** (1) refetch `activeSessionsQuery` on every `server.connected`
  and reconcile stale `busy`→`idle` in `seedActiveSessionStatuses` (covers reconnects + any event loss);
  (2) **status watchdog**: while any session is busy, re-poll `/session/status` every 15s (off when nothing
  is busy) so the Thinking row clears within ~15s of completion even with a completely silent stream.
  Verified end-to-end via the tunnel with Playwright: **RESULT: DISMISSED** (was STUCK before).
- **Limitation to note:** quick tunnels still buffer the SSE body, so live text streaming across the tunnel
  arrives via refetches with latency, not live events. A named tunnel/edge streaming may or may not fix
  parsing; the app-side watchdog makes status correct regardless.
- **Tunnel URL changed** (cloudflared relaunched with `--protocol http2` then back to default quic? no —
  final launcher unchanged `start-tunnel.sh`, default protocol): now
  `https://orlando-expansion-thu-toxic.trycloudflare.com`. OLD URL `surgeon-waiver-...` is dead.
