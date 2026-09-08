# Session s004 — p003/FE-001: web login landing page (cookie auth, remember-me)

- **Date:** 2026-09-08 (UTC)
- **Goal (user spec):** replace the web auth UX with a typical login **landing page**:
  - Input the same credentials opencode uses (Basic auth `OPENCODE_SERVER_USERNAME`/`..._PASSWORD`).
  - **Remember-me checkbox** → persist auth "forever" (long-lived cookie).
  - Session/cookie auth that **carries over in iOS "Add to Home Screen" web shortcuts**.
  - Global failure path: any auth failure → login page.
  - After login → **redirect back to the originally requested path**.
- **Status:** ✅ COMPLETE — verified end-to-end. Running on :4447.

## Code changes (all in `p003-opencode-fork/opencode/`)

1. **`packages/server/src/middleware/authorization.ts`** (shared gate): added `oc_creds` cookie helper
   set (`AUTH_COOKIE`, `parseCookies`, `cookieAuthToken`, `authCookieHeader`, `clearAuthCookieHeader`,
   `isLoginPath`) and cookie → Basic-credential fallback in `credentialFromRequest`.
2. **`packages/opencode/src/server/shared/login.ts`** (new): landing page HTML (`loginPageHTML` with dark
   theme, username/password/remember-me), `loginPage` (GET), `loginSubmit` (POST — validates against
   `ServerAuth`, sets cookie, 302 to sanitized `next`), `logout` (clears cookie).
3. **`packages/opencode/.../httpapi/middleware/authorization.ts`**: cookie fallback in the router gate;
   skip `/login`+`/logout`; on browser (Accept: text/html) auth failure → **render login page 401** with
   `next`; non-browser keeps plain 401.
4. **`packages/opencode/.../httpapi/server.ts`**: `uiRoute` now mounts `GET /login`, `POST /login`,
   `GET /logout` before the SPA catch-all; config resolved in the router builder and passed into
   `loginSubmit` (request-time `ServerAuth.Config` was unavailable to raw routes — gotcha).

## Verification (curl, against rebuilt binary on :4447 with `OPENCODE_SERVER_PASSWORD` set)

| Check | Result |
|---|---|
| GET / as browser, no cookie | 401 + `Sign in · opencode` page (has "Save auth forever") |
| POST /login wrong creds | 401 + "Sign-in failed" banner (global fail path) |
| POST correct + remember=on | 302 → `/`; `Set-Cookie oc_creds=…; Max-Age=31536000; HttpOnly; SameSite=Lax` |
| POST correct, remember off | cookie **without** Max-Age (session cookie) |
| GET / with cookie | 200 → real OpenCode SPA `<title>OpenCode</title>` |
| GET /session with cookie only (no header) | 200 (API gate cookie bridging works) |
| GET /sessions/abc123 as browser | login page with `next=/sessions/abc123`; after login → 302 to it |
| GET /logout | clears cookie, 302 → /login |
| No password configured (regression, :4448) | 200 directly — login never shown |

## Results

- Binary: `p003-opencode-fork/opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode`
  (built s004 `0.0.0-dev-202609080057`); smoke test passed; `bun run --cwd packages/{server,opencode} typecheck` clean.
- Serving: `opencode web --port 4447 --hostname 0.0.0.0` on `testing/`, password from shell env (same as :4445).

## Follow-ups created / closed

- FU-018 (first modification) → **closed** — delivered as FE-001.
- FU-020: user verifies login page from iOS (shortcut/Add-to-Home-Screen) and iterates on UX/password.
