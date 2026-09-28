# s079 — "OpenCode 1.18.0 or newer is required to use the free tier": the fork's own version string was the problem

- **Date:** 2026-09-28 (UTC) · **Session:** s079
- **Request:** *"Error from provider (Console): OpenCode 1.18.0 or newer is required to use the free tier —
  it is the version upstream"*
- **Outcome:** **✅ ROOT CAUSE FOUND AND FIXED — the wire `User-Agent` now carries the upstream base
  (`opencode/1.18.31`) instead of the fork's `1.1.<deploy-ts>`. Measured A/B against the real Zen gate:
  the old binary gets HTTP 426 with the user's exact message, the new binary gets `FREE-OK` from the same
  free model, cost 0. Deployed :4447 as `1.1.20260928065214` (pid 233322).**
- **User's decision:** *"Only fix the wire User-Agent"* — chosen over restoring the upstream base in the
  displayed number (DEC-042's grammar stays) and over a one-off `OPENCODE_VERSION=1.18.31` test build.
- **Change:** 6 files, +28/−2, **uncommitted** (not asked).

## What the error actually is

Not a fork bug in the UI and not a subscription problem: it is OpenCode's hosted Zen backend refusing the
client. The wrapper text is added by the console's own code — `packages/console/app/src/routes/zen/util/handler.ts:337`
prefixes a relayed provider error with `Error from provider (<displayName>)`, and the provider it names is
`Console`. Upstream has the identical report open three times: `anomalyco/opencode#49944` (1.18.30 user),
`#50451` and `#50581` (HTTP **426** `provider.invalid-request`, "1.18.31 works, `0.0.0-beta-*` does not").
So this is a known upstream gate, and what decides it is the version string the client puts on the wire.

**The fork sends its own version on every provider request** —
`packages/opencode/src/session/llm/request.ts:18`: `const USER_AGENT = \`opencode/${InstallationVersion}\``.

**And that version is DEC-042's.** The live :4447 binary reported `1.1.20260928023322` (verified), because
`49a9f0c` (DEC-042) replaced DEC-037's upstream-mirroring `1.18.31-fork.1-dev` with `1.<counter>.<deploy-ts>`.
`1.1.x` is **older than `1.18.0`** under any numeric comparison, so the free tier rejects the client. The user's
own remark was the missing half: `1.18.0` is *upstream's* numbering, and the fork had stopped mirroring it.
First deployed 2026-09-27 (`1.1.20260927123522`) — which is when this would have started.

## Measured, not inferred

My first instinct was to build a mock of the gate. The mock was bypassed — the catalog is baked into the binary
(`OPENCODE_MODELS_DEV`), so `OPENCODE_MODELS_URL` is ignored and the request went to the **real** service. That
accident produced the proof, because the real gate answered with the user's own error:

```
old binary 1.1.20260928061739, UA opencode/1.1.20260928061739
  → 426  {"type":"UpgradeRequired","message":"Error from provider (Console): OpenCode 1.18.0 or newer is
          required to use the free tier"}   metadata.url https://opencode.ai/zen/v1/chat/completions
new binary 1.1.20260928065214, UA opencode/1.18.31
  → 200  text "FREE-OK"  model opencode/mimo-v2.6-flash-free  cost 0  tokens 7693
```

Same account, same model, same day, minutes apart; the only variable is the declared version.

Probes that came *before* the fix, and what they ruled out (all against the real service, `max_tokens: 1`):

- `/zen/go/v1` with the `opencode-go` key, every UA tried → `403 "An active OpenCode Go subscription is required
  to use Go models"`. **Go models need the $10/mo subscription; the version fix does not grant that.**
- `/zen/v1` with a hand-rolled curl → `403 FreeTierError "OpenCode's free tier can only be used from within
  OpenCode"` (upstream #49433) — the anonymous `public` key and a Go key are both refused; the real client is
  not, which is why only the client run reached the 426.

## The change (Option B, the user's call)

Keep DEC-042's displayed version; give the wire a version OpenCode can place.

| File | Change |
|---|---|
| `packages/script/src/index.ts` | `UPSTREAM_VERSION = "1.18.31"` + `Script.upstream` getter (`OPENCODE_UPSTREAM_VERSION` env overrides) |
| `packages/opencode/script/build.ts`, `build-node.ts`, `packages/cli/script/build.ts` | new `OPENCODE_UPSTREAM_VERSION` define — all three build paths, so none silently falls back |
| `packages/core/src/installation/version.ts` | `UpstreamVersion` global + export; falls back to `InstallationVersion` when unstamped (source runs) |
| `packages/opencode/src/session/llm/request.ts:18` | `USER_AGENT = \`opencode/${UpstreamVersion}\`` |

The one-line env escape hatch works without touching a script: `build-linux.sh` only *overrides*
`OPENCODE_VERSION`/`OPENCODE_CHANNEL`, so `OPENCODE_UPSTREAM_VERSION=… scripts/deploy-web-4447.sh --detach`
reaches the build through the inherited environment.

**Deliberately not changed:** `packages/core/src/models-dev.ts:23` sends
`opencode/<channel>/<version>/<client>` to `models.opencode.ai`. Different service, no gate in evidence, and
that UA is the only place the fork build stays visible to OpenCode. If a gate ever appears there, this is the
next place to look.

**Why not the grammar (Option A, my recommendation, declined):** `1.<upstream minor>.<deploy-ts>` would have
fixed it with one notion of "version". It is a supersession of DEC-042 across three package.jsons, the desktop
`app.getVersion()` and the updater, and Option B was chosen instead — so the cost now is a second constant that
a human must bump on every upstream merge (**FU-104**).

## Gates

`bun turbo typecheck` **30/30** (exit 0) · `bun typecheck` clean in `packages/opencode`, `packages/core`,
`packages/cli` · oxlint **0 errors** on all 6 files (3 pre-existing warnings in the build scripts) ·
deploy smoke test `1.1.20260928065214` · :4447 back up on **pid 233322**, `/api/health` 401 unauth
(expected, login gating) · rollback binary kept at `/tmp/opencode/rollback/opencode-1.1.20260928061739`.

## Left for the user

The last mile is the web UI: pick a free model (`opencode/mimo-v2.6-flash-free` is what I used) and send one
prompt. The engine path is the same binary and the same `request.ts`, so the CLI A/B above is the strong
signal, but the UI is where the error was seen.
