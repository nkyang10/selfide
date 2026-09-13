# Session 016 — Session-list subtitle: last user prompt in sidebar

- **Date:** 2026-09-12 (UTC)
- **Repo:** `50-projects/p003-opencode-fork/opencode` (vendored fork, never committed to ide repo)
- **Package:** `packages/app` only (client-side)
- **User goal:** In the workspace sidebar session list, show the **last prompt I sent** under each
  session title.

## What was built

New feature **FE-006** — "last prompt" preview line under the session title in the workspace
sidebar list.

### Behavior
- Each session row now shows a one-line subtitle under the title with the text of the **last user
  prompt** (the most recent non-synthetic, non-ignored text part of the newest user message).
- Whitespace is normalized (newlines → space, collapsed, trimmed) so the preview stays on one line.
- Subtitle is hidden for **dense** rows (the compact recent-sessions overlay in the project popover).
- The row **tooltip** now shows `title + "\n" + prompt` so the full preview remains readable even
  when truncated in a collapsed/mobile sidebar.
- Empty / not-yet-prefetched sessions show no subtitle (progressive enhancement — appears once the
  existing message prefetch has pulled the session data).

### Why client-only
The message store (`serverSync().session.data.message` + `.part`) already contains user message text
for listed sessions thanks to the existing prefetch path (`prefetchSession`). No server/DB/schema
change was required.

### Files (all under `packages/app/src/`)
- `utils/session-last-prompt.ts` (new) — `sessionLastPrompt(sync, sessionID)` extracts the last user
  prompt text.
- `pages/layout/sidebar-items.tsx` — `SessionItem` computes `lastPrompt` (memo) and passes it to
  `SessionRow`; `SessionRow` renders the subtitle line and enriches the tooltip value.
- `utils/session-last-prompt.test.ts` (new) — 7 unit tests.

### Verification
- `bun run typecheck` (packages/app) — pass
- `bun run test:unit` (packages/app) — 737 pass / 0 fail (7 new tests)
- Live redeploy + smoke **not** performed in this session (build/deploy deferred).

## Notes
- The preview reflects the last *text* user message only; synthetic/ignored parts (e.g. tool-triggered
  steers) are excluded, matching the existing convention in `components/dialog-fork.tsx`.
- Scope note: desktop **or** mobile sidebar are both covered since the row component is shared; only
  dense-overlay rows are skipped.

## Addendum — async bulk prefetch so EVERY listed session gets a subtitle
The first pass only showed subtitles for sessions the existing prefetch had already loaded (current +
hover neighbors, ≤10/folder). Per user request, a **bulk async pass** now fires when the session list
renders:
- `pages/layout.tsx` — new `createEffect` on `currentSessions()` enqueues **all visible sessions** at
  low priority via the existing per-directory prefetch queue, using a small per-session message limit
  (`previewLimit = 20`) and a wider per-dir cap (`PREFETCH_PREVIEW_MAX_SESSIONS_PER_DIR = 25`).
- Queue entries carry `{ id, limit, keep }`; `prefetchMessages`/`pumpPrefetch`/`markPrefetched` honor
  the per-item limit and the per-item cache-eviction keep-count (so the store no longer evicts the
  preview data of sessions beyond 10 per folder).
- Hover/nav upgrades are unchanged: a session fetched at 20 is re-fetched up to 200 on interaction
  (`shouldPrefetch(id, 200)` stays true), bumping to the front of the queue.
- `prefetchPendingLimit` raised 10 → 30 so long lists aren't pruned before the preview pass.
- Tradeoff (accepted): up to N small API calls (N = visible sessions, 2 concurrent, ≤25/folder, 20
  messages each).

## Addendum — DEPLOYED (user: "deploy", 2026-09-12 ~10:36 UTC)
- Build `./scripts/build-linux.sh` → **0.0.0-dev-202609120234** (bun 1.3.14). Old pid 3967592
  (`0.0.0-dev-202609111028`) killed; `./scripts/run-web.sh 4447` → new pid **219946**.
- Smoke: unauth `/` 401, `/login` 200, authed POST login 302 → root 200. Served SPA entry changed from
  `index-CAzbSeqL.js` (s015) → `index-BV48gH_b.js`; served bundle contains `lastPrompt` +
  `text-text-secondary` (FE-006 subtitle code live). Log clean.
- Note: the tree also carried s017's uncommitted titlebar/chat-header work — bundled in the
  same binary (FU-030 already covered both).

### Evidence
- Deploy log rows and current pid recorded in `20-logs/command-log.md`; FU-030 (build+deploy) now **closed**; FU-031 (home Sessions tab real prompt) left open for user decision.

## Addendum — FU-031 DONE: real last-prompt in the home Sessions tab (same session)
User confirmed wanting the actual prompt text on the starting home screen (not just the title proxy).
- `pages/home/home-sessions-table-controller.tsx` — per-record **preview prefetch**: concurrency-3 queue,
  `HOME_SESSION_PREVIEW_LIMIT = 20`, guarded by `useServerSync().session.shouldPrefetch`, calling
  `.session.prefetch(id, 20)`. Reuses the SAME message store as the sidebar (home renders under the
  focused server's `ServerSyncProvider`).
- `pages/home/home-sessions-table.tsx` — each row now renders a second line under the title with the
  real last user prompt: `sessionLastPrompt(useServerSync(), session.id)`. Marker
  `data-component="home-session-row-prompt"`.
- Verified: typecheck ✅, test:unit 737 ✅. Deployed as **0.0.0-dev-202609120259** (pid 248812); served
  entry `index-DhhfqPa8.js` contains `home-session-row-prompt` + `lastPrompt`. FU-029 closed too.

## Evidence
- Helper: `packages/app/src/utils/session-last-prompt.ts`
- Component wiring: `packages/app/src/pages/layout/sidebar-items.tsx`
- Tests: `packages/app/src/utils/session-last-prompt.test.ts`
- Bulk prefetch: `packages/app/src/pages/layout.tsx`
- Home table: `packages/app/src/pages/home/home-sessions-table.tsx` + `home-sessions-table-controller.tsx`
