# Plan — FE-028 a Commentary panel that narrates the agent's work live

> **Status:** PLAN ONLY — no feature code written. Prepared 2026-09-29 (UTC), session **s082**.
> **User request (verbatim):** *"plan a new big enhencement / prepare a new commentary panel next to review
> panel control similar to 'Toggle review' button. so the new review panel will be showing commentary desc
> current agent work / the commentary will talk message by message. each message would not be too long. it is
> around 30 words. each message is added with interval 10s and is subject to llm to decide whether it is nice
> to add or wait next time. the message is a digest from the agent chat windows context (word + tools call)
> from the last commentary cursored context. the message will also consider the previous 100 message to make
> it a continuouity talk. the message is generated as a separated llm call using the same model that opencode
> using."*
> **User's three decisions** (asked before planning):
> 1. **Placement** = a **third column beside the Review panel** (desktop), toggled by a new header button next
>    to the "Toggle review" one.
> 2. **Driver** = a **server-side 10 s loop, gated on "some client currently has the panel open"** (a lease).
> 3. **Model** = the **session's own model** as the default, with a config key to switch to the provider's
>    small model.
> **Feature id:** FE-028 (FE-027 was taken by s081). Decision record: **DEC-057**. Follow-ups: **FU-110** (build) + **FU-111** (mobile variant).

---

## 0. Executive summary

Everything the feature needs already exists in the fork, three times over. There is an existing **sidecar
LLM call with no tools** (twice: the title generator and the compaction summariser), an existing **event
definition** pattern for a standalone session event, an existing **third-column precedent** in the same panel
(the file tree is already a sibling column with its own `ResizeHandle`), and an existing **lease-free
per-instance store** to hang a watcher count on. What is genuinely new is: one service, one table, one
migration, one event, one route group, one column, one button, one command.

| What we need | Reality in the fork |
|---|---|
| A separate LLM call, same model as the turn, no tools, read the result | ✅ `SessionPrompt.ensureTitle` (`packages/opencode/src/session/prompt.ts:193-253`) does *exactly this* — resolves the model, calls `llm.stream`, filters `textDelta`, `Stream.mkString`, persists. `SessionCompaction` (`packages/core/src/session/compaction.ts:176-231`) is the v2 twin. |
| A hidden internal agent to carry the prompt | ✅ `title` and `summary` already exist, `hidden: true`, `native: true`, `"*": "deny"` permissions (`packages/opencode/src/agent/agent.ts:233-258`), with prompt files in `packages/opencode/src/agent/prompt/`. |
| "Let the LLM decide whether to speak" | ⚠️ Nothing exists. Needs a tiny output contract (§3.3) and a lenient parser. This is the only genuinely novel mechanic. |
| The agent's words + tool calls as a digest | ✅ `session.messages()` + a v1 part walk. `SessionCompaction.serialize` (`compaction.ts:95-121`) is the model to follow, but it lives in core/v2 over v2 messages and is not reusable here — so a v1 serializer is written (≈35 lines). |
| A "last commentary" cursor | ✅ **Derived, not stored** — the newest commentary row carries the `anchor` message id it describes, and the next digest is everything strictly after it (§3.2). This avoids a cursor table *and* avoids the trap in §9.4. |
| 10-second cadence | ⚠️ Nothing loops on a timer today. The session loop is event-driven (`SessionPrompt` forks per turn). A small process-global fiber with a `Schedule` is new, and is the main risk (§9.1). |
| "Only while somebody is watching" | ⚠️ New. An in-memory lease map keyed by session id (§4). Sessions are process-local by rule ("Keep local Session drains process-local"), so this is free. |
| Persist the entries | ✅ `drizzle` + `bun run migration` in `packages/core` (`packages/core/script/migration.ts`) generates the migration + `schema.gen.ts` from a snapshot. One new table, one command. |
| Push entries to the browser | ✅ A standalone event module precedent: `packages/schema/src/session-status-event.ts` (`Event.define({ type: "session.status", … })`), consumed by the app's `switch` in `context/global-sync/event-reducer.ts:126` — which has **no throwing default**, so an old client safely ignores a new event type. |
| A third column beside Review | ✅ The side panel is already a flex row of sibling columns: the review column (`session-side-panel.tsx:318-757`) and the file-tree column (`:759-861`), the latter with its own `ResizeHandle` (`:845-859`). The commentary column is the same shape. |
| A toggle button + command | ✅ The review button is `session-header.tsx:465-478`; the command is `use-session-commands.tsx:562-566`; the palette allowlist is `command-palette.ts:43`. Copy all three. |
| Persisted open/closed | ✅ `store.review.panelOpened` (`context/layout.tsx:695-703`, accessor `:905-917`) under the `layout.v6` Persist key (`:271`). **Absent = closed**, so a new key needs no migrate branch and no version bump (the DEC-052 precedent). |

**Shape of the work: 1 service + 1 table + 1 event + 3 routes + 11 app files + 65 locale files.**
Roughly +900/−40. No new runtime dependency.

---

## 1. Decisions that shape everything else

| # | Decision | Why | Rejected alternative |
|---|---|---|---|
| D1 | The 10 s loop lives on the **server**, in the instance, keyed by session id | Only the server knows the model the turn is really using, and only the server can keep one shared narration for the phone and the desktop. A client loop would give two devices two different stories. | Client-driven polling (rejected by the user; also per-browser and lost on reload) |
| D2 | The loop runs **only while a client holds a lease** on the session | The user's decision, and it is the only version that is both free when unwatched and consistent across devices. | Always-on while busy (burns tokens on sessions nobody watches) |
| D3 | The cursor is **derived from the newest commentary row's `anchor`**, never persisted separately | Removes a table, removes a write, and — the real reason — a persisted cursor would have to live in `session.metadata`, and *every* write there publishes a full `session.updated` (`session/session.ts:761-764` → `patch()`), i.e. a whole-session SSE broadcast every 10 s. See §9.4. | `session.metadata` blob (looks simpler, costs a broadcast per tick) |
| D4 | The narration contract is **JSON**, not prose and not a sentinel | The LLM must be able to *choose silence*. A sentinel (`WAIT`) is cheaper but cannot be told apart from a model that genuinely wrote the word "wait". JSON also gives a place for a future `"until"` field. | `WAIT` sentinel; free-form text with a length heuristic |
| D5 | Continuity comes from the **last 100 commentary entries**, not the last 100 session messages | The user said "previous 100 message" in a sentence about continuity of the *talk*. Feeding 100 raw session messages on every tick would cost more than the turn itself and would not read as a continuing narrative. The raw side is covered by the digest; the talk side is covered by the entries. | 100 raw session messages (expensive, redundant, not continuous) |
| D6 | The default model is the **session's model**; `small` is opt-in via config | The user's words were "the same model that opencode using", and the session model is the faithful one. A 10 s cadence makes cost real, so the escape hatch is a config key, not a code change. | Default small model |
| D7 | The panel is **desktop-only** in this cut | The entire side panel is behind `createMediaQuery("(min-width: 768px)")` (`session.tsx:449`) and the header buttons are inside `hidden md:flex` (`session-header.tsx:464`). Adding a mobile surface is a separate, larger job — filed as FU-111, not silently skipped. | Also build the phone sheet now |
| D8 | Opening commentary **collapses the file tree** | Three columns do not fit next to a chat that must stay readable. Of the three, the file tree is the least valuable while a turn is running, and it is already collapsible with a persisted flag. | Let all three fight for width |

---

## 2. Architecture

```
┌─ browser ──────────────────────────────────────────────────────────────────┐
│  session-header.tsx     [Toggle commentary]  ← new, beside [Toggle review]  │
│  use-session-commands   commentary.toggle (mod+shift+c)                     │
│  commentary-panel.tsx   the third column                                    │
│  global-sync            POST /commentary/watch  every 15 s while visible   │
│  event-reducer          case "session.commentary" → append to the list      │
└───────────────┬───────────────────────────────────────────┬─────────────────┘
                │ POST watch/unwatch (lease, 45 s TTL)     │ SSE /event
┌───────────────▼───────────────────────────────────────────▼─────────────────┐
│ server                                                                    │
│   SessionCommentary service  (packages/opencode/src/session/commentary.ts) │
│     ├─ lease:  Map<SessionID, expiresAt>        (in memory, per instance)  │
│     ├─ loop:   one fiber, every `interval` ms   (default 10 000)           │
│     ├─ tick(s): busy(session) && leaseLive(s)  →  digest → llm.stream      │
│     └─ rows:   insert into session_commentary, publish Session.Commentary  │
│   GET  /api/session/:id/commentary   initial paint                         │
└────────────────────────────────────────────────────────────────────────────┘
                                   │
                            session_commentary (new table)
                            id, session_id, seq, time, text, anchor
```

---

## 3. The server service

`packages/opencode/src/session/commentary.ts` (new) — same family and same `LayerNode.make` shape as
`sessions/summary.ts`.

### 3.1 The table

Declared in `packages/core/src/session/sql.ts` beside `SessionTable` (`:22`):

```ts
export const SessionCommentaryTable = sqliteTable(
  "session_commentary",
  {
    id:         text().$type<SessionCommentary.ID>().primaryKey(),
    session_id: text().$type<SessionSchema.ID>().notNull().references(() => SessionTable.id, { onDelete: "cascade" }),
    seq:        integer().notNull(),
    time:       integer().notNull(),
    text:       text().notNull(),
    anchor:     text().$type<SessionMessage.ID>().notNull(),   // last message this entry describes
  },
  (table) => [
    index("session_commentary_session_seq_idx").on(table.session_id, table.seq),
    uniqueIndex("session_commentary_id_unique").on(table.session_id, table.seq),
  ],
)
```

Then, from `packages/core`: `bun run migration` → migration + `schema.gen.ts` + `migration.gen.ts`
(all generated from `packages/core/schema.json`; nothing hand-edited). The migration file format is one
`tx.run(...)` per statement — see `20260928004444_useful_manta.ts` for the shape.

`anchor` is **not** optional, deliberately: an entry without an anchor is an entry the next digest cannot
resume from.

### 3.2 The cursor (D3)

```
cursor(sessionID) = MAX(anchor) over the newest rows of session_commentary
                  = the anchor of the row with the greatest seq
digestFrom(sessionID) = messages strictly after cursor(sessionID)
no rows yet  → seed from the LAST 6 messages (so the first entry is about the current turn,
               not the whole session; a fresh panel on a 300-message session must not narrate history)
```

Restart-safe by construction: after a server restart the cursor is whatever the last row said, and if there
are no rows the seed applies. Nothing to rebuild, nothing to migrate.

### 3.3 The output contract (D4)

The prompt asks for exactly this object and nothing else:

```json
{"speak": true,  "text": "…at most ~30 words…"}
{"speak": false}
```

The parser is deliberately forgiving, in this order:

1. strip a fenced ```` ```json ```` block if present;
2. take the first balanced `{…}`;
3. `JSON.parse`, read `speak` (truthy) and `text` (string);
4. **any failure → treat as `speak: true` with the raw text.** A model that ignored the format still produced
   something worth showing, and silently dropping it is the worse failure. The raw text is then trimmed and
   cut to `maxEntryChars`.

The server, not the model, owns every ceiling: `MAX_ENTRY_CHARS = 240`, `MAX_ENTRIES_PER_TURN = 20`.

### 3.4 The digest serializer

A v1 serializer in `commentary.ts`. **Do not reuse `SessionCompaction.serialize`** — it is
`packages/core/src/session/compaction.ts:95-121` over v2 `SessionMessage`, is not exported for v1 messages,
and its labels read like a compaction summary. Model it, do not import it.

| Part | Rendered as | Cap |
|---|---|---|
| user text | `› <text>` | 400 chars |
| user file | `› [attached <mime>: <name>]` | — |
| assistant text | `<text>` verbatim | — (this is the point of the panel) |
| assistant tool call | `→ <name>(<args>)` then `← <result>` or `← error: <msg>` | args 160, result 200 |
| assistant reasoning | **excluded** | — |
| `step-start` / `step-finish` / `snapshot` / `patch` | **excluded** | — |
| `subtask` | `⇢ subtask: <prompt>` | 120 |
| shell / synthetic / system | one line | 160 |

Total digest ceiling **12 000 chars**, trimmed from the **front** so the newest activity always survives.

Reasoning is excluded on purpose: it is usually hidden from the user, it is the bulkiest text in a turn, and
the narrated result of a thought is the tool call that follows it.

### 3.5 Continuity (D5)

The prompt carries two blocks:

```
<narration-so-far>
…up to the last 100 commentary texts for this session, oldest first…
</narration-so-far>

<new-activity>
…the digest from §3.4…
</new-activity>
```

100 entries × ~30 words ≈ 4 k tokens, affordable. It is additionally truncated from the front to a
**24 000-char** budget, so a pathological run of long entries cannot blow the context.

### 3.6 The LLM call

A sibling of `ensureTitle` (`prompt.ts:193-253`):

```ts
const agent = yield* agents.get("commentary")                 // new hidden built-in, §3.7
const providerID = session.model.providerID
const model = settings.model === "small"
  ? ((yield* provider.getSmallModel(providerID)) ??
     (yield* provider.getModel(providerID, session.model.modelID)))
  : (yield* provider.getModel(providerID, session.model.modelID))
const text = yield* llm
  .stream({
    agent,
    user: syntheticUser,          // a throwaway SessionV1.User with a generated id
    sessionID: session.id,
    model,
    small: settings.model === "small",
    system: [],
    tools: {},                    // never: the commentator gets no tools
    retries: 1,                   // title uses 2; a failed tick must not stall the loop
    messages: [...toModelMessages(digest), { role: "user", content: INSTRUCTIONS }],
  })
  .pipe(
    Stream.filter(LLMEvent.is.textDelta),
    Stream.map((e) => e.text),
    Stream.mkString,
    Effect.orDie,
  )
```

`SessionV1.WithParts[]` → `ModelMessage[]` via the same `MessageV2.toModelMessagesEffect` the title path
uses, so the model sees the digest in the shape it already knows.

**`small: true` and the model choice must agree** — passing `small: true` together with a full model is what
the title path avoids by construction; here the config key drives both, so they cannot disagree.

### 3.7 The `commentary` agent

In `packages/opencode/src/agent/agent.ts`, immediately after `title` (`:233`) and `summary` (`:248`):

```ts
commentary: {
  name: "commentary",
  mode: "primary",
  options: {},
  native: true,
  hidden: true,                    // never in the agent picker
  temperature: 0.5,                // same as title: narration should not be robotic
  permission: Permission.merge(defaults, Permission.fromConfig({ "*": "deny" }), user),
  prompt: PROMPT_COMMENTARY,      // packages/opencode/src/agent/prompt/commentary.txt
},
```

`hidden` + `native` + `"*": "deny"` is exactly the `title`/`summary` shape, and `agents.get("title")`
resolves a hidden agent today — so `agents.get("commentary")` will too (verify in P1; it is the one
assumption in this section that is inferred rather than read).

`commentary.txt` must state, at minimum:

- output **only** the JSON object, nothing around it;
- ≤30 words, one short paragraph, present tense, describing *what the agent is doing and why it matters*;
- **continue the narration** in `<narration-so-far>` — do not open a new topic each time, do not recap it,
  and **never refer to the previous lines** ("as I said before…") or to being an observer;
- `speak: false` when there is nothing worth saying (a poll, a duplicate step, a wait) — silence is the
  correct answer most ticks;
- **same language as the user's messages** (the `title` prompt's rule, `:8`);
- name real files/commands exactly; do not invent progress.

### 3.8 The loop

One fiber per instance, forked where the instance scope is available, ticking on
`Schedule.spaced(settings.interval ?? 10_000)`. Each tick:

```
for (sessionID of liveLeases())          // Map iteration; expired entries are deleted in place
  if (!busy(sessionID)) continue                       // nothing is happening: never speak
  if (inFlight.has(sessionID)) continue                // one call per session, never overlapping
  if (sinceLastEntry(sessionID) < MIN_GAP_MS) continue
  if (entriesSinceLastUserMessage(sessionID) >= MAX_ENTRIES_PER_TURN) continue
  const digest = digestFrom(sessionID)
  if (digest.length < MIN_ACTIVITY_CHARS) continue     // ← this gate alone kills most empty ticks
  inFlight.add(sessionID); speak(sessionID, digest).finally(() => inFlight.delete(sessionID))
```

The tick body is `Effect.ignore`-wrapped per session so one failure cannot kill the loop — the same shape
`prompt.ts:1139` uses for its forked work.

`busy(sessionID)` reads the same status the app reads (`session.status`; the app's own definition of "doing
something" is `status !== "idle"`, so `retry` counts as busy — which is correct here, a backoff is news).

### 3.9 Cost guards — the numbers

| Guard | Default | Why |
|---|---|---|
| `interval` | 10 000 ms | the user's cadence |
| `MIN_GAP_MS` | 10 000 | a call that takes 8 s must not be followed immediately by another |
| `MIN_ACTIVITY_CHARS` | 120 | **the important one** — a tick with almost nothing new never calls the LLM at all |
| `MAX_ENTRIES_PER_TURN` | 20 | a 10-minute turn cannot produce 60 entries; the counter resets on each user message |
| `MAX_DIGEST_CHARS` | 12 000 | one `bash` result must not cost more than the narration |
| `MAX_ENTRY_CHARS` | 240 | ~30 words, enforced server-side |
| `NARRATION_HISTORY` | 100 | the user's number, from §3.5 |
| `NARRATION_CHARS` | 24 000 | the budget behind that 100 |

A 5-minute turn therefore costs **at most ~20 calls**, usually far fewer, and zero when nothing is happening.

---

## 4. Routes, event, config

### 4.1 Routes (v1 instance API, `packages/opencode/src/server/routes/instance/httpapi/`)

| Route | Group file | Handler | Purpose |
|---|---|---|---|
| `POST /api/session/:sessionID/commentary/watch` | `groups/session.ts` (beside `summarize` at `:303`) | `handlers/session.ts` | set `lease[sessionID] = now + 45_000` |
| `POST /api/session/:sessionID/commentary/unwatch` | same | same | delete the lease |
| `GET  /api/session/:sessionID/commentary?limit=50` | same | same | `{ data: Entry[] }`, newest last, for the initial paint |

Follow the `summarize` endpoint's exact shape (`:303-314` in the group, `:273-290` in the handler): same
`SessionID` param, same `WorkspaceRoutingQuery`, same error set, same `HttpApiSchema.described` wrapper.

The client calls these with a hand-rolled `fetch` + Basic auth, **not** the generated SDK — the
`fetchWebuiStatus` pattern (`packages/app/src/utils/server.ts:118-134`) — so **no `bun run generate` in
`packages/client` is needed for the routes**. The *event* still needs the client regenerated if it is added
to the client-side union (§9.11).

### 4.2 The event (new file, existing pattern)

`packages/schema/src/session-commentary-event.ts`, modelled on `session-status-event.ts`:

```ts
export const Entry = Schema.Struct({
  id: Schema.String, sessionID: SessionID, seq: Schema.Finite,
  time: Schema.Finite, text: Schema.String, anchor: Schema.String,
}).annotate({ identifier: "SessionCommentaryEntry" })

export const Posted = Event.define({
  type: "session.commentary",
  schema: { sessionID: SessionID, entry: Entry },
})
```

Registered in the v1 inventory at `packages/schema/src/v1/session.ts:659-676` (`Event = { …events, PartDelta,
Diff, Error, Definitions: inventory(…) }`) — add the definition to the `inventory(...)` call, and re-export
from `packages/core/src/v1/session.ts` if the client union needs it.

### 4.3 Config

New `packages/core/src/v1/config/commentary.ts`, mounted with the self-export pattern the style guide
requires (`export * as ConfigCommentary from "./commentary"`), and referenced from the config document:

```ts
export const Commentary = Schema.Struct({
  enabled:            Schema.optional(Schema.Boolean),                        // default true
  interval:           Schema.optional(PositiveInt),                          // ms, default 10_000
  model:              Schema.optional(Schema.Literals(["session", "small"])), // default "session"
  maxEntriesPerTurn:  Schema.optional(PositiveInt),                          // default 20
  minActivityChars:   Schema.optional(PositiveInt),                          // default 120
  narrationHistory:   Schema.optional(PositiveInt),                          // default 100
}).annotate({ identifier: "CommentaryConfig" })
```

**The FE-023 rule applies verbatim:** an undeclared key is dropped by `onExcessProperty: "ignore"`, so a
setting in `opencode.json` that has no schema entry **silently does nothing**. The schema entry is not
optional work. Do not add an Admin row for this in the first cut — a hand-edited config key is enough until
the feature proves itself.

---

## 5. The app

### 5.1 Files

| # | File | Change |
|---|---|---|
| 1 | `packages/ui/src/components/icon.tsx` | `commentary` + `commentary-active`, derived from the existing `speech-bubble` path (`:3-…`) so the pair reads like `review`/`review-active` (`:28-29`). |
| 2 | `packages/app/src/context/layout.tsx` | `commentary: { panelOpened, width }` in the store (beside `review`, `:695-703`) and a `view().commentaryPanel.{opened,open,close,toggle}` accessor beside `reviewPanel` (`:905-917`). **Absent = closed** → no migrate branch, no `layout.v6` bump (DEC-052). |
| 3 | `packages/app/src/components/session/session-header.tsx` | the new button, copied from the review button (`:465-478`), placed **immediately after** it, `aria-controls="commentary-panel"`. |
| 4 | `packages/app/src/pages/session/use-session-commands.tsx` | `commentary.toggle` command. `mod+shift+r` is taken by review → use **`mod+shift+c`**. |
| 5 | `packages/app/src/components/command-palette.ts:43` | add `"commentary.toggle"` to the allowlist, or the palette entry is filtered out. |
| 6 | `packages/app/src/pages/session/commentary-panel.tsx` (new) | the panel itself (§5.2). |
| 7 | `packages/app/src/pages/session/session-side-panel.tsx` | the third `<div id="commentary-panel">` sibling of the review column (`:318-757`) and the file-tree column (`:759-861`), with its own `ResizeHandle` (copy `:845-859`). |
| 8 | `packages/app/src/pages/session.tsx` | `desktopCommentaryOpen()`, fold it into `desktopSidePanelOpen()` (`:461`) and into `sessionPanelMax()` (`:486-489`) so the chat keeps its floor; pass `commentaryPanel={…}` into `<SessionSidePanel>` (`:2304`/`:2321`). |
| 9 | `packages/app/src/context/global-sync/event-reducer.ts` | `case "session.commentary"` — append to the per-session entry list. The switch has no throwing default, so an **older client safely ignores the new event**; app and server can deploy independently. |
| 10 | `packages/app/src/context/server-session.ts` | the initial `GET`, and the watch/unwatch + 15 s heartbeat lifecycle. |
| 11 | `packages/app/src/i18n/*.ts` — **65 files** | the new keys, English everywhere, per the FU-026 pattern. |

### 5.2 The panel component

```
┌─ Commentary ─────────── 7 ─┐
│ 07:41  Reading the tool row │
│       definitions to find   │
│       where the retry lands │
│ 07:51  The retry backoff is │
│       provider-side; the    │
│       third attempt is in   │
│ 08:02  …                    │
└─────────────────────────────┘
```

- newest at the **bottom**, auto-scroll **only if already at the bottom** (never yank the view while the
  user has scrolled up to read);
- each entry: relative time (`ui.message.duration.*` already exists and is translated) + the text;
- states: **empty** (panel open, session idle → "Commentary appears while the agent works"), **waiting**
  (session busy, nothing said yet → a small pulsing indicator + "Watching the agent"), **list**;
- `data-slot="session-commentary-entry"` on each row, `data-slot="session-commentary-list"` on the scroller,
  so the e2e probes and the benchmark have stable hooks (house convention);
- entries are **read-only** in this cut. No edit, no delete, no regenerate.

### 5.3 Width policy (D8)

The side panel today is `auto` (review) + `fileTree.width()` (200 px default, `layout.tsx:31`). Three columns
need an explicit budget:

- commentary: **340 px** default, resizable **260–520**;
- opening commentary calls `layout.fileTree.close()` (it already has a persisted `opened` flag);
- `sessionPanelMax()` subtracts the commentary width so the chat column never drops below its floor;
- below 1280 px the commentary column clamps to 260 px.

### 5.4 Watch lifecycle (the lease)

```
panel becomes visible  → POST /commentary/watch
every 15 s while visible → POST /commentay/watch   (refreshes the 45 s TTL)
panel hidden / unmount  → POST /commentary/unwatch, and navigator.sendBeacon on pagehide
no sendBeacon support   → the 45 s TTL is the backstop; nothing to clean up
```

The interval **must be strictly shorter than the TTL** (15 s vs 45 s) so one dropped request — a phone going
to sleep, a tunnel hiccup — cannot silently end the narration.

---

## 6. Build order

| Phase | Work | Gate |
|---|---|---|
| **P1** | Table + `bun run migration` + the `commentary` agent + `commentary.txt` + `config/commentary.ts` | `bun typecheck` in `packages/core` and `packages/opencode`; migration applies on a scratch DB |
| **P2** | `packages/opencode/src/session/commentary.ts`: digest serializer, cursor, JSON parse, `speak`, lease, loop | unit tests for every pure function; a manual tick against a live session with a stubbed model |
| **P3** | Event + the three routes + the handler | `test:httpapi` scenario; `bun typecheck` |
| **P4** | The app: icon, store, button, command, panel, column, width, reducer, watch lifecycle, i18n | `bun turbo typecheck` 30/30; app unit incl. **i18n parity 5/5**; oxlint 0 errors |
| **P5** | Benchmark + live verification + docs | see §7 |

---

## 7. Tests, benchmark, gates

**Unit (`packages/opencode/test/session/commentary.test.ts`)** — the pure logic, which is where the bugs
will be: digest serialization per part type, reasoning excluded, the front-trim at 12 000 chars, cursor
derivation from the newest row, the "no rows → last 6 messages" seed, the lenient JSON parser (fenced,
bare, malformed, `speak: false`, over-long text), the `minActivityChars` gate, the
`maxEntriesPerTurn` reset on a user message, the 100-entry narration budget + its char trim.

**App** — `event-reducer.test.ts` gains a `session.commentary` case (append, and the unknown-event no-op
that older clients rely on); a layout-store test for `commentary.panelOpened` defaulting to closed; i18n
parity 5/5 over 65 files.

**`test:httpapi`** — one commentary scenario. Per **FU-094's lesson**: assert decode + declared errors +
shape, and do **not** write an order-dependent seeded scenario (the runner loads the instance at
`runner.ts:96` *before* the seed at `:188`, so a seeded row is invisible to the route under test).

**Benchmark** (`packages/app/AGENTS.md` requires a baseline before touching session code): the panel is
mounted only while opened, so the numbers to record are (a) closed state — 0 extra DOM nodes, 1 memo;
(b) open state — scroll height and paint cost for 50 entries; (c) the 10 s tick's effect on the message
timeline's re-render count, which must be **zero** (the commentary event touches only the commentary store,
not the message store — that isolation is the point and must be measured, not assumed).

**Gates before any commit:** `bun turbo typecheck` (30/30), app unit, oxlint, i18n parity, `test:httpapi`.
**Before any build:** `git status` — FU-082 bit three times because the build compiles the whole checkout
and an in-flight session's edits ship in the binary. `s081`'s work (`document-title.tsx`, `app.tsx`) is
uncommitted in this checkout right now.

---

## 8. i18n keys

`command.commentary.toggle` ("Toggle commentary"), `session.commentary.title` ("Commentary"),
`session.commentary.empty` (idle, nothing to say), `session.commentary.waiting` (busy, not yet),
`session.commentary.watching`. Five keys × **65 locale files**, English values everywhere, per FU-026 —
a real translation sweep is a separate follow-up, not something to fabricate from model knowledge
(`packages/app/AGENTS.md` forbids that outright).

---

## 9. Risks and traps

1. **The 10 s loop is the only timer in the engine.** Everything else is event-driven. It must be
   `Effect.ignore`-wrapped per session, must never overlap a call for the same session, and must be forked
   into the instance scope so it dies with the instance. Verify it does not survive `server.instance.disposed`
   — the app's reducer has a case for that event (`event-reducer.ts:127`) precisely because instances come
   and go.
2. **Cost.** 20 entries/turn on the session's own model is real money. `minActivityChars` is the mitigation
   that matters; it must be tuned by observation, not left at a guess.
3. **`llm.stream` with a synthetic user message must publish nothing.** `ensureTitle` is the proof that it
   does not (it passes a *real* user message and only reads the text), but the synthetic id is new — verify
   no `message.updated` event appears for it, or the timeline will grow phantom user messages every 10 s.
4. **Do not "fix" the cursor by persisting it.** A cursor in `session.metadata` writes through
   `Session.setMetadata` → `patch()` (`session/session.ts:761-764`) → a full `session.updated` broadcast
   **every tick**, which re-renders the sidebar's whole session list every 10 s. D3 exists to make that
   tempting change obviously wrong.
5. **Two clients, one narration.** Two panels on the same session hold two leases; the lease is a
   `Set`/`Map` of session ids, so the loop still speaks **once**. Do not turn it into a counter.
6. **Server restart mid-turn** → the cursor falls back to the last entry's anchor, or the 6-message seed.
   Expected, documented, not a bug.
7. **One long tool result** → the serializer's 200-char cap plus the 12 000-char digest cap. Without both, a
   single `bash` output can cost more than the entire narration.
8. **The 10 s cadence is a floor, not a guarantee.** `MIN_GAP_MS` prevents overlap, not back-to-back calls.
9. **The prompt must forbid meta-commentary.** Without "never refer to the previous lines", the narration
   degenerates into "As I mentioned earlier…", which is the single most likely visible failure of this feature.
10. **Language.** The prompt inherits the `title` prompt's rule (same language as the user's messages). A
    zh user must get zh narration, and the locale must not be forced to the UI language — the user may be
    reading an English conversation in a Chinese UI.
11. **The event may require a client regen.** The three *routes* deliberately use a hand-rolled fetch so no
    `bun run generate` is needed. The *event*, if it goes into the client-side union, does — run
    `bun run generate` from `packages/client` and commit the result, or the union will not type it.
12. **Build hygiene (FU-082).** `git status` before `build-linux.sh`; build from a detached worktree at
    `origin/dev` if this must not carry anyone's WIP (the DEC-052 throwaway-worktree recipe).
13. **Subagent sessions.** The loop keys on any leased session, so a subagent tab with the panel open gets
    its own narration. That is probably right, but it is a behaviour to confirm, not assume.

---

## 10. Explicitly out of scope

- **Mobile placement.** The panel is desktop-only in this cut (D7). The phone story deserves its own design
  — most likely a bottom sheet, given the mission — filed as **FU-111**.
- An Admin settings row for `session.commentary.*` (hand-edited config for now).
- Editing, deleting, or regenerating an entry.
- Sharing or exporting the narration.
- Narration for sessions other than the ones a human has open.
- Retroactive narration of a session that is already finished.
