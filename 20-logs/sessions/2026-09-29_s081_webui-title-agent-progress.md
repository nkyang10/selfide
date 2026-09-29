# s081 — FE-027: the web UI title counts finished agent tabs (`MarkCode [1 of 2]`)

- **Opened (UTC):** 2026-09-29 02:43
- **Status:** CLOSED 03:10 — **FE-027 code complete, every gate green, live-measured. COMMITTED `e76ffba` (03:15).
  NOT pushed / NOT built into the binary / NOT deployed.** The user is talking to me *through* :4447, so a deploy would kill this
  session — the commit/build/deploy step is theirs to call.
- **Fork:** `50-projects/p003-opencode-fork/opencode` (`dev`, clean at `a9029ff`)

## Request (verbatim)

> new feature. webui title show MarkCode [1 of 2]
> 1 = number of completed agent action
> 2 = total number
> keep update

Refined by the user before any code was written:

> i refine the count
> it is the number of opened project agent tab that finished / idle VS total number of opened project agent tab

**The refinement changes the feature.** The first reading was "agent actions" (tool calls). The
refined reading is **tabs**: numerator = open agent tabs that are finished/idle, denominator = every
open agent tab. So the title answers *"how many of the agents I have open are done?"* — which is the
question a phone user has when they switch back to the browser mid-work.

## Where the data comes from (traced before writing code)

| Need | Source |
|---|---|
| The open agent tabs | `useTabs().store` — `context/tabs.tsx`, the persisted titlebar tab list (`SessionTab` = `{type:"session", server, sessionId}`; `DraftTab` is a not-yet-created session) |
| Finished / not finished | `sync.session.data.session_working(sessionID)` — `context/server-session.ts:214`, the app's one definition of "this session is doing something" (`session_status[id].type !== "idle"`, so `busy` **and** `retry` both count as not finished) |
| The per-server session store | `useGlobal().ensureServerCtx(conn).sync` — `context/global.tsx:45`, which already creates a ctx for every connected server |
| Where a global effect can live | `SharedProviders` in `app.tsx:313`, beside `BodyDesignClass` (the existing `document.*` mutator), inside the router root → mounted for every route in **both** the web and desktop entry points (`entry.tsx:172`, `packages/desktop/src/renderer/index.tsx:407`) |

The title is currently static: `packages/app/index.html:9` → `<title>MarkCode</title>`. Nothing in
`packages/app` ever writes `document.title` (grep: zero hits), so there is no existing title state to
extend or conflict with.

## Decisions taken (to be recorded as DEC-056)

1. **Count session tabs only.** A `DraftTab` is not an agent yet (no session, cannot be busy), so it is
   left out of both numbers rather than inflating "finished". Flagged to the user as a one-line change.
2. **Plain `MarkCode` when no agent tab is open**; the counter appears as soon as one exists, including
   `[1 of 1]`. The all-done end state stays visible as `[2 of 2]` — the user asked for the count, not
   for a "done" banner that disappears.
3. **"Finished" = `!session_working(id)`**, i.e. idle. A tab blocked on a permission/question counts as
   finished (it is not the agent working); this is the same definition the sidebar dot uses
   (`pages/layout/sidebar-items.tsx:177`).
4. **The counter is localized, the product name is not.** `MarkCode` is a product name (kept in code,
   as `index.html` already has it); the `[{{done}} of {{total}}]` phrase is a new i18n key
   `app.title.tabs` in `packages/app/src/i18n/en.ts` + **all 63** non-English locales (English source
   copy byte-for-byte, the FU-026 pattern; `zh`/`zht` translated) or `i18n/parity.test.ts` fails.

## Gates

- [x] `bun typecheck` in `packages/app` — clean
- [x] `bun run test:unit` — **780 pass / 0 fail** (3129 assertions)
- [x] `bun test src/i18n/parity.test.ts` — **5 pass / 979 assertions** (unchanged count)
- [x] `oxlint` on the 2 changed code files — new file **0 warnings**; `app.tsx` 4 warnings, **identical with the
      change stashed** (pre-existing)
- [x] `bun run build` — bundle carries both the key and the compiled effect
- [x] **live check** (below)

**One correction I owe the record:** I first reported "9 pre-existing unit failures". They were **my own wrong
command** — I ran bare `bun test`, which resolves solid's *server* build and throws
`Export named 'use' not found in solid-js/web/dist/server.js` in 6 files. The package's own script is
`bun run test:unit` (`--conditions=solid --preload ./happydom.ts`), which is **780/0**. The A/B I did with
`git stash` "proved" the failures were pre-existing because they were identical in both trees — identical to a
wrong command in both trees. Recorded so nobody repeats it.

## What shipped — committed `e76ffba` (65 files, +194/−0, tree clean, not pushed)

| File | Change |
|---|---|
| `packages/app/src/components/document-title.tsx` | **new**, 42 lines — `DocumentTitle`, one `createRenderEffect` that reads the open session tabs and their `session_working`, SSR-guarded like `BodyDesignClass` |
| `packages/app/src/app.tsx` | +2 — import and mount in `SharedProviders` beside `BodyDesignClass` |
| `packages/app/src/i18n/en.ts` | +1 key `app.title.tabs` = `"[{{done}} of {{total}}]"` |
| `packages/app/src/i18n/*.ts` (61) | the same key; English copy verbatim, `zh`/`zht` = `[已完成 {{done}} / 共 {{total}}]` |

63 modified + 1 new, +168/−0. No other package touched, no store, no migration, no new dependency.

## Live measurement (nothing on the box restarted or redeployed)

Playwright served the freshly built `packages/app/dist` to a browser and intercepted **only the document and
`/assets`**; the login POST, every API call and the SSE stream went to the real :4447. So the code under test is
the new one and the statuses under test are real.

```
03:07:57  home, no agent tab          MarkCode
03:08:00  opened a busy session tab   MarkCode [0 of 1]     <- that session is the one running this probe
03:08:03  new (draft) tab opened      MarkCode [0 of 1]     <- draft excluded from both numbers
03:08:04  0.26 s after Enter          MarkCode [0 of 2]     <- promoted to a session tab, both busy
03:08:05  turn finished               MarkCode [1 of 2]
```

Same probe in the zht locale rendered `MarkCode [已完成 0 / 共 1]`. **0 page errors.**

Three probe sessions were created in the user's project and one directory under `/tmp`; see FU-107 — deleting
them is the user's call, not mine.

## Evidence

- command-log rows `2026-09-29 02:43` → `03:09`
- `40-knowledge/decisions-log.md` → **DEC-056**
- fork `AGENTS.md` → "The window title counts agent tabs"

