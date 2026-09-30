# FE-001 — Fill a model's missing context size from the provider API, once

> Project p001 (the opencode web UI) implemented inside the vendored fork p003, per the fork's rule
> that UI/UX work lives in the fork's own packages. Status: **CODE COMPLETE**, gates green, live-verified.

## The request

> "when the model selected has no context size specified, try to use the api to get the context size
> to fill in once"

## The defect it fixes (measured, not assumed)

`ocgo/opencode-go-default` is declared in `~/.config/opencode/opencode.jsonc` with **no `limit` block**.
`Model.Info.empty` (`packages/schema/src/model.ts:103`) defaults to `limit: { context: 0, output: 0 }`,
and `ConfigProviderPlugin` only overwrites it when a `limit` is present
(`packages/core/src/config/plugin/provider.ts:105` — `if (config.limit !== undefined)`).

Proved live against the running server (pid 1331373, build `1.1.20260929172032`):

```
GET /provider      →  ocgo/opencode-go-default limit={"context":0,"output":0}
GET /api/model     →  ocgo/opencode-go-default limit={"context":0,"output":0}
```

`context: 0` is not cosmetic. Two things break:

1. **Auto-compaction silently never runs.** `SessionCompaction.compactAfterOverflow` and
   `compactIfNeeded` both open with `if (context === undefined || context <= 0) return false`
   (`packages/core/src/session/compaction.ts:180` and `:235`). A session on such a model grows
   until the provider rejects the request, with no compaction and no warning.
2. **The context meter renders blank.** `getSessionContext` computes
   `usage: limit ? Math.round((total / limit) * 100) : null` — `0` is falsy, so `usage` is `null`
   and the progress ring has no denominator (`session-context-metrics.ts:59`).

## What the API can and cannot answer (probed, 2026-09-30)

| provider | endpoint | result |
|---|---|---|
| `dgx` → `:8102/v1` | `GET /v1/models` | 4 models, each with **`max_model_len: 1048576`** (vLLM) |
| `ocgo` → `:8101/v1` | `GET /v1/models` | 25 models, keys `id,object,created,owned_by` — **no context field at all** |
| `rtx` → `:8104/v1` | `GET /v1/models` | **`{"error":"proxy_error"}`** on 3/3 attempts at planning time |

So the API is a real source for self-hosted gateways (the exact case that needs it) and a dead end
for a hosted proxy that simply does not publish the number. **The feature must be able to answer
"no" and must never guess.** A wrong context size is worse than none: it sets the compaction
trigger, so a fabricated 128k would truncate a 1M session.

`rtx` being down is not incidental — it is the reason the fetch needs a hard timeout and a
negative cache.

## Decisions (user's answers, 2026-09-30)

1. **Source** — the provider's own `/models` endpoint. Not the models.dev catalog: `opencode-go-default`
   is a local alias and is absent from the catalog, so the catalog cannot answer the case that
   motivated this.
2. **Destination** — **in-memory only, per server session.** No `opencode.jsonc` write. This avoids
   the config-write hazards already documented for this fork (a global config write disposes every
   instance; a write here would also be a surprising side effect of merely starting a server).
3. **Stale values** — **not** handled. A value the user typed is treated as a deliberate choice and
   is never overwritten. Only missing/zero is filled.

### Consequence of (2) and (3), stated plainly

The fill is per server process. It disappears on restart and is re-fetched then. That is the
accepted trade for not writing config, and it is why the fetch is cached rather than repeated.

## Side finding, deliberately NOT acted on

`dgx/general` is configured `context: 500000`, but the vLLM server reports `max_model_len: 1048576`.
By decision (3) this is left alone and is **not** corrected. It is recorded here because it is a
real inaccuracy in the live config, and the user may want to fix it by hand.

## Design

**New module** `packages/core/src/model-context-size.ts`:

- `contextSize(entry)` — **pure**, exported, and the only thing unit-tested directly. Reads the
  first positive finite number among the field names real providers use for a context window
  (`max_model_len`, `context_length`, `context_window`, `max_context_length`, `max_input_tokens`).
- `modelsPayload(json)` — pure; pulls the model array out of `data` / `models` / a bare array. An
  error object such as `rtx`'s `{"error":"proxy_error"}` yields `[]`, i.e. "no answer".
- `fill(input)` — the once-only cached fetch: `GET <baseURL>/models` with the provider's own
  credentials, bounded by a 5s timeout, memoized **process-globally per base URL**.

**The cache is process-global, not per instance, and that is load-bearing.** The catalog transform
runs once per open *location* (directory) and again on every `State.reload()` (config change,
models.dev refresh). A per-instance cache would re-hit the network for every open tab. Keying on
the base URL gives exactly **one** request per provider per server process, and lets the *negative*
result be remembered too — a provider that publishes no context size is never asked again. That is
what makes "fill in once" literally true.

**Hook** — `packages/core/src/config/plugin/provider.ts`, immediately after the existing
`if (config.limit !== undefined)` line, so the "never overwrite what the user configured" rule is
visible in the same place the limit is applied rather than in a separate plugin that could be
ordered wrongly against it.

`State.ts:8-10` states transforms may perform Effects, and `packages/opencode/src/provider/provider.ts:1658-1668`
already does a real awaited network call inside a state build, so an async transform is the
established pattern here, not a new mechanism.

**Credentials** come from the same provider record the request will be sent to: an existing
`Authorization` / `x-api-key` header in `provider.request.headers` wins, otherwise
`Bearer` the `api.settings.apiKey`. Never logged.

**Failure is visible.** Both outcomes are logged once per provider: a fill, and a refusal with the
reason. A `context: 0` that stays `0` is otherwise indistinguishable from a bug — the FU-101 class
this repo keeps filing.

## Files

| File | Change |
|---|---|
| `packages/core/src/model-context-size.ts` | new — extractor + once-only cached fetch |
| `packages/core/src/config/plugin/provider.ts` | fill a zero `limit.context` after the config limit is applied |
| `packages/core/test/model-context-size.test.ts` | new — pure extractor + payload + fill-rule tests |

No UI change, no i18n key, no new route, no new event, no config schema change.
