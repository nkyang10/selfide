# s085 — Fill a model's missing context size from its provider API, once (FE-001 / DEC-059)

**Date:** 2026-09-30 (UTC) · **Fork commits:** `97363f7` + `bf346e6` — **both now on `origin/dev`, pushed by a parallel session rather than by me** (see the addendum) · **Deployed:** `1.1.20261001041357`, pid 2555733 on :4447

## The request

> "opencode webui project. when the model selected has no context size specified, try to use the api to get
> the context size to fill in once"

## What the request actually was

Not a cosmetic gap. A config model declared without a `limit` keeps `Model.Info.empty`'s default
`limit: { context: 0, output: 0 }` (`schema/src/model.ts:103`), and `ConfigProviderPlugin` only writes a
limit when the config has one (`config/plugin/provider.ts:105`). Confirmed live on both routes:

```
GET /provider   →  ocgo/opencode-go-default limit={"context":0,"output":0}
GET /api/model  →  ocgo/opencode-go-default limit={"context":0,"output":0}
```

`0` breaks two things, neither of which explains itself:

1. **Auto-compaction never runs.** `compaction.ts:180` and `:235` both open with
   `if (context === undefined || context <= 0) return false`. A session on that model grows until the
   provider rejects it — silently, with no compaction and no warning.
2. **The context meter is blank.** `session-context-metrics.ts:59` is `usage: limit ? … : null`, and `0`
   is falsy, so the progress ring has no denominator.

## The API can only sometimes answer — measured, not assumed

| provider | `GET /v1/models` | result |
|---|---|---|
| `dgx` :8102 (vLLM) | 4 models, `max_model_len: 1048576` | **answers** |
| `ocgo` :8101 | 25 models, keys `id,object,created,owned_by` | **no context field at all** |
| `rtx` :8104 | `{"error":"proxy_error"}` 3/3 | **down** at planning time |

So the honest feature is *"ask once, use only what the provider reports, and be able to answer 'no'"*.
A fabricated number would be **worse** than none: that number is the compaction trigger, so a guessed
128k would truncate a session that holds 1M.

## Decisions (asked, not assumed)

1. **Provider's own `/models`** — the models.dev catalog cannot answer `opencode-go-default`, which is a
   local alias absent from it, so it could not serve the case that prompted the request.
2. **In-memory only, per server session** — no `opencode.jsonc` write, whose write path disposes every
   open instance. Accepted cost: re-fetched after a restart.
3. **Missing/zero only** — a value the user wrote is a deliberate choice and is never overwritten.

Full reasoning in **DEC-059**.

## What shipped

| File | Change |
|---|---|
| `packages/core/src/model-context-size.ts` | new, 134 lines — pure `contextSize` / `modelsPayload` / `contextSizes` / `resolve`, plus a once-per-provider-per-process `GET <baseURL>/models` with the provider's own credentials, 5s timeout, **failure cached as a refusal** |
| `packages/core/src/config/plugin/provider.ts` | +32 — fills a zero `limit.context` immediately after the configured limit is applied, so "never overwrite" is visible in the same three lines that apply it |
| `packages/core/test/model-context-size.test.ts` | new, 18 tests |
| `packages/core/test/config/provider.test.ts` | +3 end-to-end tests through the real plugin against a real `Bun.serve` gateway |

No UI change, no i18n key, no route, no event, no config schema change.

## The load-bearing design points

- **The cache is process-global, keyed on the base URL, and caches the refusal too.** The catalog
  transform runs once per open *directory* and again on every `State.reload()` (config change, models.dev
  refresh — hourly), so a per-instance cache would re-hit the network per tab. Caching "no" is what makes
  a provider that publishes nothing stop being asked, instead of taxing every reload forever.
- **A provider with no in-band credential is skipped, not called unauthenticated.** The catalog draft
  cannot see env-var or integration credentials, so asking anyway is a pointless request per catalog build.
  Found by *reading* the existing test, which would otherwise have made real network calls.
- **Only the catalog can fix both symptoms**, because the meter reads it and compaction reads the same
  resolved model. One write fixes the meter and compaction together.

## Two real bugs the tests caught

1. **The first cache stored the `Effect`, not its result** — so it re-issued the request on *every* call,
   the exact opposite of "once". Only visible because the test counts requests against a real server; a
   mock would have agreed with it by construction.
2. **`Effect.cached` does not memoize in effect `4.0.0-beta.83`**, despite `packages/opencode/AGENTS.md`
   and the migration spec advertising it for deduplication. Probed three ways: separate runtimes (re-runs),
   one shared root (re-runs), hoisted inner effect (**memoizes**, 1 run for 3 uses). The trap is that
   `Effect.cached(e)` returns `Effect<Effect<A>>` and re-running the **outer** effect silently rebuilds an
   empty cache, so the obvious `Effect.flatMap(cached, …)` loses every result. Worked around with an
   explicit result map; filed as **FU-119**.

## Gates

- `bun turbo typecheck` — **30/30**
- `packages/core` full suite — **1109 pass / 16 fail**
- **True baseline** — 1088 pass / **the same 16 fail** (15 `cross-spawn spawner`, 1 `ProjectCopy`), all
  pre-existing and unrelated. +21 passing tests, nothing broken.
  *The first baseline attempt was invalid*: `git stash push -- <path>` silently failed on my two untracked
  new files, so the "baseline" still contained my code. Caught because the test count matched rather than
  dropping by 21; redone by moving the files aside and `git checkout`-ing the tracked pair.
- oxlint — 0 errors on the changed files

## Live verification

The decisive run — the real `ConfigProviderPlugin` against the real LAN gateways:

| case | result |
|---|---|
| `dgx/general`, no `limit` | → **1048576** (from `max_model_len`) |
| `dgxstale/general`, `limit: 500000` | → **500000**, untouched |
| `ocgo/opencode-go-default` | → **0** (publishes nothing — correct) |
| `rtx/general`, no `limit` | → **262144** (recovered from the outage) |

Whole catalog build: **896 ms** for 4 providers including 2 LAN round trips.

On the deployed build the same rules hold (`ocgo` still `0`, `dgx` 500000 and `rtx` 262144 untouched), and
`strings` confirms the code shipped.

**One honest limitation.** I could not get a project-level `opencode.json` consulted: `Config` walks
`fs.up(start: location.directory, stop: location.project.directory)`, and a `/tmp` directory resolved to the
existing `ide` project even after `git init`. Forcing it would have meant editing the user's global config,
which disposes every instance and needs a restart. So the deployed binary's fill path is proven by
`strings` + the in-process run of the identical code, **not** by a filled value observed on :4447. The
probe directory was deleted and the user's config was never touched.

## Follow-ups filed

- **FU-119** — `Effect.cached` does not memoize in this effect build; the AGENTS.md/spec guidance is wrong.
- **FU-120** — `ocgo` still has no context size, correctly. Needs a decision: set it in the config by hand,
  or get the gateway to publish it. Auto-compaction stays off for that model until then.
- **FU-121** — `dgx/general` is configured `500000` but its server reports `1048576`. Left alone by
  decision 3; a one-line manual config fix.

## Notes for the next session

- Both commits are **on `origin/dev`** — I did not push them; a parallel session committed on top of mine
  and pushed. `bf346e6` verified as an ancestor of `origin/dev`.
- The build compiled the whole checkout, so the **parallel session's 3 uncommitted
  `packages/opencode` files shipped in this binary** (FU-117 hazard, user approved it explicitly).
- `packages/opencode/config.json` is still an untracked FU-112 artifact from a `test:httpapi` run.

---

# Addendum — the reader corrected me, and the fix that followed (DEC-060)

**The reader's challenge:** *"ocgo by api 應該有返 context size?"* — **they were right and I was wrong.**

What I had written in this record: "the honest outcome is that the mechanism correctly answers *I don't know*."
That sentence was true about the **route I had tested** and false as a conclusion. I verified `/v1/models`
(7 endpoint variants, 25 entries, keys union exactly `id,object,created,owned_by`) and reported **"it does not
exist."** That is the exact error class this repo keeps filing: a single negative observation stated as an
absolute.

**What I had missed:** `opencode-go-default` is an **alias**, not a model. A real completion names what served it:

```
x-opencode-upstream-model-id: space-bunny
x-zen-model:                 space-bunny-free
X-Model-Profile:             oc-go
```

and `space-bunny-free` **is in the catalog** at `context: 1048576`. Stable across three consecutive requests.
`x-zen-model` is set by **OpenCode's own Zen service** (`console/.../zen/util/handler.ts:255`) and already
forwarded by its inference proxy (`lib/inference-proxy.ts:75`) — first-party, not one gateway's invention.

**The reader's second instruction:** *"not hardcode context size in opencode.jsonc for opgo"* — consistent with
their original in-memory choice, so the fix had to be dynamic. Then: **automatic probe**, and **keep 0 + warn on
failure**.

## What shipped — `bf346e6`, deployed `1.1.20261001041357` (pid 2555733)

`catalogLimits` + `resolveAlias` in `model-context-size.ts`; the config plugin now reads the catalog once and,
when a size is *still* 0, asks what the model serves and looks that name up. 4 files, +354/−38.

**The load-bearing property: only an alias costs a request.** Every id the catalog knows already arrives with a
limit from the models-dev plugin, so a model still at 0 is by definition an alias — the cheap test bounds the
expensive one. Live: `dgx` and `rtx` took **no** completion; only `ocgo` did.

**Five discovery endpoints were tried and all 404'd** (`/v1/profiles`, `/v1/model-profiles`, `/profiles`,
`/zen/go/models`, `/v1/endpoints`), so a request is genuinely required — the honest design keeps it to one
`max_tokens: 1` call per alias per process, and caches the **name** so reloads reuse it.

## Live, on the deployed build

```
ocgo/opencode-go-default  limit={"context":1048576,"output":0}   ← was 0
dgx/general               limit={"context":500000,"output":32000}  ← configured, untouched
rtx/general               limit={"context":262144,"output":32000}  ← untouched
```

**And the reader's config was not edited** — `ocgo.opencode-go-default` still carries **no `limit` block**, read
back after the deploy, so the number cannot have come from there.

- Gates: `turbo typecheck` **30/30** · core **1121 pass / 16 fail** (baseline 1088 / the same 16) → **+33 tests**
- Full catalog build with the alias probe and the 5 MB catalog fetch: **2156 ms**, once per process
- oxlint **0 errors**; my file went 8 warnings → 1 by replacing three `unknown → Record` assertions with one
  guarded `record()` helper

## The reusable lesson

I stated a negative conclusion from one positive observation and only corrected it because the user pushed back.
Probing `/v1/models` seven ways would **not** have found it — only *asking the model* did. The guard is to ask
"what other route could answer this?" before writing "no".

## Process defect found and filed (FU-134)

`open-followups.md` contains **two rows numbered FU-120** (s084's narration item and this feature's), because
parallel sessions mint ids without seeing each other. My index-based edit of "FU-120" then ran from the **s084**
row through this session's FU-121 and deleted **s084's follow-up plus my own FU-121**. Caught by
`git diff --stat` reporting 4 deletions where 1 was intended; restored with `git checkout --`, then redone
matching on session id as well as number. **Never edit a shared append-only tracker by number alone.**
