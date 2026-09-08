# p003 — opencode fork: local clone, modifications, own Linux build

**Project:** Vendor the **opencode** source (`github.com/anomalyco/opencode`, MIT), modify it, and build our own
Linux binary instead of relying on prebuilt releases.
**Status:** 🟢 MODIFIED + SELF-BUILT + SERVING (s004) — first modification **FE-001 live**: cookie-auth
**login landing page**. Web UI on http://192.168.1.249:4447/ (cwd `testing/`).
**Source:** `opencode/` — vendored clone (git-ignored as a nested repo; never commit it to the ide repo).

## Mission

A sandbox where we can patch opencode itself. Upstream build toolchain is **Bun 1.3+** (never assume it's
installed — bootstrapping the toolchain is part of this project).

## Deliverables map

- `config/` — build/env templates, configs for the fork
- `notes/` — design notes for planned modifications
- `scripts/` — build/bootstrap scripts (source-of-truth)
- `sessions/` — per-modification working notes

## FE-001 — Login landing page + persistent cookie auth (DONE, s004)

Replaces the raw Basic-auth prompt with a real login page served by the server:

- **Landing page** at `/login` (auto-shown when an unauthenticated browser hits **any** path — the 401
  "global failure path" renders the page, not the browser's Basic dialog).
- **Credentials** = the same server credentials (`OPENCODE_SERVER_USERNAME`/`OPENCODE_SERVER_PASSWORD`).
  Prompts only when a password is configured; no password → server stays open (unchanged).
- **Save auth forever** checkbox → long-lived cookie `oc_creds` (base64 `user:pass`, `Max-Age=1y`,
  `HttpOnly`, `SameSite=Lax`). Unchecked → session cookie. **Cookie carries into iOS *Add to Home Screen***
  shortcuts (WKWebView keeps cookies for the origin).
- **Redirect-back**: the requested path is preserved (`next`), and after a successful login the browser
  returns to it (open-redirect sanitized).
- **Log out** at `/logout` clears the cookie.
- Cookie → Basic header bridging on **both** gates: the web/UI router middleware *and* the JSON API layer.
- Files touched (in `opencode/`): `packages/opencode/src/server/shared/login.ts` (new), the auth middleware
  `packages/opencode/src/server/routes/instance/httpapi/middleware/authorization.ts`, routes
  `packages/opencode/src/server/routes/instance/httpapi/server.ts`, shared
  `packages/server/src/middleware/authorization.ts`.
- Designs + verification: `20-logs/sessions/2026-09-08_s004_login-landing-page.md`, DEC-011.

## Build recipe (VALIDATED — host is aarch64)

```bash
cd opencode && export PATH="$HOME/.bun/bin:$PATH"
bun install                         # OK — 2346 packages
bun ./packages/opencode/script/build.ts --single   # OK — smoke test passes
# binary: packages/opencode/dist/opencode-linux-arm64/bin/opencode
```

## Running the local build (web)

```bash
cd testing
# With OPENCODE_SERVER_PASSWORD set (recommended) -> login landing page active.
OPENCODE_SERVER_PASSWORD=<pw> setsid nohup ../opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode web --port 4447 --hostname 0.0.0.0 > web-4447.log 2>&1 < /dev/null &
# or: ../scripts/run-web.sh   (keeps whatever OPENCODE_SERVER_PASSWORD is in env)
```

- **URL:** host http://0.0.0.0:4447/, LAN http://192.168.1.249:4447/ (`hostname -I`).
- **Running instance (s004):** pid rec in `20-logs/command-log.md`, password = the one already exported in
  the login shell (`hahahaha`? verify), i.e. **the same credentials as the old :4445 instance**.
- **Security note:** `oc_creds` is the base64-encoded credential (readable if stolen, effective only when
  copied — http LAN). Same trust model as the Basic auth it replaces. Do not expose LAN ports to the internet.

## Vendored clone state

- Cloned: 2026-09-08 (s003) from `https://github.com/anomalyco/opencode.git`
- HEAD at clone: `ecbc6ccac85b3e8087b6445e584318419b9e2b34` (branch `dev`, shallow, 2026-09-08)
- **Forked (s003):** `nkyang10/opencode` (fork of anomalyco/opencode, public). Remotes on the vendored clone:
  - `origin`  → https://github.com/nkyang10/opencode.git (our fork — push here)
  - `upstream` → https://github.com/anomalyco/opencode.git (original — pull latest from here)
- Note: shallow clone (`--depth 1`); consider `git fetch --unshallow` before first push/PR.

## References

- Decisions: DEC-010 (fork project), DEC-011 (FE-001 login/cookie design), 2026-09-08
- Follow-ups: FU-018 (first modification) ✅ done via FE-001; FU-020 (user verify on iOS + iterate)
- Runtime notes: `notes/build-runtime.md`
