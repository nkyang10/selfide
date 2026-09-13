# p003 — visual_model fallback for image messages (s023, 2026-09-12)

Feature implemented + deployed in the fork and verified end-to-end on the live :4447 instance.

## What
New top-level config key `visual_model` (`provider/model`, mirrors `small_model`). Each turn, if the
active model's `capabilities.input.image === false` and the last user message has an `image/*` /
`data:image/` file part, that turn routes to the visual model.

## Source changes (only these 5 files, per `git diff`)
- `packages/core/src/v1/config/config.ts` — `visual_model` key
- `packages/opencode/src/provider/provider.ts` — `Interface.getVisualModel` + impl (config → parse →
  `getModel`, no-op on missing model, no-op if `=== cfg.model`) + `Service.of` wiring
- `packages/opencode/src/session/prompt.ts` ~L1141 — per-turn substitution at the `getModel` site;
  assistant `providerID/modelID` + `processor.create({model})` follow it; session default model untouched
- `packages/opencode/test/fake/provider.ts` — fake `getVisualModel`
- `config/v1/config/migrate.ts` deliberately NOT changed (would drop the key via legacy migration)

Typecheck clean (core + opencode), 43 related upload tests pass.

## Verified (runtime, via `POST /session/:id/message` with a `{type:"file", mime:"image/png",
url:"data:image/..."}` part)
| Prompt | model used for assistant turn |
|---|---|
| image + `dgx/general` (non-vision) | **`dgx-vision/vision-model-default`** |
| text-only follow-up | `dgx/general` |

Session's stored default model (`dgx/general`) never mutated.

## Runtime config
`visual_model: "dgx-vision/vision-model-default"` in global `~/.config/opencode/opencode.jsonc`
(providers `dgx`, `ocgo`, `dgx-vision` defined there). The fork server exposes it via `/config`.

## Caveats
- The `dgx-vision` endpoint (:8103) currently replies "I can't view images" — the DGX gateway's
  vision model is not actually image-capable yet. Routing works; backend vision pending (see ide
  project FU-038).
- Docs for this fork work live in the ide project (`50-projects/p003-opencode-fork` work is tracked
  in `/home/mark/Desktop/ide` 20-logs + 40-knowledge; session record
  `2026-09-12_s023_visual-model-fallback.md`).
