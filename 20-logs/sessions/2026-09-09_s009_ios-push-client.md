# s009 — iOS push notifications: client/service-worker side

- **Date:** 2026-09-09 (UTC)
- **Project:** p003-opencode-fork (app = `packages/app`, server = `packages/opencode`)
- **Resumes:** s008 (research + server-side partial) — s008's server work found uncommitted
- **Type:** implementation
- **Status:** COMPLETE

## Result

Client side of iOS web push implemented and verified. Server side (s008) typechecks; this session added
the service worker + subscribe flow + settings toggle.

### Client (packages/app)
- `src/utils/web-push.ts` (+ `web-push.test.ts`) — `webPushSupported()` (guards SW/PushManager/secure
  context), `enableWebPush()` (register SW → `Notification.requestPermission()` → `/api/push/pubkey` →
  `pushManager.subscribe` → POST `/api/push/subscribe`), `disableWebPush()` (get sub → POST
  `/api/push/unsubscribe` → `unsubscribe()`), plus `useWebPushEnabled()`.
- `public/sw.js` — `install`(skipWaiting)+`activate`(clients.claim); `push` → `showNotification` (title/body,
  icon/badge); `notificationclick` → focus existing or open payload `url` (now deep-links to session: server
  sends `{title, body, url}` top-level, SW reads `payload.url`).
- `src/context/settings.tsx` — `NotificationSettings.webPush` (default false) + `webPush()`/`setWebPush()`.
- `src/components/settings-general.tsx` — "Background notifications" toggle in Notifications section
  (`data-action=settings-notifications-webpush`), `selectWebPush()` async on/off, disabled while busy /
  unsupported.
- `src/entry.tsx` — register `/sw.js` at startup when supported+secure and not the app.opencode.ai proxy.
- i18n: keys added to `en.ts`, `zh.ts` (translated), and the other 60 locales (English fallback to satisfy
  the i18n-parity test that now asserts identical key sets).

## Verification
- `packages/opencode` typecheck: clean (s008 server code).
- `packages/app` typecheck (`tsgo -b`): clean.
- `packages/app` unit `--conditions=solid ./src`: **729 pass / 104 files / 0 fail** (incl. i18n parity + new
  web-push.test).
- `packages/app` browser `./test-browser`: **41 pass / 14 files / 0 fail**.
- `bunx vite build` from clean `dist/`: succeeds; `dist/sw.js` + `dist/site.webmanifest` emitted.
- Serve path: `createEmbeddedWebUIBundle` globs all of `packages/app/dist` → `/sw.js` served with
  `application/javascript` (valid SW type) and `/site.webmanifest` as `application/manifest+json` via
  `FSUtil.mimeType` (mime-types lookup).

## iOS requirements (documented, verified against WebKit source in s008)
- Origin must be HTTPS (secure context) — LAN `http://192.168.1.249:4447` is not. Use the chosen access path:
  `cloudflared tunnel --url http://localhost:4447` → `https://<rand>.trycloudflare.com`.
- Must be added to Home Screen once (iOS 16.4+) — manifest already `display: standalone` + `start_url`.
- The "Background notifications" toggle click is the required user gesture for `Notification.requestPermission()`.
- SW must not do network-loops on iOS — web-push is server-initiated, so this is satisfied by design.

## Review + commit + push (later same day, UTC 04:10–04:18)

- **Reviewed** all uncommitted FE-005 (s008 server + s009 client):
  - `bun.lock`: bun install pruned 37 **dead** entries (unreferenced `@vitest/coverage-v8` suite +
    `@standard-community/*` with their `effect@beta.74`/`@standard-schema/spec`) while adding `web-push` +
    `@types/web-push` + transitive deps. Verified none are referenced by any workspace package.json, no
    coverage scripts exist, catalog `effect@beta.83` unchanged → **kept** (internally consistent; reverting
    would break `--frozen-lockfile` CI).
  - **Fixed**: `httpapi/server.ts` had `disableLogger: false` (a s008 debug aid) → reverted to `true`.
    Removed dead `useWebPushEnabled()` hook + unused `createResource` import from `web-push.ts`.
- **Re-verified**: opencode + app typechecks clean; app unit **729 pass / 0 fail**.
- **Commit**: `b922fe4` "feat(app,core): send web push notifications when a session finishes (FE-005)"
  (73 files, +617/−37). Working tree clean.
- **Push**: to the fork `origin` (nkyang10/opencode) per `p003/README.md`. Shallow clone base `ecbc6cc`
  matched `origin/dev`, so it fast-forwarded. First attempts failed (no HTTPS cred helper; `ssh -T
  git@github.com` denied). Pushed with the user's PAT via a temp `GIT_ASKPASS` (token in env only, never
  written to `.git-credentials`, repo config, or disk) and `PATH+=~/.bun/bin` so the husky **pre-push**
  hook's typecheck (30/30 tasks) passed. Result: `ecbc6cc..b922fe4 dev -> dev`. Temp askpass removed.
- **Deployment note**: FE-005 is now in `origin/dev` and ahead of the running :4447 binary (built before
  these commits). A rebuild + restart is needed to make it live; the toggle still needs an HTTPS origin
  (cloudflared tunnel) before iOS will enable it (FU-025).

## Deployment + FE-005 live (later same day, UTC 04:25–04:55)

- **Audit**: the running server was :4445 = `~/.opencode/bin/opencode` (official build 08-25, NO FE-001..005).
  The :4447 instance had been stopped; the fork binary predated FE-005.
- **Rebuilt** with `build-linux.sh` at HEAD `b922fe4` → binary `0.0.0-dev-202609090450`. Started :4447
  (`run-web.sh`) behind the `hahahaha` login (pid 2415340).
- **Found a blocking bug**: `GET /sw.js` returned **401** because `PUBLIC_UI_PATHS`
  (`server/shared/public-ui.ts`) auth-gates static UI paths but was missing `/sw.js` → a browser behind
  the login page could never register the service worker, so web push was impossible.
- **Fix**: add `/sw.js` to `PUBLIC_UI_PATHS` (public on GET, same as manifest/icons). Server typecheck
  clean. Rebuilt (`0.0.0-dev-202609090452`) + restarted :4447. Verified: `/sw.js` 200
  `text/javascript` (has install/activate/push/notificationclick), `/site.webmanifest` 200
  `application/manifest+json`, `/login` 200, unauthed `/` 401, unauthed `/api/push/pubkey` 401 (gated — correct).
- **Commit + push**: `e0511c4` "fix(server): serve /sw.js publicly so service worker can register behind
  login" → pushed `b922fe4..e0511c4 dev->dev`. Tree clean. Pre-push typecheck 30/30.
- **Net state**: FE-005 (server + client + sw.js gate fix) is now **committed, pushed, and live on :4447**.
  The only remaining step for a real iPhone is an HTTPS origin (cloudflared tunnel) + Home Screen add.

## Cloudflare HTTPS tunnel (UTC 05:05–05:12)
- Installed `cloudflared` 2026.8.3 (linux-arm64) to `~/.local/bin/`. Added `scripts/start-tunnel.sh`
  (mirrors the `run-web.sh` detach pattern; target defaults to `http://localhost:4447`), because inline
  `setsid nohup … &` got killed when the tool command ended — the script pattern survives.
- Quick tunnel pid 2417167: **https://surgeon-waiver-bell-imagination.trycloudflare.com**
  (conn hkg01, quic; ICMP ping WRN about ping_group_range is harmless). Verified through the public HTTPS
  origin: `/login` 200, `/sw.js` 200 `text/javascript`, unauthed `/` 401.
- Important: trycloudflare URL is **ephemeral** — dies with the cloudflared process and changes on each
  restart. Persistent HTTPS would need a named CF tunnel (domain) or Tailscale.

## Token storage (this session)
- Config: `git config credential.helper store` (repo-local). Wrote user PAT as `x-access-token` to
  `~/.git-credentials` (chmod 600, in home dir, **not** in the project). Verified `ls-remote` + push
  authenticate without a prompt. Not committed anywhere; repo is secret-free.

## Quirks / gotchas recorded
- Server push payload carries the session URL at the **top level** (`{title, body, url}`); SW reads
  `payload.url` into notification data for deep-linking (initial SW version read `payload.data.url` and fell
  back to `/` — fixed).
- `window.isSecureContext` is `undefined` (not `false`) in happydom; tests assert `not.toBe(true)`.

## Follow-up (outside this session)
- HTTPS origin must actually be stood up before the toggle will work on the real iPhone (FU-020/FU-025).
- `httpapi/server.ts` diff from s008 flips `disableLogger` to `false` — confirm intent or revert before commit.
- SW cache-control on the real origin (avoid stale SW on updates).

## Resuming state

s008 (2026-09-08) researched Web Push for iOS and left the **server side implemented but
uncommitted** in the repo (`packages/opencode/src/push/push.ts`, `src/server/push/route.ts`,
wiring in `httpapi/server.ts`, `web-push` + `@types/web-push` in package.json). Session marked
IN PROGRESS; frontend (service worker + client subscribe) not started.

## Goal (from s008)

Notify the user on iOS when an LLM session finishes. iOS suspends background tabs so a web page
cannot poll; the server must send a **Web Push** (RFC 8030/RFC 8291, VAPID). Notification must
fire only when a session reaches its finished/idle state. Requires HTTPS origin. iOS web push
additionally requires the site be installed to the home screen (PWA), the SW handles the `push`
event.

## Server side already present (uncommitted, verify)

- `push/push.ts` — Push layer: VAPID key generate/persist, subscribe/unsubscribe store
  (subscriptions.json), sends notification on session idle event.
- `server/push/route.ts` — GET `/api/push/pubkey`, POST/DELETE `/api/push/subscribe` (auth-gated).
- `httpapi/server.ts` — `Push.node` layered in, `pushRoute` added, VAPID pubkey logged.
- Note: server.ts diff also flips `disableLogger: false` → **scope to confirm as debug-only**.

## Missing (this session)

- [ ] Frontend service worker (`public/sw.js`): `push` event → `showNotification`; `notificationclick`
      → focus/reopen session.
- [ ] Client subscribe/unsubscribe module tied to logged-in state + permission flow, uses VAPID pubkey.
- [ ] iOS PWA wiring: SW registration, manifest already present; verify HTTPS requirement documented.
- [ ] Build + typecheck + verify.

## OUT OF SCOPE / user decision pending (from s008)

- HTTPS origin deployment (LAN http is not secure context) — needs FU on deployment target.
- Whether toggling notifications off per-session; UI toggle placement.
