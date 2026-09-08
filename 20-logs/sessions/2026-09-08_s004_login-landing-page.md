# Session s004 — p003/FE-001: web login landing page (cookie auth, remember-me)

- **Date:** 2026-09-08 (UTC)
- **Goal (user spec):** replace the current web auth UX with a typical login **landing page**:
  - Input the same credentials opencode uses (Basic auth `OPENCODE_SERVER_PASSWORD`; username+password).
  - **Remember-me checkbox** → persist auth "forever" (long-lived cookie).
  - Session/cookie-based auth that **carries over in iOS "Add to Home Screen" web shortcuts**.
  - Global failure path: any auth failure → login page.
  - After successful login → **redirect back to the originally requested path**.
- **Status:** 🟡 IN PROGRESS
- **Bible:** fork source `50-projects/p003-opencode-fork/opencode/` (HEAD ecbc6cc).

## References

- Server auth gate: `opencode/packages/opencode/src/server/routes/instance/httpapi/middleware/authorization.ts`
- Upstream base: `packages/server/src/middleware/authorization.ts`
- Web frontend: `packages/web/src`
