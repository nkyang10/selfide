# s023 — Visual model fallback for image messages (p003 opencode fork)

**Date:** 2026-09-12 | **Controller:** opencode

## Objective
Confirm image/media upload works in the p003 opencode fork, and add a configurable
`visual_model` fallback (opencode.jsonc) so image-bearing turns route to a vision-capable
model when the active session model (e.g. Hermes) lacks image input support.

## Outcome (verified)
- Image upload is functional code-level (43 related tests pass — attachments, build-request-parts,
  utils) and now also verified **end-to-end over the running fork HTTP API** (file part with
  `mime: image/png, url: data:image/...` → accepted, persisted, model turn generated).
- **`visual_model` implemented end-to-end and verified on the live served fork (:4447):**
  - Image message + `dgx/general` (non-vision: `capabilities.input.image=false`) →
    assistant turn used **`dgx-vision/vision-model-default`**.
  - Text-only follow-up → stayed on **`dgx/general`** (no substitution).
  - Session's stored default model untouched (per-turn substitution only).
- Runtime config: `visual_model: "dgx-vision/vision-model-default"` lives in the **global**
  config `~/.config/opencode/opencode.jsonc` (providers `dgx`, `ocgo`, `dgx-vision` already
  present from earlier session; `/config` on the fork returns the key → server picks it up).

## Change set (fork source, only the feature — `git diff` is exactly these 5 files)
| File | Change |
|---|---|
| `packages/core/src/v1/config/config.ts` | `visual_model` optional string key after `small_model` |
| `packages/opencode/src/provider/provider.ts` | `getVisualModel` on `Interface` + impl (`cfg.visual_model` → `parseModel` → `getModel`, `undefined` if `=== cfg.model`, swallow `ProviderModelNotFoundError`) + wired into `Service.of` |
| `packages/opencode/src/session/prompt.ts` | routing at the per-turn `getModel(...)` interception (~L1141): if `capabilities.input.image === false` and the last user message's parts contain a `file` part with `mime`/`url` `image/` / `data:image/`, substitute `provider.getVisualModel()`; assistant `msg.modelID/providerID` and `processor.create({model})` then use the visual model |
| `packages/opencode/test/fake/provider.ts` | fake `getVisualModel` (`Effect.succeed(undefined)`) |
| — | `config/migrate.ts` deliberately **NOT** touched (see below) |

Typecheck clean: `packages/core` + `packages/opencode` (tsgo --noEmit).

## Key decisions / facts
- **Why `migrate.ts` untouched:** its `keys` set feeds `isV1()` (legacy-config detection). Adding
  `visual_model` there would misdetect modern V2 configs and DROP the key during `migrate()`
  (field-by-field rebuild). `visual_model` never existed in legacy V1 files → no migration need.
- **Fallback design is per-turn at `session/prompt.ts:1141`** (approved design: global key,
  fallback-only). It checks ONLY the last user message's parts (not earlier turns' history).
- **Hermes has no vision** (confirmed in `models-api.json` fixture: `attachment:false`,
  `modalities.input:["text"]` for `hermes-4-70b` etc.).
- **Runtime image parts** arrive server-side as `{type:"file", mime, url:"data:image/..."}` —
  matches `packages/app/src/components/prompt-input/build-request-parts.ts`.

## Blocker found + fixed during verification (pre-existing, NOT the visual_model feature)
Every HTTP prompt on the **bun-1.4.2 build crashed** with
`TypeError: undefined is not an object (evaluating 'a.name')` at `Agent.state` init →
`createUserMessage` (`err_*` in `~/.local/share/opencode/log/opencode.log`). Root cause:
this fork's killer **bun 1.4.x compiler bug** (embedded effect/schema graph), already documented
in `scripts/build-linux.sh` (pin bun **1.3.14**; see note `build-runtime.md` / earlier sessions).
Diagnosis path:
1. Source-run (`bun run src/index.ts run …`) works; built binary fails → build artifact not source.
2. A diagnostic build with `minify:false, splitting:false` worked; then `minify:true, splitting:false`
   worked → the crash tracks bun-1.4.x + `splitting:true` bundle graph.
3. Decisive fix: reverted the `splitting` experiment in `script/build.ts` and rebuilt with the
   **pinned bun 1.3.14** via `scripts/build-linux.sh` → working binary `0.0.0-dev-202609121134`
   (184 MB). Re-verified image routing on it → production served instance restored.
- `script/build.ts` is **back to HEAD** (no remaining diff); the fix is "build with bun 1.3.14".

## Environment verified facts
- Pinned bun 1.3.14 download cache: `~/.cache/opencode-build/bun-1.3.14/…` (per build-linux.sh).
- Served fork auth for :4447: `opencode` / `hahahaha` (Basic) — the process env carries
  `OPENCODE_SERVER_PASSWORD=hahahaha`, username `opencode` in this install.
- Test image payload + verification session records kept in `/tmp` only (no secrets to repo).

## Protocol
- Command log appended for s023 commands.
- `current-state.md` updated (s023 addendum).
- `decisions-log.md` DEC-021.
- `open-followups.md` FU-038 (+ FU-039).
- Fork-side note: this session record lives in the ide project logs (p003 work tracked here).
