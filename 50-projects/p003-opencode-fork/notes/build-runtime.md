# p003 — Build & runtime notes (s003, addendum s023)

## Toolchain

- Bun installed 2026-09-08 to `~/.bun/bin/bun` (v1.4.2) via official installer. Not in repo.
- Host is **aarch64** (`uname -m` = aarch64), so single-target build produces `opencode-linux-arm64`.

## Build (validated)

- `bun install` → 2346 packages, ~24s.
- `bun ./packages/opencode/script/build.ts --single` → `packages/opencode/dist/opencode-linux-arm64/bin/opencode`
  (176 MB ELF aarch64, not stripped). Smoke test: `0.0.0-dev-202609072334`.
- **s023 CORRECTION (2026-09-12):** the above "validated" line predates the discovery that **bun 1.4.x
  must not be used to build** this fork — its compiler embeds a broken effect/schema graph that crashes
  v2 endpoints AND every prompt (`TypeError: undefined is not an object (evaluating 'a.name')` at
  `Agent.state` → `createUserMessage`). Build with the **pinned bun 1.3.14**: `scripts/build-linux.sh`
  → working `0.0.0-dev-202609121134` (184 MB). Do not change `script/build.ts`'s `splitting:true`
  (disabling it only dodges the 1.4.x symptom; the canonical fix is the pinned toolchain).

## Running

- Command (run from `testing/`, binds **0.0.0.0** for LAN access)::<br>
  `setsid nohup env OPENCODE_SERVER_PASSWORD=hahahaha <bin> web --port 4447 --hostname 0.0.0.0 > web-4447.log 2>&1 < /dev/null &`
- Session auth for this install: Basic `opencode` / `hahahaha`.
- URL: http://127.0.0.1:4447/ locally; from other devices on the LAN: http://192.168.1.249:4447/
  (`hostname -I`: 192.168.100.11, 192.168.101.11, 192.168.1.249, 172.17.0.1). GET / returns 200.

## Gotchas / environment facts

1. **Shell env leak:** the login shell exports `OPENCODE_SERVER_PASSWORD=hahahaha` (+ `OPENCODE_PID`,
   `OPENCODE=1`) from the older `~/.opencode` install. If you launch WITH that env, HTTP Basic 401
   challenge applies (`realm="Secure Area"`); s023 launch keeps it intentionally (LAN-auth wanted) —
   otherwise `env -u OPENCODE_SERVER_PASSWORD` for open LAN access.
2. **Pre-existing process:** `~/.opencode/bin/opencode web --hostname 0.0.0.0 --port 4445` is still running
   (older install). Don't kill the user's 4445 instance.
3. **Config:** global `~/.config/opencode/opencode.jsonc` defines the DGX providers (`dgx`, `ocgo`,
   `dgx-vision`) + **`visual_model: "dgx-vision/vision-model-default"`** (image-fallback routing, s023).
4. **State:** `~/.local/share/opencode/` holds `auth.json` (provider cred for opencode-go), `opencode.db`,
   snapshots. Not replicated into this repo.
5. **s023 feature:** `visual_model` per-turn image fallback — see `sessions/2026-09-12-visual-model-fallback.md`.

