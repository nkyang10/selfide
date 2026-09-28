# s078 — Home Sessions list: previous session vanishes, replaced by an untitled "New session" row

- **Date:** 2026-09-28 (UTC) · **Session:** s078
- **Request:** *"http://192.168.1.249:4447/server/…/session/ses_f1e1105d8ffemIqA1fu6wNrXE7all previous session in
  session list become New session with not correct last user prompt"*
- **Outcome:** **✅ FIXED — committed `86c621c`, pushed to `origin/dev`, deployed :4447 as
  `1.1.20260928011449` (pid 58516) and verified in the live web UI.**
- **Target:** the fork's **server** (`packages/core` + `packages/server`), not the list component.
- **User's decision:** *"Server fix + index on (time_updated, id)"* — chosen over the app-only workaround
  and over a bare sort-column swap.

## Symptom, reproduced live

Probe (`/tmp/opencode/probe/home-list2.mjs`, 390×844, real login) — Home ▸ Sessions, first 12 rows:

```
[0] Fix New session last user prompt | 6 秒前 | … | http://192.168.1.249:4447/… previous session in session list become New session …
[1] New session | 7 小時前 | … | (no prompt line)
[2] New session | 7 小時前 | … | (no prompt line)
[3] New session | 8 小時前 | … | reply with the single word: ok
…
```

The session the user was in, `ses_f1e1105d8ffemIqA1fu6wNrXE7` ("Show agent progress after user prompt",
still being updated this minute), is **not in the list at all**. The row that took its place is
`ses_f1c355dfaffexVfLya0LS5XKkw`, a genuinely empty session whose title really is
`New session - 2026-09-27T16:55:02.928Z` → rendered "New session" by `sessionTitle()`
(`packages/app/src/utils/session-title.ts:1,18`). It has **0 messages**, hence no last-prompt line.
So "became New session with a wrong last user prompt" is one symptom: the row shows *a different session*.

Also missing for the same reason: `ses_f1e1283deffelepkjG1WgANi1y` ("Set opencode default port to 4447").

## Root cause (proven at the SQL level)

The list is fed by `client.v2.session.list` → `GET /api/session?limit=15&order=desc`
(`packages/app/src/pages/home/home-sessions-table-controller.tsx:34`, page limit 15 at `:16`; the grouped
Projects-tab list is identical at `home-sessions-controller.tsx:59`).

`V2Session.list` sorts by **creation** time:

- `packages/core/src/session.ts:271` — `const sortColumn = SessionTable.time_created`
- `packages/core/src/session.ts:295-298` — `orderBy(desc/asc(sortColumn), desc/asc(SessionTable.id))`

and the keyset cursor anchors on `time.created` too:

- `packages/server/src/handlers/session.ts:50,58` — `DateTime.toEpochMillis(first.time.created)` / `last.time.created`

Direct SQL on the live DB (`~/.local/share/opencode/opencode-mark-dev.db`, 109 sessions):

| order | rows 1-3 |
|---|---|
| `ORDER BY time_updated DESC` (what the UI shows) | `ses_f1a98e374…`(now) · **`ses_f1e1105d8ffe…`** · `ses_f1c20dcd1ffe…` |
| `ORDER BY time_created DESC` (what the API returns) | `ses_f1a98e374…` · `ses_f1c20dcd1ffe…` · `ses_f1c355dfaff…` |

`LIMIT 15` therefore cuts off both `ses_f1e1105d8ffemIqA1fu6wNrXE7` (created 17 h ago, updated now) and
`ses_f1e1283deffelepkjG1WgANi1y` — exactly the two absent rows. The client re-sorts its page correctly
(`home-sessions-paged.ts:13-19` `mergeSessionPages`, `home-sessions-table.tsx:30-36`), so the **ordering is
right and the page membership is wrong**.

Corroboration that updated-time is the intended contract:

- v1 sibling route `GET /session` is documented *"sorted by most recently updated"* and does order by updated.
- `packages/app/src/context/global-sync/child-store.ts:334-336` — *"Once released, use client.v2.project.list
  and root-filtered, **updated-time v2.session.list**"*.
- `home-session-index.ts:172-176` — *"the current V2 API orders by creation time … A bounded page could omit an
  old session updated today."* **That comment predicted exactly this bug; FE-016 (s058) then shipped the bounded
  page anyway.**
- `packages/app/src/context/directory-sync.ts:160` fetches `order: "desc"` and slices the result, so the
  per-directory session fetch is wrong the same way.

## Ruled out

- **Last-prompt util** is fine: `sessionLastPrompt` (`utils/session-last-prompt.ts`) walks the stored messages
  backwards, and `fetchMessages` (`context/server-session.ts:549`) requests `order: "desc"` then reverses, so the
  window is the *newest* N — the last user message is always inside it.
- **Nothing wrong server-side with the session**: `GET /session/ses_f1e1105d8ffemIqA1fu6wNrXE7/message` returns
  its 17 user messages, last = "the bak file keep them. for other task please go on. …".
- The pasted URL ends `…NrXE7all`; the real id is `…NrXE7` (`GET /session/ses_f1e1105d8ffemIqA1fu6wNrXE7all`
  → `Session not found`). The extra `all` looks like a paste artefact, not a bug.

## Plan proposed (then executed)

1. `packages/core/src/session.ts:271` — sort column `time_created` → **`time_updated`**.
2. `packages/server/src/handlers/session.ts:50,58` — cursor anchor `time.created` → **`time.updated`** (must move
   with the sort column or paging breaks).
3. Tests: a `packages/core/test/` case for `V2Session.list` proving an old-but-just-updated session outranks a
   newly created one, plus cursor paging over the new column.
4. Gates: `bun turbo typecheck`, core tests, app unit, then build + redeploy :4447 and re-run the probe to prove
   the previous session is back at row 1 with its real title and last prompt.

Perf was neutral for the bare swap: `EXPLAIN QUERY PLAN` for the old query is `SCAN session` +
`USE TEMP B-TREE FOR ORDER BY` — there is **no** index on `time_created` or `time_updated`, so swapping the column
cost the same. The user asked for the index as well, so it is a speed-up on top, not a trade.

## What shipped (`86c621c`, 9 files, +245/−5)

| File | Change |
|---|---|
| `packages/core/src/session.ts` | `sortColumn` → `time_updated`, with a 5-line comment on why |
| `packages/server/src/handlers/session.ts` | `cursor.previous`/`cursor.next` built from `first/last.time.updated` |
| `packages/core/src/session/sql.ts` | `index("session_time_updated_id_idx").on(time_updated, id)` |
| `packages/core/src/database/migration/20260928004444_useful_manta.ts` | **new** — one `CREATE INDEX`, no rewrite |
| `packages/core/schema.json`, `schema.gen.ts`, `migration.gen.ts` | generated; snapshot prettier-formatted to keep the diff at +20/−2 |
| `packages/core/test/session-list.test.ts` | **new** — 5 cases |
| `packages/opencode/test/server/httpapi-session.test.ts` | 1 route-level case + a `setSessionTimes` helper |

### Tests, and proof they are not vacuous

My first draft of the fixture was **vacuous**: it stamped `time_created` and `time_updated` to the *same* value
everywhere, so created-order and updated-order gave identical results and all 5 cases passed against the old sort
column. Fixed by adding a `used(id, timeUpdated)` helper that moves only `time_updated`, so the two orders genuinely
disagree. Re-checked by `sed`-ing the sort column back to `time_created`:

- core `session-list.test.ts`: **3 of 5 fail** on the old column, 5/5 pass on the new one.
- `httpapi-session.test.ts` route case: **fails** on the old column, passes on the new one.

The route case also asserts the **decoded** cursor, so the anchor and the sort column cannot drift apart again —
that is the one coupling in this change that no type system covers, since the two files do not reference each other.

### Gates (all re-run, not assumed)

| Gate | Result |
|---|---|
| `bun turbo typecheck` | **30/30** |
| `bun test` (core) | 1088 pass / **16 fail** — baseline stashed = 1083 / **16**, so +5 (mine) and no new failure. The 16 are `cross-spawn spawner` (13) and `ProjectCopy > dirty git worktree` (1) etc., all environmental. |
| `bun test test/server` (opencode) | 298 pass / **2 fail** — baseline stashed = 297 / **2**. Same 2 (`HttpApi Server.listen` response logs, project directories/copies). |
| `bun run test:unit` (app) | **780 / 0** |
| `bunx oxlint` (5 touched files) | 0 errors, 6 warnings — all on pre-existing lines |
| `bunx prettier --check` (5 touched files) | clean (the route test needed one reformat) |
| `bun run migration --check` (core) | *"No schema changes, nothing to migrate"* |

### Deploy

- **DB backed up first:** `~/.local/share/opencode/opencode-mark-dev.db` → `/tmp/opencode/db-backup-before-s078.db`
  (896 MB, 109 sessions), because this migration touches live data. It is a `CREATE INDEX` and nothing else.
- `./scripts/deploy-web-4447.sh --detach` (detached: step 1 kills the :4447 listener, which is the process serving
  this session — the first attempt interrupted the tool call, and that interruption **is** the expected behaviour).
- Build **`1.1.20260928011449`**, server **pid 58516**, `/api/health` → `{"healthy":true,…}`.
- Migration applied: `session_time_updated_id_idx` present; `EXPLAIN QUERY PLAN` now
  `SCAN session USING INDEX session_time_updated_id_idx` (was `SCAN session` + temp B-tree).
- **Live proof.** `GET /api/session?limit=15&order=desc` — the exact request the Sessions tab makes — now returns
  `ses_f1e1105d8ffemIqA1fu6wNrXE7` ("Show agent progress after user prompt") as row 2; before the fix it was not
  in the response at all. Re-running the browser probe on the **real UI** (390×844, real login), the rows are now:

  ```
  [0] Fix New session last user prompt   | 3 秒前   | … | done?
  [1] Show agent progress after user prompt | 46 分鐘前 | … | fix all
  ...
  [9] Set opencode default port to 4447  | 15 小時前 | … | continue
  ```

  Both previously-absent sessions are back, with their real titles **and** their real last-user-prompt lines.
  Row count went 12 → 13 because the two recovered sessions pushed two subagent children off page 1.

### Provenance / hygiene

- The tree held **2 modified files not mine** (`packages/app/src/utils/turn-progress.ts` + its test) when I
  started; the parallel session committed them as `6aee40b` mid-task, so at build time the tree held nothing but
  my 9 files. Verified: `git status` is empty and the build input is exactly `origin/dev`.
- Staged and committed **only** the 9 paths above. Pushed with the pre-push gate live (`bun turbo typecheck`
  30/30), not bypassed.

## Known wart left alone (offered as a follow-up)

`parseHomeSessionIndex` (`home-session-index.ts:177-182`) drops child and archived sessions **after** the page is
fetched, so a 15-row page renders as 12–13 rows (subagent children eat page slots). The fix makes the *right*
sessions appear, but the list still under-fills a page. Fixing it needs server-side root/archived filtering —
which is exactly what the two `TODO(v2)` comments say the v2 API is not ready for.

