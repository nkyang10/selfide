# s058 — Home Sessions list AJAX cursor pagination (FE-016)

**Date:** 2026-09-19 (UTC) **UTC timestamp:** 2026-09-19 12:40
**Trigger:** user asked to improve the home/starting work-sessions list; chose pagination, then asked
to make it **AJAX load-more** (save refresh time) and apply the same to the Sessions-tab list. Also
requested a code-debt review of all modified/uncommitted code at feature end.
**Result:** ✅ implemented + typechecked + unit-tested + app-builds + **deployed :4447 + committed + pushed**.

## Final state (session close-out)
- **Deployed** :4447 — server PID 1724164, v1.18.31-fork.1-dev (via `deploy-web-4447.sh --detach`).
- **Page-1 limit = 15** (both lists; `HOME_SESSION_PAGE_LIMIT`/`HOME_SESSION_TABLE_PAGE_LIMIT=15`, retain cap stays 64) — user requested after first deploy.
- **Committed + pushed** FE-016: `2b6c3a2` `feat(app): Home Sessions AJAX cursor pagination — Load more on both lists, search scan deferred` → `92678c1..2b6c3a2 dev->dev` (10 files: 8 modified + 2 new).
- **Committed + pushed** s056 terminal rebrand (FU-061): `f2fe4cd` `chore(ui): rebrand CLI/TUI terminal art opencode → MarkCode` → `2b6c3a2..f2fe4cd dev->dev`.
- Follow-ups FU-061 ✅, FU-062 ✅ (verified), FU-064 ✅.

## Scope (confirmed via questions)
1. Load more **by AJAX** (server cursor pages) instead of in-memory slice → big refresh-time saving.
2. Do the same in the **Sessions-tab table** list (`HomeSessionsTable`).
3. Keep search **eager full-scan**, but **defer it until search is focused** (so refresh that never
   touches search does not scan). [user chose: Search deferred]
4. Live session events → **re-fetch page 1** (cheap, keep top fresh) rather than merging cursor pages.
   [user chose: re-fetch page 1]

## What changed (fork `opencode` nested repo, branch `dev`)
- `context/global-sync/home-session-index.ts` — added `fetchHomeSessionPage(list, pageLimit, cursor?)`
  → one server page `{sessions, nextCursor, hasMore}` (uses `parseHomeSessionIndex`; no full scan). The
  old eager full-scan `loadHomeSessionIndex` remains but is now used **only by search**.
- **NEW** `pages/home/home-sessions-paged.ts` — `createPagedHomeSessions()` shared hook: page-1 backed by
  a tanstack query (refetch on mount/reconnect/stale), subsequent pages appended via `loadMore()` cursor
  fetch; `mergeSessionPages` dedupes by id + sorts newest-first; SSE event bump triggers a page-1 reload.
- `home-sessions-controller.tsx` (Projects tab list) — replaced eager `sessionLoad`/`indexedSessions`
  with the paged hook; `records`/`groups` from paged sessions; exposed `pagination.{canLoadMore,
  loadingMore, onLoadMore}`; dropped `loadHomeSessionIndex`, dead `data.loading`, `data.searchRecords`.
- `home-sessions-table-controller.tsx` (Sessions tab) — same paged-swap; dropped `data.loading` (dead).
- `home-session-search-controller.ts` — now owns its **own lazy eager index** (`loadHomeSessionIndex`),
  enabled only when `state.focused`; keeps search over the full retained index; `result.loading` gated on
  focused; no longer reads `sessions.data.searchRecords`/`sessions.data.loading`.
- `home.sessions.tsx`, `home-sessions-view.tsx`, `home-sessions-table.tsx`, `home.tsx` — wired
  `canLoadMore`/`loadingMore`/`onLoadMore`; **Load more** ghost button (`common.loadMore`) with
  `variant="loading"` spinner while fetching, click guarded; added to both lists.

## Code-debt review (user-requested, done at end)
- Removed: dead `data.loading` from both list controllers (nothing consumed it — views gate on Suspense /
  avatar loading); dead `paged.loading` + `reloadFirstPage` from the hook's public surface; the in-memory
  slice constants `HOME_PAGE_SIZE`/`HOME_PAGE_INCREMENT`; a forced-abstraction helper I added then reverted.
- Kept intentionally: `projectDirectories`/`projectByID` memos duplicated in list + search controllers
  (small, stable; extracting adds coupling/risk for little gain); `ctx!` in the `list` closures (guarded
  by tanstack `enabled`).
- Net: 9 fork files changed, ~173 insertions / 83 deletions.

## Verification
- `bun run typecheck` (tsgo -b): ✅ (bun 1.3.14 pinned).
- `bun test --conditions=solid --preload ./happydom.ts ./src/pages/home`: ✅ 6 pass / 0 fail
  (incl. new `home-sessions-paged.test.ts` for `fetchHomeSessionPage` + `mergeSessionPages`).
- `bun run build` (vite, app pkg): ✅ built in ~10s.

## Deploy
- Spawn host = `:4447` (pid 658386). Use `./deploy-web-4447.sh --detach`; deploy log
  `testing/deploy-4447.log`.

## Follow-ups
- FU-062 verify deploy after reconnect; FU-064 commit+push (9 files + new paged module + test).

