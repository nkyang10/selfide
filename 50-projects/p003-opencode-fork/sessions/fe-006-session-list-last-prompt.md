# FE-006 — Session-list subtitle: last prompt in the sidebar (s016)

2026-09-12 — implemented, typechecked, unit-tested. **Not yet deployed.**

## Goal
In the workspace sidebar session list, show the **last user prompt** under each session title.

## Approach
Client-only. The existing prefetch path already loads per-session messages into
`serverSync().session.data.message` + `.part`. So:

- New util `packages/app/src/utils/session-last-prompt.ts`:
  - Iterate the session's messages newest-first.
  - Take the newest **user** message that has a non-`synthetic`/non-`ignored` **text** part.
  - Return that text with whitespace normalized (multi-space/newline → single space, trimmed), so the
    subtitle stays on one line.
- `pages/layout/sidebar-items.tsx`:
  - `SessionItem` builds an `lastPrompt` memo and forwards it to `SessionRow`.
  - `SessionRow` renders a `text-13-regular text-text-secondary` subtitle under the title when
    present **and** not `dense`.
  - Tooltip enriched to `title\nprompt` so the full preview is readable when truncated.

## Why not server-side
The `Session` object has no stored prompt text; storing one means touching schema + DB + Server HttpApi.
The message store already carries the text for listed sessions, so the frontend approach is zero-risk
and additive. Tradeoff: subtitle appears only once the session has been prefetched (brief blank state
for cold sessions).

## Addendum (same session) — bulk async prefetch for all listed rows
User followed up wanting every displayed session to load its prompt via async fetches on render.

- `pages/layout.tsx`: new `createEffect` on `currentSessions()` enqueues **all visible sessions** at
  low priority through the existing per-directory prefetch queue, `previewLimit = 20` messages each,
  per-dir cap 25 (was 10) via `maxPerDir` option.
- Queue `pending` entries are now `{ id, limit, keep }`; `prefetchMessages`, `pumpPrefetch` and
  `markPrefetched(directory, id, keep)` honor the per-item fetch limit and the eviction keep-count so
  the session-cache no longer drops preview data for sessions beyond 10/folder.
- Hover/nav upgrades unchanged: `shouldPrefetch(id, 200)` stays true after a 20-message fetch, so
  interaction re-fetches up to 200 and bumps to the queue front.
- `prefetchPendingLimit` 10 → 30 so the bulk pass isn't pruned on long lists.
- Tradeoff: N small API calls on open (2 concurrent, ≤25/folder, 20 msgs each) — accepted.

## Verification
- `bun run typecheck` (packages/app): pass
- `bun run test:unit` (packages/app): 737 pass / 0 fail
- Deploy: deferred (next build `./scripts/build-linux.sh` + restart on :4447)

## Follow-ups
- [ ] Build + deploy, smoke-test subtitle in browser.
- [ ] Consider also showing the prompt in `sidebar-project.tsx` dense rows (currently hidden by design).

## Addendum 2 (same session) — home Sessions tab shows the real last prompt (FU-031)
User's starting screen (projects/session picker) has no sidebar; the s015 home **Sessions** table used
`session.title` (LLM-generated) as a proxy. Now each row shows the real last user prompt under the title:
- `home-sessions-table-controller.tsx`: per-record preview prefetch — concurrency-3 queue, limit 20,
  `shouldPrefetch`-guarded, reuses the shared message store (`useServerSync().session.prefetch`).
- `home-sessions-table.tsx`: subtitle line via `sessionLastPrompt(useServerSync(), session.id)`.
Deployed 0.0.0-dev-202609120259 (pid 248812). FU-029/FU-031 closed.
