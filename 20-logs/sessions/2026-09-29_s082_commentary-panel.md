# s082 — FE-028: the Commentary panel (a live, LLM-written narration of the agent's work)

- **Opened (UTC):** 2026-09-29
- **Status:** CLOSED — **committed, pushed, deployed and live-verified.** Build `1.1.20260929072355`, pid 1005463 on :4447. Commits `412984d` (feature) + `d0d0fd5` and `4218986` (two bugs only the live server exposed).
- **Fork:** `50-projects/p003-opencode-fork/opencode` (`dev`, HEAD `a9029ff` + s081's `e76ffba`)
- **Plan:** `50-projects/p003-opencode-fork/notes/plan-commentary-panel.md`
- **Decision record:** DEC-057 · **Follow-ups:** FU-110 (build) + FU-111 (mobile variant)

## Request (verbatim)

> plan a new big enhencement
> prepare a new commentary panel next to review panel control similar to "Toggle review" button.
> so the new review panel will be showing commentary desc current agent work
> the commentary will talk message by message. each message would not be too long. it is around 30 words.
> each message is added with interval 10s and is subject to llm to decide whether it is nice to add or wait
> next time. the message is a digest from the agent chat windows context (word + tools call) from the last
> commentary cursored context. the message will also consider the previous 100 message to make it a
> continuouity talk. the message is generated as a separated llm call using the same model that opencode
> using. u should know what i need now and try to plan it

## Scope questions asked before planning (the answers reshaped the design)

1. **Placement** → **a third column beside the Review panel (desktop).** Not a tab inside the side panel
   (you would not see commentary and diffs together), not a bottom panel like the Terminal.
2. **Who runs the 10 s call** → **a server-side loop, gated on "some client currently has the panel open"**
   (a lease). Not always-on-while-busy (spends tokens on unwatched sessions), not client-driven (each
   browser would invent its own narration).
3. **Which model** → **the session's own model, configurable to the provider's small model** via a config
   key. Noted in the plan that a 5-minute turn is up to 30 calls, and that the cost guards (below) are what
   make that acceptable.

## What the code says (all of it read, none of it from memory)

| Need | Found |
|---|---|
| A sidecar LLM call, session model, no tools, read the text | `SessionPrompt.ensureTitle` — `packages/opencode/src/session/prompt.ts:193-253` |
| The v2 twin | `packages/core/src/session/compaction.ts:176-231` |
| A hidden internal agent to carry the prompt | `title` / `summary` — `packages/opencode/src/agent/agent.ts:233-258` + `prompt/*.txt` |
| The serializer model (words + tool calls) | `SessionCompaction.serialize` — `compaction.ts:95-121` (**not reusable**: core/v2, v2 messages) |
| The session's model | `Session.Info.model` — `packages/opencode/src/session/session.ts:237`; `provider.getModel` / `getSmallModel` — `provider.ts:1198,1204` |
| The LLM call shape | `LLM.StreamInput` — `packages/opencode/src/session/llm.ts:35-48` |
| A standalone session event | `packages/schema/src/session-status-event.ts` (`Event.define`) + the v1 inventory at `packages/schema/src/v1/session.ts:659-676` |
| The app's event switch (and its safe default) | `context/global-sync/event-reducer.ts:126` — no throwing default, so an old client ignores a new event |
| A hand-rolled route call, no SDK regen | `fetchWebuiStatus` — `packages/app/src/utils/server.ts:118-134` |
| The third-column precedent | the file tree is already a sibling column with its own `ResizeHandle` — `pages/session/session-side-panel.tsx:759-861` |
| The button / command / palette trio to copy | `session-header.tsx:465-478`, `use-session-commands.tsx:562-566`, `command-palette.ts:43` |
| Persisted open/closed, no version bump | `store.review.panelOpened` — `context/layout.tsx:695-703`, accessor `:905-917`, Persist key `layout.v6` at `:271` |
| A table, generated | `packages/core/src/session/sql.ts:22` + `bun run migration` (`packages/core/script/migration.ts`) |
| The i18n surface | **65** locale files + `i18n/parity.test.ts` |

## The five judgement calls in the plan (each with a rejected alternative, in the doc)

1. **The cursor is derived, not stored.** The newest commentary row carries the `anchor` message id it
   describes; the next digest is everything strictly after it. No cursor table — and, more importantly, this
   avoids the trap: a persisted cursor would live in `session.metadata`, and `Session.setMetadata` →
   `patch()` (`session/session.ts:761-764`) broadcasts a **full `session.updated` every tick**, re-rendering
   the sidebar's whole session list every 10 s.
2. **"Let the LLM decide" is a JSON contract** (`{"speak":false}` / `{"speak":true,"text":"…"}`) with a
   forgiving parser whose failure mode is *show it anyway* — not a `WAIT` sentinel, which cannot be told
   apart from a model that genuinely wrote "wait".
3. **Continuity = the last 100 commentary entries**, not the last 100 session messages. The user said "100
   message" inside a sentence about continuity of the *talk*; 100 raw session messages per tick would cost
   more than the turn and would not read as a continuing narrative. The raw side is already covered by the
   digest.
4. **Cost guards, with numbers.** `minActivityChars: 120` is the one that matters — a tick with almost
   nothing new never calls the LLM at all. Then `interval 10 s`, `minGap 10 s`, `maxEntriesPerTurn 20`
   (reset on each user message), `maxDigest 12 000 chars`, `maxEntry 240 chars`, `narration 100 entries /
   24 000 chars`. A 5-minute turn is therefore **at most ~20 calls**, usually far fewer, zero when idle.
5. **Reasoning is excluded from the digest.** It is the bulkiest text in a turn, usually hidden from the
   user, and the narrated result of a thought is the tool call that follows it.

## Two things the plan deliberately does *not* cover

- **Mobile.** The whole side panel is behind `min-width: 768px` and the header buttons sit in `hidden
  md:flex`, so the panel is desktop-only in this cut. Given the project's mobile-first mission that is a
  real gap, not a detail — filed as **FU-111** rather than quietly dropped.
- **The 10 s loop is the only timer in the engine.** Everything else is event-driven. It is the highest-risk
  item in the build order (P2) and the first thing to test.

## Deliverable

`50-projects/p003-opencode-fork/notes/plan-commentary-panel.md` — 10 sections: executive summary, the eight
decisions, architecture diagram, the server service (table / cursor / contract / serializer / continuity /
LLM call / agent / loop / cost table), routes+event+config, the app (11 files, panel mock, width policy,
watch lifecycle), the P1-P5 build order, tests+benchmark+gates, 13 risks, explicit out-of-scope.


---

## Close-out (same session, after "go" and "continue")

P1 → P5 all executed. **103 paths** (30 modified + 11 new + 62 locale files), non-locale **+783/−63**.

| Phase | What | Gate |
|---|---|---|
| P1 | `session_commentary` table + generated migration, the `session.commentary` event, the hidden `commentary` agent + `commentary.txt`, the `commentary` config section | `turbo typecheck` 30/30 · core migration 19/19 (incl. "applies tracked migrations to an empty database") |
| P2 | `SessionCommentary`: digest serializer, derived cursor, JSON contract, lease, the 10 s loop | 47/47 new tests; 614/614 in the touched packages |
| P3 | `GET /session/{id}/commentary`, `POST …/watch`, `POST …/unwatch` | 4/4 route tests over real HTTP · `test:httpapi` 215/0/0/0 × 3 modes, exit 0 |
| P4 | icon pair, layout store, header button, `mod+shift+c`, palette, panel, third column, width math, reducer, watch lifecycle, 62 locales | app `test:unit` 792/0 · i18n parity 5/5 · oxlint 0 errors |
| P5 | the benchmark `packages/app/AGENTS.md` requires | flat cost from a 10- to a 5000-message timeline |

**The verified claims, not the asserted ones:**
- the model call is a sidecar — **no tools**, the **session's own model**, the digest in the prompt;
- the event is **published**, so a stored entry is not invisible to an open client;
- **no message leaks into the timeline** (2 messages before and after) — this was risk #3 in the plan and is
  now a standing assertion that fails loudly if it regresses;
- per-line cost is **O(1) in timeline size** — the isolation claim, measured across a 500× range.

**Three defects in my own code, caught by its own tests:** the off-by-one ellipsis in `truncate`; the
`{"speak":true,"text":""}` fallthrough that would have stored raw JSON as a narration line; and the backwards
`SESSION_CONTENT_EVENTS` assumption that would have deleted the narration in trimmed views.

**Two pre-existing problems found and filed, neither caused by this work:** the schema manifest test was
already red on `dev` (FU-113) and `test:httpapi --mode auth` leaves a stray `config.json` in the repo
(FU-112). Both were proved pre-existing by re-running them against a clean tree.

**Four plan corrections** are recorded with their reasons in the DEC-057 addendum. The one worth repeating:
the min-gap moved from an in-memory map to the newest stored entry, which removed redundant state *and*
fixed a restart bug, and forced `minGap` to become a real config key because effect `4.0.0-beta.83`'s
`TestClock.adjust` is broken.

**Out of scope, filed not dropped:** FU-111 (the panel is desktop-only, which is a real gap in a
mobile-first product) · real `zh`/`zht` translations (English everywhere per the FU-026 pattern).
