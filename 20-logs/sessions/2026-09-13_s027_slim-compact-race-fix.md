# s027 — FE-011 slim fix: compact summary race + progress toast

**Date:** 2026-09-13 (UTC)
**Scope:** `packages/app` (client-only). Fixes the deployed slim icon button (FE-011, s023).

## Problem (reported on-device)
The slim icon (compact + start a new session seeded with the summary) works for compaction and opening a
new tab, but **the compact result never reaches the new tab**. Also there was **no progress notification**
while the (sometimes multi-second) compaction runs.

## Root cause
In `slimSession` (message-timeline.tsx), after `await session.compact` + `await session.wait`, the code
reads the compaction summary synchronously from the client reactive store:

```ts
const messages = sync().data.message[id] ?? []
const summaryMessage = [...messages].reverse().find((m) => m.role === "assistant" && m.summary)
```

`session.wait` resolves when the server has committed the summary message, but the client's `sync().data`
store is populated **asynchronously** by the SSE event stream. Reading it synchronously right after
`await wait()` races the SSE delivery, so `summaryMessage` is usually `undefined`, `report` becomes `""`,
and the `if (report)` block is skipped → nothing submitted to the new tab.

## Fix
1. **Race:** wrap the summary read in a bounded poll loop (up to 40 × 150ms ≈ 6s) that re-reads
   `sync().data.message[id]` (and re-extracts parts) until an assistant `summary` message with non-empty
   content is found. The still-empty `report` is tolerated (session still created, just not seeded).
2. **Progress:** on click, show a persistent **loading** toast (`variant:"loading"`, `icon:"reset"`,
   `session.slim.progress.*`) that stays up across the compaction; dismiss it and show a **success**
   toast (`session.slim.success.*`) when done (or dismiss + error toast on failure). Button stays
   disabled via `slimming()`.

## Files changed
- `packages/app/src/i18n/en.ts` + 61 locales: added `session.slim.progress.title/description`,
  `session.slim.success.title/description`.
- `packages/app/src/pages/session/timeline/message-timeline.tsx`: `import { dismissToast }`; slimSession
  rewritten as above.

## Verification
- `tsgo -b` typecheck: clean.
- i18n parity test: 5 pass (all 61 locales + en).
- lint: 0 new errors (1 unrelated pre-existing in an e2e file).
- Built `scripts/build-linux.sh` (bun 1.3.14) → `0.0.0-dev-202609130611`, smoke OK.
- Deployed: kill 1009078 → relaunch `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447`
  (pid 1040890). unauth `/`=401, `/login`=200. New `session.slim.progress` keys present in dist bundles.

## Note (timestamp drift)
Recent command-log rows (s025/s026) are in local CST; per POLICY I logged s027 rows in UTC and
flagged this discrepancy for reconciliation.

## On-device test needed (FU-037)
(1) long session → click slim → loading toast appears; (2) new `<title> (N)` session opens, focused,
with the summary as its first message that actually replies; (3) source session untouched; (4)
loading toast clears and success toast shows.
