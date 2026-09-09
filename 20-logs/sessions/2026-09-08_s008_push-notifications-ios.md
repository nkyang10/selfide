# s008 — Push notifications for iOS web (web push)

- **Date:** 2026-09-08 (UTC)
- **Project:** p003-opencode-fork (app = `packages/app`, server = `packages/opencode`)
- **Type:** research + implementation + runbook
- **Status:** COMPLETE — research + server-side impl held here; client side implemented in **s009**
  (2026-09-09, `20-logs/sessions/2026-09-09_s009_ios-push-client.md`). Server work was left uncommitted
  in the repo (`packages/opencode/src/push/`, `src/server/push/`, wiring + `web-push` dep).

## Goal (user request)

On iOS in a web page/PWA, an LLM request may take a long time. User wants to run it in the
background (leave the tab / use another app), and be notified when a session finishes, so they
can come back and check the result. Notification must fire only when the session reaches a
complete/finished state.

## Key research findings

1. **iOS cannot keep a background tab alive / poll.** Safari suspends background tabs; there is no
   reliable "background polling" from a web page on iOS. The only dependable mechanism is **Web Push**:
   the browser never has to be open — the *server* sends the notification, iOS wakes a brief
   service-worker `push` event to display it. (WebKit is the only engine on iOS; other browsers are
   wrappers.)
2. **Prerequisites** (verified):
   - Requires an **HTTPS** origin. LAN `http://192.168.1.249:4447` is **NOT** a secure context.
     Verified in WebKit source `Source/WebCore/page/SecurityOrigin.cpp:90-110`:
     `shouldTreatAsPotentiallyTrustworthy` is true only for secure schemes, `localhost`/loopback,
     and local schemes. A private IP is not on that list, so `PushManager`/`Notification` are gated.
   - Add to **Home Screen** once (iOS 16.4+) → installs like an app; iOS shows the Allow-flags prompt
     on a user tap.
   - No Apple Developer Program membership needed.
   - Service worker usable (only a *brief* wake; do not do network fetch loops from SW on iOS — use
     server push).
3. **Delivery**: server uses **VAPID** (self-managed keys, no third-party service) → talks to the
   browser's push service (APNs on iOS) per RFC 8030/8291. `web-push` npm lib works on Bun now
   (Bun AES-GCM bug fixed, verified via oven-sh/bun#6455).
4. **Completion hook**: `SessionStatus.set()` (packages/opencode/src/session/status.ts) publishes
   `session.status` with `{ sessionID, status: { type: "idle" } }` (and deprecated `session.idle`)
   when a session finishes. This is the exact "complete finish state" the user wants.

## Access path (chosen by user)

`cloudflared tunnel --url http://localhost:4447` → gives an instant **https** `https://<random>.trycloudflare.com`
origin the phone can reach, satisfying the secure-context requirement.

## Implementation plan

- **Server** (`packages/opencode`):
  - Add `web-push` dependency + a `Push` service (LayerNode) exposing:
    - `pubKey` application-server key (generated once, persisted under global state dir).
    - `subscribe/unsubscribe` (store subscriptions keyed by serverKey/url).
    - Long-lived background subscription on `session.status` → when `status.type === "idle"`,
      resolve session title/directory and `webpush.sendNotification` a matching `data` payload
      (title = session title, body = finished, url = `/{dir}/session/{id}`).
  - HTTP endpoints under a new `push` group: `GET /push/pubkey` (public VAPID key),
    `POST /push/subscribe`, `POST /push/unsubscribe`.
- **App** (`packages/app`):
  - `public/sw.js` service worker: `push` → `showNotification`; `notificationclick` → close +
    focus/open the session URL. Register via the app entry.
  - Manifest `display: standalone`, add `start_url`/icons already present; add to-home-screen
    instructions + an in-app "Enable notifications" button that requests permission and registers
    the subscription.
- **Runbook**: `30-runbooks/rb-003-push-notifications.md` with key management, cloudflared command,
  iOS Add-to-Home-Screen flow, and testing steps.

## Open decisions / follow-ups
- TBD (write at close-out).
