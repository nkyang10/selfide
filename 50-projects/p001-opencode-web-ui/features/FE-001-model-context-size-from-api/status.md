# FE-001 — status

**State:** ✅ CODE COMPLETE · all gates green · committed `97363f7` (**not pushed**) · **deployed** `1.1.20260929181740` (pid 1393483, :4447)
**Decisions:** DEC-059 · **Session:** `20-logs/sessions/2026-09-30_s085_model-context-size-from-api.md`

## Shipped

| File | Change |
|---|---|
| `packages/core/src/model-context-size.ts` | new, 134 lines |
| `packages/core/src/config/plugin/provider.ts` | +32 |
| `packages/core/test/model-context-size.test.ts` | new, 18 tests |
| `packages/core/test/config/provider.test.ts` | +3 end-to-end tests |

4 files, +419/−0, `packages/core` only. No UI change, no i18n key, no route, no event, no config schema change.

## Verified

- `bun turbo typecheck` **30/30**
- `packages/core` **1109 pass / 16 fail**, against a true baseline of **1088 / the same 16** pre-existing
  failures → +21 tests, nothing broken
- **Live against the real gateways:** `dgx/general` (no limit) → **1048576**; a configured `500000` →
  **untouched**; `ocgo` → **0** (publishes nothing, correct); `rtx/general` → **262144**

## Known limitations (deliberate, see DEC-059)

- **`ocgo/opencode-go-default` still shows `0`.** Correct — its gateway publishes no context field.
  Auto-compaction stays off for that model until a number is set in the config by hand. → **FU-120**
- **`dgx/general` is configured `500000` but the server reports `1048576`.** Left as the user wrote it.
  → **FU-121**
- The fill is **in-memory**, so it is re-fetched after a server restart (the accepted cost of not writing
  `opencode.jsonc`).
- The deployed binary's fill path is proven by `strings` + an in-process run of the identical code, not by
  a filled value observed on :4447 — a project-level config is not consulted for a `/tmp` directory.

## Next

Commit is unpushed. The build shipped a parallel session's 3 uncommitted `packages/opencode` files
(FU-117 hazard, user approved).
