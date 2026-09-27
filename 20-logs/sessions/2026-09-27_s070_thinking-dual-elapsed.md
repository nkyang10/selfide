# s070 — Thinking dual elapsed counters (FE-021)

> Session record. Opened 2026-09-27 (UTC). Project: `50-projects/p003-opencode-fork` (fork `dev`).

## Request

User (verbatim intent): the fork on :4447 already shows an elapsed time after "Thinking" (s048 /
FU-055). Enhance it to `Thinking [sec from previous tool call or text update from the LLM / sec from
the user prompt]`, so the user can tell **when the LLM last responded** and **how long the prompt has
been running**.

## What the existing code does (verified by reading)

`packages/app/src/pages/session/timeline/message-timeline.tsx`

- `TimelineThinkingRow` (line 141): 1 s `setInterval` ticker, renders
  `ui.sessionTurn.status.thinking` via `TextShimmer` + `ui.message.duration.seconds` into
  `data-slot="session-turn-thinking-elapsed"`.
- Call site (line 1270-1285): `baseTime = lastAssistantMessageOfTurn?.time.created ?? userMessage.time.created`.

**Gap 1 — "since last output" is actually "since this step started".** A streaming part keeps its
original `time.start`, so the number grows while text/reasoning tokens keep arriving.
**Gap 2 — no prompt-relative time at all.**

**Data available** (`packages/sdk/js/src/v2/gen/types.gen.ts`): `ToolPart.state.time` =
`{start}` (running) / `{start,end}` (completed,error); `TextPart.time?` = `{start,end?}`;
`ReasoningPart.time` = `{start,end?}`; `AssistantMessage.time` = `{created, completed?}`.
Client store mutates `part.text` on every `message.part.delta`
(`packages/app/src/context/server-session.ts:1190`), so a delta is observable.

**Visibility (important, verified):** `rows.ts:193` —
`isActive && busy && !error && (showReasoning ? assistantPartRefs.length === 0 : true)`. Default is
`showReasoningSummaries: false` (`packages/app/src/context/settings.tsx:194`), so the row is the
**live footer of the whole busy turn** — visible under streaming text. With reasoning summaries ON
the row hides at the first reasoning text (pre-existing behaviour, untouched).

## Plan (approved shape)

1. New pure helper `packages/app/src/pages/session/timeline/turn-activity.ts` +
   `turn-activity.test.ts`: `latestTurnActivity({ messages, parts }) -> { at, key }`.
   `at` = max(assistant `created`/`completed`, each part's last server time). `key` = fingerprint
   that also changes on in-flight streamed updates.
2. Row: `createEffect(on(() => activity().key, () => setObserved(Date.now()), { defer: true }))`,
   **A = max(at, observed)**. `defer` prevents a mount (page reload mid-turn / virtualizer remount)
   from stamping "now" and showing 0 s.
3. `TimelineThinkingRow` takes `activityAt` + `promptAt`, renders `· A / B` reusing the already
   translated `ui.message.duration.seconds` / `ui.message.duration.minutesSeconds`.
4. One new i18n key for the tooltip (also prints the absolute clock time of the last model output).
5. `max(0, …)` guards clock skew. No other row/CSS/visibility change.

## Baselines (before any edit)

| Gate | Result |
|---|---|
| `bun typecheck` (packages/app) | clean (`tsgo -b`) |
| app unit suite | **755 pass / 1 fail** — fail is the pre-existing FU-076 i18n parity (6 `settings.general.notifications.rss.*` keys missing in all 60 locales) |
| oxlint `packages/app/src` | **0 errors**, 822 warnings (pre-existing) |

Environment note: **no `node` binary on this machine**, so `bun run lint` (oxlint needs node) fails.
Ran the type-aware pass with a throwaway shim `/tmp/opencode/nodeshim/node` → `exec bun "$@"`.

## Result

**Shipped (source, uncommitted):** `Thinking · A / B` — A = seconds since the last model output, B = seconds
since the user prompt — with a localized tooltip that also prints the absolute clock time of the last output.

| File | Change |
|---|---|
| `packages/app/src/pages/session/timeline/turn-activity.ts` | **new.** `latestTurnActivity({ messages, parts, observed })` → `{ at, key }` |
| `packages/app/src/pages/session/timeline/turn-activity.test.ts` | **new.** 9 cases |
| `packages/app/src/pages/session/timeline/message-timeline.tsx` | +48/−13 |
| `packages/app/src/i18n/en.ts` + 61 locale files | `session.thinking.elapsed` (+ the 6 RSS keys → FU-076) |

**Bugs caught in my own work, before shipping**

1. **Infinite reactive loop.** `createEffect(on(() => activity().key, () => setObserved(Date.now()), { defer: true }))`
   reads correct but loops forever: `setObserved` invalidates `activity()`, which re-fires the effect, which
   stamps again. Solid's `on` only compares element-wise in the **array** form
   (`node_modules/solid-js/dist/solid.js:457-475`); the single-dependency form has no dedupe. Replaced with an
   explicit previous-fingerprint comparison — which also subsumes what `defer` was for (a mount must not stamp
   "now").
2. **Flicker.** Gating the row on `A > 0` makes the counter disappear on every delta while the model streams,
   because `A = 0` is the *healthy* case. Gate moved to `B > 0`.
3. Typecheck: `ToolStatePending` has no `time`; `"end" in time` narrowing for the running/completed union;
   `undefined` is not assignable into the `(string | number)[]` fingerprint.

**Gates (all run after the change)**

| Gate | Before | After |
|---|---|---|
| root `bun turbo typecheck` | 30/30 | **30/30** |
| app unit `./src` | 755 / 1 fail | **765 / 0** |
| `src/i18n` parity | 12 / 1 fail | **13 / 0** |
| `e2e/performance/unit` | 43 / 0 | **43 / 0** |
| oxlint `packages/app/src` | 822 warn / 0 err | **822 warn / 0 err** |
| `vite build` | ok | ok (`session.thinking.elapsed` in the bundle) |
| prettier `--check` (touched files) | 1 violation in `message-timeline.tsx` | clean |

**Env finding (worth keeping):** there is **no `node` binary on this machine**, so `bun run lint` fails at
`/usr/bin/env: node`. A throwaway shim `/tmp/opencode/nodeshim/node` → `exec ~/.bun/bin/bun "$@"` makes
oxlint's type-aware pass (which spawns `oxlint-tsgolint`) work. Not written into the repo on purpose.

**Committed `5d6b47a` + pushed to `origin/dev`** (pre-push `bun turbo typecheck` 30/30 FULL TURBO,
`c1f1b58..5d6b47a`). Staged alone: only `timeline/turn-activity*.ts`, `timeline/message-timeline.tsx` and
`i18n/` — s071's `AGENTS.md` / `README.md` / `titlebar.tsx` were verified still unstaged afterwards. The commit
carries both parts (FE-021 and the FU-076 RSS keys) because they touch the same 62 files; the body says so.

**Deployed 07:28 UTC by the user** (the hold was their call, not a blocker): build **`1.1.20260927072837`**,
server **pid 3654762** (was 3613950), bundle `assets/index-BFF1n-Mg.js`. Probed and **confirmed live** —
`session.thinking.elapsed`, `since the last model output` and the RSS key are all in the served bundle and in the
binary; `/api/health` healthy; FE-001 auth intact (unauth `/` → 401, `/login` → 200). The fork `AGENTS.md`
"Last deploy" paragraph was rewritten at the same time (it still named the old pid and still called FE-021
uncommitted WIP — drift) and now records the two durable lessons: a build ships whatever is in the tree, and a
deploy kills the session host, so use `--detach`. **Remaining: the user's visual check** (FU-085).

**Drift corrected (AGENTS.md drift check).** s071 recorded that the deployed binary ships this WIP. Measured
against the binary and the served bundle: `session-turn-thinking-elapsed` present, `session.thinking.elapsed` /
`since the last model output` **absent** (the 06:53 UTC build predates these edits). Corrected in
`10-status/current-state.md` and `50-projects/p003-opencode-fork/README.md`.

**Also closed:** FU-076 (i18n parity) — the 6 RSS keys existed only in `en.ts` + `tk.ts`; added to the other
60 locales with the English source copy (FU-026 pattern, no invented translations).

**Recorded:** DEC-047 (why the observation is client-side + the three traps), FU-085 (deploy + live verify),
p003 `README.md` → `## FE-021`.

**Concurrency note.** A parallel session (**s071**, DEV-menu utility items) was editing the same fork checkout
and the same log files during this session. It renamed itself s070 → s071 to avoid colliding with this session
number, rotated `command-log.md`, and added FU-081..084. Nothing of s071's was modified here; `titlebar.tsx`,
fork `AGENTS.md` and fork `README.md` are **its** uncommitted WIP, so a future commit must stage FE-021 alone.

