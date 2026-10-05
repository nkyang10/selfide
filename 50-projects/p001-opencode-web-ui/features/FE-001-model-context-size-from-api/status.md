# FE-001 — status

**State:** ✅ CODE COMPLETE · gates green · **2 commits** (`97363f7` provider `/models`, `bf346e6` alias
resolution) — **both on `origin/dev`**, pushed by a parallel session rather than by me · **deployed**
`1.1.20261001041357` (pid 2555733, :4447)
**Decisions:** DEC-059 (fill from `/models`) · DEC-060 (resolve an alias from what it serves)
**Session:** `20-logs/sessions/2026-09-30_s085_model-context-size-from-api.md` (+ addendum)

## Shipped

| File | Change |
|---|---|
| `packages/core/src/model-context-size.ts` | new — pure extractors, once-per-process caches, alias resolution |
| `packages/core/src/config/plugin/provider.ts` | fills a zero `limit.context` |
| `packages/core/test/model-context-size.test.ts` | new — extractor, cache and alias tests |
| `packages/core/test/config/provider.test.ts` | end-to-end through the real plugin against real gateways |

## Verified live

| case | result |
|---|---|
| `dgx/general`, no `limit` | **1048576** from vLLM `max_model_len` |
| configured `limit: 500000` | **untouched** (and no request made) |
| `ocgo/opencode-go-default` (alias) | **1048576** — resolved via `x-zen-model: space-bunny-free` |
| `rtx/general`, no `limit` | **262144** |

- `bun turbo typecheck` **30/30**
- `packages/core` **1121 pass / 16 fail** against a true baseline of **1088 / the same 16** → **+33 tests**
- oxlint **0 errors**
- Full catalog build incl. the alias probe and the 5 MB catalog fetch: **2156 ms**, once per server process

## Known limitations (deliberate)

- **`dgx/general` is configured `500000` but its server reports `1048576`.** Left as the user wrote it, per
  "missing/zero only". → **FU-121**
- The fill is **in-memory**: re-fetched after a server restart (the accepted cost of not writing
  `opencode.jsonc`).
- Only an **alias** costs a request — bounded to one `max_tokens:1` per alias per process.
- **An alias named `default` can move.** The mapping was stable across 3 requests, and re-resolving each start
  is *better* than a frozen number, but a stale value is only possible for the life of one server process.

## Next

Both commits are **on `origin/dev`** (I did not push; a parallel session did). The second deploy shipped a
clean tree, so unlike the first one it carried no uncommitted parallel work.

