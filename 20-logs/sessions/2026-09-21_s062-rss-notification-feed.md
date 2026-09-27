# Session s062 — RSS notification feed (planning)

- **Date (UTC):** 2026-09-21
- **Session:** s062
- **Target:** p003-opencode-fork — server route + settings UI
- **Request:** New enhancement — per-user RSS feed served on the same port as the web
  UI, as a duplicate OK-free channel of the notifications opencode fires. No login /
  session required to read the feed; content is non-sensitive (tab title, tab URL).
  Feed URL carries an un-brute-forceable token (per user). URL is surfaced on the
  Settings page for copying.

## Status

PLANNING ONLY — no code changed. Plan below.

## Understanding (from code)

- Notification source: `packages/opencode/src/push/push.ts` `notifier` — watches the
  process-wide `EventV2` stream for `session.status` where `status.type === "idle"`,
  skips child sessions, resolves `title` via `session.get`, builds the in-app deep link
  `/{base64url(directory)}/session/{id}`, then sends a Web Push payload
  `{title, body, url}` to every subscribed browser (FE-004 / FE-005).
- Auth wall: `server/routes/instance/httpapi/middleware/authorization.ts` gates every
  route except `isPublicUIPath` / `isLoginPath`. Raw auth-only routes are layered in
  `routes/instance/httpapi/server.ts` `createRoutes()` (e.g. `pushRoute`).
- User concept today is single-instance: one Basic-auth credential
  (`OPENCODE_SERVER_USERNAME`/`OPENCODE_SERVER_PASSWORD`, DEC-041). There is no
  multi-account system, so "per user" maps to a per-deployment token (one RSS feed
  per server), designed to scale to future multi-user (token = hash of username+secret).
- Settings UI: `packages/app/src/components/settings-general.tsx`
  `NotificationsSection` (agent / permissions / errors / webPush toggles) — RSS URL
  row fits here. i18n keys in `packages/app/src/i18n/en.ts` `settings.general.notifications.*`.
- State persistence pattern: `Global.Path.state` JSON files (push uses
  `state/push/subscriptions.json` + `vapid.json`).
- Client base URL: `window.location.origin` (same origin as web UI).

## Proposed design

### Server — `packages/opencode/src/server/rss/`

New raw route `GET /rss/:token` mounted in `createRoutes()` WITHOUT the auth
middleware (feed is intentionally public-by-token).

- **Feed model** (`rss/feed.ts`): an in-memory ring buffer (per user token) of the
  last N (e.g. 20) notification entries, persisted to `Global.Path.state/rss/<token>.json`
  so feed survives restarts.
- **Token generation** (`rss/token.ts`): 32-byte CSPRNG (`crypto.randomBytes`) hex /
  base64url, persisted at `Global.Path.state/rss/tokens.json`. One token per
  configured username; if username changes a new token is issued (old one stays
  readable for a grace window). Token is the sole auth factor → un-brute-forceable
  (2^256).
- **Notifier** (`rss/notifier.ts`): same `EventV2` stream hook as push — on
  `session.status idle`, non-child, append `{ title, url, ts }` to the user feed.
  Reuses the exact title/url building logic (extract to shared helper).
- **Handler** (`rss/route.ts`): `GET /rss/:token` → RSS 2.0 XML (`<channel><item>…`),
  `Content-Type: application/rss+xml; charset=utf-8`, `Cache-Control: no-store`.
  Invalid token → 404 (not 401, to leak nothing). Optionally honor `?n=` for item count.
- Mount in `server.ts` `createRoutes()`: add `rssRoute` beside `pushRoute`, but do
  NOT provide `authOnlyRouterLayer` (public path).

### App — Settings row

In `settings-general.tsx` `NotificationsSection`, add a readonly row
**RSS feed URL** that:
1. Fetches the feed URL from a server endpoint (e.g. `GET /api/rss/url`, auth-gated —
   the only authed new endpoint; returns `{ url }`).
2. Renders it read-only + **Copy** button (reuse existing copy-icon pattern).

New i18n keys in `en.ts` (+ parity sync to all locales):
`settings.general.notifications.rss.*` (title / description / copy / copied).

### Security properties

- Feed contains only `title` (session title) + `url` (deep link to the session) +
  timestamp — non-sensitive by design; the deep link is behind the auth wall so a
  leaked feed token reveals titles/URLs only, never content.
- Token is 256-bit random → un-brute-forceable.
- Feed endpoint is rate-limited only by server default; optional simple per-token
  throttle if ever needed.

### Open questions for user

1. Feed content: only finished-session notifications (mirror push), or also
   question/permission/error events (mirror in-app notifications)?
2. Retain count (default 20) and feed TTL / pruning policy?
3. RSS path prefix: `/rss/:token` vs `/feed/:token` — cosmetic.
4. One token per deployment (single user today) vs pre-provision a "user slot"
   per username now?

## Verification plan

- Typecheck (`bun run typecheck`), oxlint.
- Unit test for token gen/validation + feed append/prune.
- Playwright / curl: unauth `curl /rss/<token>` → 200 RSS XML; wrong token → 404;
  authed Settings shows URL + copy works.
- Deploy per RB-003 (`scripts/deploy-web-4447.sh --detach`).
