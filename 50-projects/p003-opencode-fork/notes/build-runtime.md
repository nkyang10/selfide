# p003 — Build & runtime notes (s003)

## Toolchain

- Bun installed 2026-09-08 to `~/.bun/bin/bun` (v1.4.2) via official installer. Not in repo.
- Host is **aarch64** (`uname -m` = aarch64), so single-target build produces `opencode-linux-arm64`.

## Build (validated)

- `bun install` → 2346 packages, ~24s.
- `bun ./packages/opencode/script/build.ts --single` → `packages/opencode/dist/opencode-linux-arm64/bin/opencode`
  (176 MB ELF aarch64, not stripped). Smoke test: `0.0.0-dev-202609072334`.

## Running

- Command (run from `testing/`, binds **0.0.0.0** for LAN access, no auth for LAN)::<br>
  `env -u OPENCODE_SERVER_PASSWORD setsid nohup <bin> web --port 4447 --hostname 0.0.0.0 > web-4447.log 2>&1 < /dev/null &`
- URL: http://127.0.0.1:4447/ locally; from other devices on the LAN: http://192.168.1.249:4447/
  (`hostname -I`: 192.168.100.11, 192.168.101.11, 192.168.1.249, 172.17.0.1). GET / returns 200.
- **Security:** unauthenticated on 0.0.0.0 — only expose on the trusted LAN; use
  `OPENCODE_SERVER_PASSWORD` + Basic auth if broader exposure is needed.

## Gotchas / environment facts

1. **Shell env leak:** the login shell exports `OPENCODE_SERVER_PASSWORD=hahahaha` (+ `OPENCODE_PID`,
   `OPENCODE=1`) from the older `~/.opencode` install. Any server we start inherits it → HTTP Basic 401
   challenge (`realm="Secure Area"`, see `opencode/packages/opencode/src/server/auth.ts`). Mitigation:
   `env -u OPENCODE_SERVER_PASSWORD` when launching our own instance.
2. **Pre-existing process:** `~/.opencode/bin/opencode web --hostname 0.0.0.0 --port 4445` is still running
   (older install, pid observed 36797). Ours runs on 127.0.0.1:4447. Don't kill the user's 4445 instance.
3. **Config:** global `~/.config/opencode/opencode.jsonc` defines the DGX providers (llm main + ocgo) used
   for model access; no password/policies there.
4. **State:** `~/.local/share/opencode/` holds `auth.json` (provider cred for opencode-go), `opencode.db`,
   snapshots. Not replicated into this repo.
