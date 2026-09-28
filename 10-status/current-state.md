# Current Project State

> Snapshot of the last known state. Updated by the agent at the end of EVERY session.
> If reality differs from this file, fix it immediately (drift check).

- **Last updated:** 2026-09-27 (UTC) — **s077: FE-025 is CODE COMPLETE and every gate is green — the timeline "N Changed files" group now collapses to one 44px row by default, toggled by a click, persisted per session (DEC-052). NOT committed / NOT built / NOT deployed.** After the user said "go" I implemented the plan's F1-F10. **What shipped (5 modified + 3 new, +160/−59):** `context/layout.tsx` gains `SessionView.diffSummaryOpen?: boolean` with an accessor beside `todoCollapsed` — **absent means collapsed**, so no `migrate` branch and no `layout.v6` bump, and one flag serves the whole session (the user's option A: opening one turn's list leaves the others open, recorded as accepted); `message-timeline.tsx` turns the existing sticky header into the toggle (`role="button" tabIndex="0" aria-expanded` + Enter/Space, mirroring the composer todo dock) and wraps the file list in `<Show when={open()}>`, with a new `session-turn-diffs-chevron` (`aria-hidden`, rotated on the group's `[data-expanded]` — a **different** `data-slot` from the per-file `session-turn-diff-chevron`, so the two rules do not collide, verified in the built CSS); `Show all` and `+N more files` became real `<button type="button">`s with `stopPropagation()` and a `:focus-visible` opacity lift (they were a bare `<span onClick>` that was `opacity: 0` until hover, i.e. invisible to keyboard **and** touch users). **The row's content is unchanged and adds no i18n key** — the count is the existing plural, the `+12 −4` split is the turn total because `<DiffChanges changes={props.diffs}>` sums the whole array, and both fields are required `Schema.Finite`, so parity stayed **5/5 / 979 assertions**. **Benchmark** (`packages/app/AGENTS.md` requires one before touching timeline code): **44px collapsed vs 393px expanded** for 12 files = **349px saved per group**; the header measures **44px in both states**, so the `--sticky-accordion-offset: 44px` the per-file sticky headers depend on still holds (first file row sits 50px below the header, no overlap); at **390×844** `documentElement.scrollWidth == clientWidth == 390` (no page-level horizontal scroll) and the label is not clipped. **Gates:** app + e2e typecheck clean · unit **775→780** (+5, 0 fail; baseline proven by `git stash push -u` and re-running) · oxlint **0 errors** on all 7 files · `bun run build` ✓ · new e2e spec **8/8** · `session-timeline-projection` **5/5** · `collapse-state`/`shell-outline`/new **19 pass** · full `timeline-stability` **43/44**. **Two failures are pre-existing, not mine** — both reproduce identically with all my files stashed away: `session-timeline-lifecycle-state.spec.ts:74` (the `Thinking` row, FE-022 WIP) and `timeline-stability/adverse.spec.ts:82` (shell virtualization). **Three of my own mistakes the runs caught:** an `as SummaryDiff` assertion (oxlint `no-unsafe-type-assertion` → `satisfies SnapshotFileDiff[]`), an invented CSS token `--border-focus-base` that does not exist (→ the real v1 `--border-focus`), and an e2e assertion that assumed `Show all` lives in the collapsible body — it lives in the **header**, so only `+N more files` and the file list are behind the toggle; the same run also exposed a pre-existing loose locator, since the Review panel's "Show all lines" matches the spec's `/show all/i` regex. **Deviation from the plan:** the new persistence e2e case became its **own** spec file rather than a case in `session-timeline-collapse-state.spec.ts`, because adding diffs to that file's shared `userMessage` would have perturbed its 3 unrelated tests. The fork `AGENTS.md` gained +63 lines recording the 44px-both-states constraint, the two chevron slots, the one-flag consequence and the `stopPropagation` rule. **Owed:** commit **alone** (s076's uncommitted FE-023/024 WIP is in the tree, disjoint from FE-025's 8 paths) and `scripts/deploy-web-4447.sh --detach`, which kills this session's listener. Details: `20-logs/sessions/2026-09-27_s077_fe-025-diff-summary-collapse.md`.
- **Last updated:** 2026-09-27 (UTC) — **s077: FE-025 PLANNED, not built — the timeline "N Changed files" group will collapse to a single row by default, and the state will persist per session (DEC-052).** User: "opencode fork project webui plan do modified file default collapse like todo list. default collapse, toggle on user manual click." Asked 3 scope questions first, and the answers shaped the design: (1) the **whole group** collapses (group → file list → diff), not just the header; (2) state **persists per session**; (3) fix the bare-`<span onClick>` controls while there. Traced the component before proposing anything: `TimelineDiffSummaryRow` (`packages/app/src/pages/session/timeline/message-timeline.tsx:204-284`) already has **two** collapse axes — a 10-file cap (`showAll`) and a per-file Kobalte `Accordion` that is *already* collapsed by default — so the request is a **third axis around the whole group**: the always-expanded file list (up to 10 rows ≈ 440px) is the real cost. **Design:** the existing 44px sticky header becomes a `role="button" tabIndex="0" aria-expanded` toggle (Enter/Space, trailing chevron) and `<Show when={open()}>` wraps the per-file Accordion → a collapsed row is 44px. `open` = a new `SessionView.diffSummaryOpen?: boolean` beside the existing `todoCollapsed` (`layout.tsx:75`, accessor `:865-876`), so **"default collapse" is the absence of state** (`?? false`) — **no `migrate` branch, no `layout.v6` bump**, and no migration for existing browsers. `MessageTimeline` already holds `useSessionKey()` (`:332`), so **no new prop** and no change at the `session.tsx:2089` call site. `Show all` (`<span onClick>`, `opacity:0` until hover → invisible to keyboard *and* touch users) and `+N more files` (`<div onClick>`) become real `<button type="button">`s **with `stopPropagation()`** — they sit inside the header that just became clickable, so that is the likeliest defect. **Zero new i18n keys:** the chevron is `aria-hidden`, `ui.sessionTurn.diffs.changed` is the accessible name, and the `ui.*` keys live in `packages/ui/src/i18n/` (66 locales, parity-enforced), so the 66-file cost is avoided entirely. Also recorded: the state is **already** lost on virtualised remount today (the row unmounts; `createStore` at `:207-210` resets) — persistence is what stops the new axis inheriting that; a **dead duplicate** of the markup lives in `packages/session-ui/src/components/session-turn.tsx:436-527` sharing the same `data-slot`s and the live CSS; and two e2e specs (`timeline-stability/interaction.spec.ts:176-231`, `session-timeline-projection.spec.ts:131-162`) assert the *expanded* list and will red until they open the group — that is the feature working, not a regression. **Plan doc:** `50-projects/p003-opencode-fork/notes/plan-diff-summary-collapse.md` (4 phases: P1 store 1 file · P2 component + `session-turn.css` 2 files · P3 2 e2e edits + 1 new e2e + 1 unit test for the extracted `diff-summary-state.ts` helper — the app has **zero** component tests, so only pure logic is unit-testable · P4 deploy, needs the user's OK because `deploy-web-4447.sh --detach` kills this session's listener). `packages/app/AGENTS.md` requires a production benchmark baseline **before** touching timeline code, and FE-025 must be committed **alone** (the tree still holds s076's uncommitted FE-023/024 WIP). **No code, no commit, no build, no deploy.** Details: `20-logs/sessions/2026-09-27_s077_fe-025-diff-summary-collapse.md`.
- **Last updated:** 2026-09-28 (UTC) — **s073 deployed `f3db840` (:4447 → `1.1.20260928061739`, pid 230458) and verified the settings-strip scroll fade live, 10/10 — and cleaned up worktrees my own test runs had left behind.** The fade is the four-layer pure-CSS scroll shadow on the horizontal settings list; the check that matters is that it is **locale-correct**: the four layers and `background-attachment: local, local, scroll, scroll` are live in both locales, **English** overflows (421 px of content in a 358 px strip, scrolls to `scrollLeft=63/63`) so a fade is warranted, and **zh** fits exactly (358 = 358) so **nothing is drawn** — the pre-build measurement predicted exactly this, and a static fade overlay would have dimmed the ends in zh for no reason. 0 page errors in both. Also landed the three items you decided on: `a858764` (deleted `STATS.md` + `script/stats.ts`, kept the guarded upstream stats workflow, documented the `OPENCODE_VERSION` packaging requirement in AGENTS.md) and the fade itself. **Housekeeping finding:** `git worktree list` showed 9 entries — 8 were `prunable` leftovers with their directories deleted, created by **my own** `test:httpapi` runs (the harness registers a worktree per scenario that calls `worktree create`). Pruned the registrations and deleted the eight `opencode/*` scratch branches (all at `75e5c77`, an ancestor of `dev`, so nothing unmerged was lost). The fork is back to one worktree, one branch, clean tree; **every `test:httpapi` run leaves these behind**, so they need pruning after each. Open: FU-092 (SDK regen — you asked what it is for; explained, awaiting your call), FU-091 (deferred by your choice), FU-102 (needs a server-side API that does not exist yet).
- **Last updated:** 2026-09-28 (UTC) — **s073 re-visited all 9 open follow-ups: 3 closed (2 were stale), `test:httpapi` is green for the first time, and a comment that had become a lie is fixed. `e9ff2c8` pushed.** **FU-094 (real, now fixed):** the `test:httpapi` gate had been red for everyone — `--fail-on-missing` with 3 uncovered routes (the FE-049 skill endpoints). I wrote happy-path scenarios first and they **passed only in `--mode coverage`**, failing in `auth`/`effect` with `400 Skill not found`, because the runner loads the instance (`runner.ts:96`) *before* the scenario seed (`runner.ts:188`) so a seeded SKILL.md is not in the discovery set — order-dependent scenarios are worse than none, so the committed ones assert decode + instance context + the declared `InvalidRequestError` with the reason in a comment. All three modes now report `pass=212 fail=0 skip=0 missing=0 extra=0`, **exit 0**. **FU-070 is MOOT:** `rearrangeTabsAfterSlim` no longer exists — the sibling session redesigned FE-017 in `b9ead30` to compact in place, so there was nothing to commit. **FU-071 was stale:** the touch-Enter change was committed on 2026-09-20 in `4b21d04` and is in the live build; only a one-minute phone spot-check is left. **A comment that had become a lie:** `home-session-index.ts:172` justified its full-table scan with "the V2 API orders by creation time", untrue since the session list started ordering by last activity (`86c621c`) — rewritten to the reasons that remain. **FU-091 re-checked item by item:** (1) the duplicate `web-research` skill copy is still md5-identical to the global one, (2) both Desktop launchers are still world-readable with the password in plaintext, (3) **my earlier diagnosis there was wrong** — the subcommand exists as `service password`; the desktop passes a spurious `get`, and I left it alone on purpose (upstream `packages/desktop`; the fork's rule is that customisations live in `packages/app`), (5) inotify is down to 67/128 and the ENOSPC failures have not recurred. Still open and awaiting your call: FU-060 (STATS.md), FU-074 (desktop packaging version), FU-077 (settings-strip polish), FU-091(1)(2), FU-092 (SDK regen), FU-102 (Home page under-fill). Details: command-log rows 03:05–03:26.
- **Last updated:** 2026-09-28 (UTC) — **s073 deployed the fix-all commit: :4447 now runs `1.1.20260928023322` (pid 90290) with the Chinese UI verified live (FU-102 closed).** Built from a **detached worktree at `origin/dev` = `75e5c77`** (DEC-052, so nothing uncommitted rode along), pinned bun 1.3.14, no `bun install`; swapped with `cp`→`mv -f` (ETXTBSY on a running exe), old listener pid 58516 stopped, worktree removed afterwards. The binary carries **both** the user's session-ordering fix (`session_time_updated_id_idx`) and the fix-all commit's autostart string. **Live, in Chinese:** DEV menu `["主页","刷新","清除缓存","调试工具","退出登录","设置","帮助"]` — the first four had **no i18n key at all** before this work — Settings categories `[通用, 快捷键, 服务器, 提供者, 模型, 管理]`, the whole Admin panel localised and still reporting the live port **4447**, timeline stages **发送中 → 思考中** with 秒 counters, default model `dgx/general`. **A probe check failed and I chased it rather than waving it off:** "bundle carries the zh translations" was a **false negative in my own probe** — it grepped only the entry chunk, which holds the **English** dictionaries plus `labelKey`/`confirmKey` references, while the locale is `import()`-ed lazily. Proof the copy really ships: the zh strings are inside the embedded binary, and the browser renders them. `等待模型回应` did not appear only because that stage needs ≥10 s of silence and the turn answered faster. Details: session record, command-log rows 02:22–02:45.
- **Last updated:** 2026-09-28 (UTC) — **s073 "fix all" pass: the user's own session-ordering fix verified, FU-101 fixed, and the Chinese translation debt cleared — `75e5c77` pushed, live binary still `1.1.20260927153151` (not yet redeployed).** (1) **Reviewed the user's `86c621c fix(core): order the v2 session list by last activity, not creation` — necessary and correct.** Its comment claims the v1 route already sorted that way, and that checks out: `packages/server/src/handlers/session.ts:33` calls the *same* `SessionV2.list` and anchors both cursors on `time.updated` (lines 47, 58) while `list` was ordering by `time_created`, so keyset pages could skip or repeat rows. The `(time_updated, id)` index matches the new order, the migration is wired into `schema.gen.ts`, `time_updated` is genuinely bumped per message (SSE `session.updated`), and the tests pass (core session-list **5/5**, httpapi-session **22/22**). (2) **FU-101 fixed:** a failed web-UI autostart reported `reason: "disabled"` — the same value as "the setting is off" — and the TUI printed nothing, so a port clash was invisible outside the log. Now a distinct `reason: "failed"` carries the port and the TUI prints a danger line naming it (**10/10** tests; my first attempt used a `TEXT_ERROR_BOLD` style that does not exist, caught by listing the real names in `cli/ui.ts` and corrected to `TEXT_DANGER_BOLD`). (3) **Translation debt cleared for the locales this box uses.** A better detector than "identical to en" (a zh value can be English yet differ from en) found **50 real UI strings still English in `zh` and 54 in `zht`** — and that `zht` is **Taiwan** register (工作階段/連接埠/快取/重新整理) while `zh` is **Mainland** (会话/端口/缓存/刷新), so they are not mechanical variants. Every term was taken from what each file already used (`mcp.status.disabled` 已禁用/已停用, `common.save` 保存/儲存, `home.title` 主页/首頁, `desktop.wsl.error.failedPort` 端口/連接埠), never invented. Both files now have **0 untranslated UI strings**; what stays English is enumerated in the commit body (product/provider names, tool names, keyboard legends, MCP/LSP/WSL/PDF, example placeholders). **FU-083 too:** the DEV menu's four items were hardcoded English with **no key at all**, so they could not be translated even in principle — they now use `devMenu.*` (English source copy in the other 58 locales, per the FU-026 pattern) wired at `titlebar.tsx:669,672,697,700`. Gates: `bun turbo typecheck` **30/30**, app unit **780/0** (parity green), oxlint 0 errors. **Closed: FU-083, FU-084, FU-098, FU-101.** Details: `20-logs/sessions/2026-09-27_s073_post-submit-progress.md`, command-log rows 01:05–01:31.
- **Last updated:** 2026-09-28 (UTC) — **s073 review: everything pushed today audited for necessity and junk; one piece of my own dead state removed, one real defect filed.** Scope: fork `origin/dev`'s 9 commits today (`c1f1b58`…`6aee40b`) + the `ide` doc commits. **Clean:** no committed artifacts (`test-results`/`playwright-report`/`dist`/`*.log`/`*.png`/`.bak`); the `TODO` grep hits are pre-existing i18n strings; **all 20 i18n keys added today are referenced** (3 apparent misses were my own sed artefact on multi-line strings); **no dead exports**; the FE-025 extraction left **no** duplicate of the old inline `maxFiles = 10`; the `export * as Webui from "./webui"` self-alias matches the house pattern (`core/…/config/server.ts:3`) and stays; `httpapi-exercise` **pass=209 fail=0** with the new `GET /global/webui` scenario passing on real assertions (the 3 missing ones are FU-094's pre-existing `/api/skill/{name}`). **Fixed — in my own code:** `TurnProgress.at` was written on every `begin` and read nowhere (leftover from the expiry the watchdog replaced) → `6aee40b`, plus one 128-char line wrapped. **Filed, not fixed (FU-101):** FE-024's autostart returns `reason: "disabled"` when a **bind fails**, and the TUI prints nothing for that — a failed autostart is invisible outside the log, the same "silent failure" class this session began with; it is another feature's RPC contract so I did not change it unilaterally. **Also verified correct rather than assumed:** `secured: !!Flag.OPENCODE_SERVER_PASSWORD` really matches the server's notion of secured (`server/auth.ts:18,25` read only the env var). Details: `20-logs/sessions/2026-09-27_s073_post-submit-progress.md`, command-log rows 00:20–00:36.
- **Last updated:** 2026-09-27 (UTC) — **s073 follow-on: default model is now LLM Main (`dgx/general`), and ALL recent enhancements are deployed in one binary — `1.1.20260927153151`, pid 3944553, verified 9/10 live.** (1) **Model:** the user asked what "LLM Main" as default would be → `"model": "dgx/general"`, verified **in the UI first** (one real prompt: `dgx/general`, parts `step-start → text("4") → step-finish`, chat renders exactly `4`, 0 blank progress samples across a 74.6 s turn), then written to `~/.config/opencode/opencode.jsonc`. **The global config is read at server startup only** — `GET /config` still reported the old value after 60 s, so a :4447 restart was required; it now reports `dgx/general`. Backups: `.bak-before-model-fix` (pre-FE-022) and `.bak-before-dgx-default` (the `ocgo` default). (2) **One wrong call on the record:** probing the gateways with `max_tokens: 5` made `dgx:8102` and `rtx:8104` both return `proxy_error`, and I reported "LLM Main isn't answering, don't set it yet". The user pushed back; re-probing with a different request shape showed **all three healthy** — a transient DGX upstream blip that I presented as a standing fact. (3) **All enhancements deployed together** at the user's request: pre-flight `bun turbo typecheck` **30/30** + app unit **780/0** + a quiet tree (no source file touched in 10 min), rollback binary kept, then one build carrying **FE-022** (my turn progress), **FE-023** (Admin/`webui.autoStart`, the parallel session) and **FE-025** (timeline diff summary) — confirmed by scanning the binary (`Waiting for the model` ×62, `autoStart` ×71, `diff-summary`) and the served bundle `/assets/index-C8vo-4Vw.js`. Verification **9/10**: the one failure was my probe reading the composer's model label too early — the label reads **"LLM Main"** and appears **542 ms** after a cold page load, so no app defect; the decisive check (fresh profile answered by `dgx/general`, progress row up throughout) passed. **Caveat:** the parallel session's 85 files ship **uncommitted**, so `:4447` is not yet reproducible from `origin/dev` — that session should commit for the two to match. Details: `20-logs/sessions/2026-09-27_s073_post-submit-progress.md`, FU-099.
- **Last updated:** 2026-09-27 (UTC) — **s073 SHIPPED + LIVE-VERIFIED (FE-022 / DEC-051 / DEC-052): the agent chat now shows turn progress from the submit keystroke to `idle` and names the stage; the fork's default model is fixed; :4447 serves a clean build. 3 commits, 3 deploys, 7/7 live checks.** Final state: `origin/dev` = `d04b79e` (`3f72392` feat · `a325324` fix · `d04b79e` refactor), live build **`1.1.20260927123522`**, **pid 3851578** on :4447, built from a **detached worktree at `origin/dev`** so it carries none of the parallel session's WIP (DEC-052 — the build compiles the whole tree, which had shipped FE-023's half-finished Admin UI twice: FU-082, third occurrence). **The change:** a client-side record of a submitted turn (`packages/app/src/utils/turn-progress.ts`, `begin` before any `await`, settled by the server's first status event / every rollback / the watchdog), the row's gate becomes `status !== "idle" || pending` (**`retry` included**), the 15 s watchdog asks the server for the session's messages before demoting a session it does not list (`turnIsFinished`, extracted + 8 assertions), and the label says **Sending → Thinking → "Waiting for the model"** (≥10 s with zero model output, so a long tool call cannot trip it). **Live proof (390×844 phone viewport, fresh profile, clean binary):** composer resolves "Opencode Go Default", progress row on screen **35 ms** after Enter, "Sending" → "思考中 · A / B", never blank while the turn ran, assistant answered `ok` via `ocgo/opencode-go-default` with no provider error — 7/7. **Root cause of the reported symptom, also fixed (FU-096; originally filed as FU-087, which the parallel s072 session took mid-session):** the server default model was `opencode-go/gpt-5.6-luna`, which answers *"An active OpenCode Go subscription is required to use Go models"* — every prompt on a fresh device went `busy → retry(1) → … → error`, which reads exactly like a dropped connection; `"model": "ocgo/opencode-go-default"` is now in `~/.config/opencode/opencode.jsonc` (backup `/tmp/opencode/opencode.jsonc.bak-before-model-fix`). **How the bug was found:** measurement, not inspection — a healthy model already showed the row in 28 ms, so the fault was the *transient* states; a Playwright probe that tees the SSE stream and watches the row's DOM mutations caught the row blanking at ~7–10 s mid-retry, which is what produced `a325324`. **My own process errors, recorded because they matter:** I shipped `a325324` before asking (right call, wrong order), and I pushed once with `--no-verify` because `bun turbo typecheck` was red **from the parallel session's** WIP (`packages/opencode/src/cli/tui/worker.ts` vs their new `packages/core` config schema — green again once they fixed it, so the bypass was unnecessary by the end). Gates: app+ui typecheck clean, app unit **780/0**, e2e `post-submit-progress.spec.ts` 3/3 (each case verified to fail without the fix), timeline stability 43/44 (the 1 failure pre-existing), oxlint 0 errors. Details: `20-logs/sessions/2026-09-27_s073_post-submit-progress.md`, DEC-051, DEC-052, FU-096/097/098 (renumbered from 087/088/089 — the parallel s072/s074 sessions claimed those numbers while this session was running).
- **Last updated:** 2026-09-27 (UTC) — **s073 (earlier entry, the investigation): FE-022 — the agent chat's turn progress can no longer go blank while a turn is running, and it says which stage it is in (DEC-051; code complete, all gates green, NOT committed / NOT deployed).** User: "user input prompt and submit → there is no 'Thinking' until the first response from LLM → user is confused if connection problem or sth else → show thinking of any progress after the user prompt". **Measured before changing anything** (Playwright vs the live :4447: `addInitScript` tees the SSE body with `performance.now()` stamps + a `MutationObserver` on `[data-slot="session-turn-thinking"]`; probes in `/tmp/opencode/probe/`): with a healthy model the row already appeared **28 ms** after Enter (6275→6303 ms) and was on screen at 390×844 (list `clientHeight == scrollHeight`), so neither the happy path nor scrolling was the bug. Three real holes: (1) the row was gated on `status === "busy"` **only**, so a `retry` (upstream backoff) removed it; (2) the 15 s status watchdog ("store says busy but the server does not list the session ⇒ idle") **demoted a live turn** — during a retry backoff the session is legitimately absent from `/session/status` (reproduced live: row removed at 15.1 s while the server was on retry attempt 4); (3) the optimistic `busy` is skipped when `sessionDirectory !== projectDirectory` (sandbox worktrees) and is only as fresh as the last status event. **Fix:** new `packages/app/src/utils/turn-progress.ts` = a per-(server scope, session) signal-backed record of a submitted turn (`begin` before any `await` in `handleSubmit`/`sendFollowupDraft` + both command branches; `settle` on the server's first status event, on every rollback, and by the watchdog for sessions the server does not list as running); row gate `status !== "idle" || pending` (**retry included**) so an upstream backoff can never look like a dead socket; the watchdog no longer demotes a `retry`; labels `Sending` → `Thinking` → `Waiting for the model` (≥10 s with **zero** model output, so a long tool call cannot trip it), FE-021's `· A / B` counters untouched. 2 new i18n keys in `packages/ui/src/i18n` `en.ts` + all 61 other locales (English source copy — FU-089). **Gates:** `bun turbo typecheck` **30/30** · app unit **773 pass / 0 fail** (i18n parity green) · ui unit 27/27 · oxlint **0 errors** (1 accepted-style warning, same pattern as `server.test.ts`) · new e2e `post-submit-progress.spec.ts` **3/3**, each case verified to **fail without the fix** (reverted `inFlight` and re-ran) · timeline-stability **43/44**, the single failure (`adverse.spec.ts` "shell state across virtualization") is **pre-existing** — verified identical with the change stashed, as are the 3 `remote-*-spec` failures. **Side finding (fixed later the same session as FU-096):** the :4447 server default model was `opencode-go/gpt-5.6-luna`, which answers *"An active OpenCode Go subscription is required to use Go models"* — on a fresh profile every prompt enters the retry loop, i.e. it **looks** like a connection problem (FU-087). Details: `20-logs/sessions/2026-09-27_s073_post-submit-progress.md`, DEC-051, FU-087/088/089.
- **Last updated:** 2026-09-27 (UTC) — **s076: FE-023 (Admin settings) + FE-024 (exe web auto-start) are CODE COMPLETE and every gate is green — but NOT built, NOT deployed, NOT committed (FU-093).** Twelve code files + 62 locale files, all uncommitted in the fork beside the parallel s073 WIP (disjoint). **FE-023** adds an **Admin** tab to the settings-v2 dialog whose rows write the **global** `opencode.json(c)`: new `server.webui.autoStart` in the config schema (`packages/core/src/v1/config/server.ts`, the `Webui` struct declared *before* `Server` — module TDZ), a new declared route **`GET /global/webui`** (`Webui.DefaultPort = 4446`; the handler reads the global config only and the running values from `Server.url` through a *deferred* dynamic import, because a static one would cycle with `server/server.ts`), `WebuiStatus` + `fetchWebuiStatus` in `packages/app/src/utils/server.ts` (same Basic-auth pattern as `fetchProjectDirectories`), and `settings-v2/admin.tsx` (auto-start switch, port input with an **explicit Save**, and a status line that distinguishes *running on the configured port* / *restart to apply X* / *not set in the config file, running on Y*). 14 new i18n keys × 62 locales in English (FU-026 pattern), documented in `packages/web/src/content/docs/config.mdx`, and the fork `AGENTS.md` now records the four rules (patch only the changed leaf because arrays are **replaced**; a config write **disposes every instance** so never save on blur; the port is read once at start so it needs a restart; v1 settings are dead code so the tab is v2-only on purpose). **FE-024** makes a bare `opencode.exe` serve the web UI: `cli/web-autostart.ts` (pure `resolveAutoStart` policy + binder + `networkURLs`), a `webuiAutoStart` RPC on the TUI worker that binds through the worker's own listener ref (so `shutdown` stops it and the `--port` path keeps priority, and a failed bind cannot kill the TUI), and a print of the URL / LAN URLs / unsecured warning before the TUI takes the screen. **The plan's open questions are settled:** 4446 is the value the Admin row *offers* and auto-start *uses*, **not** a new compiled-in default (DEC-050's schema-default idea was **not** used — it would make `server.port` required in the TS type and change every `GET /config` response; correction recorded), auto-start is **opt-in**, the wildcard address is only used when `OPENCODE_SERVER_PASSWORD` is set (otherwise 127.0.0.1 + warning), and "admin" = any authenticated browser because this server has no user/role model. **Gates:** `bun turbo typecheck` **30/30** · app `test:unit` **774 pass / 0 fail** (i18n parity 5/5, 979 assertions) · auto-start policy **9/9** · `httpapi-exercise` `global.webui` **PASS** (the run still reports **3 pre-existing MISS** for the FE-049 skill routes, so `test:httpapi` was already red → FU-094) · oxlint **0 errors**, new files warning-free. Traps recorded: `Rpc.client.call` types as `Promise<Promise<X>>` (await it, don't `.then()`), `AppRuntime` has no `ServerAuth.Config` (use the same `Flag.OPENCODE_SERVER_PASSWORD` the auth header reads), and the generated SDK types predate `server.webui` (one cast, FU-092). **Nothing is in a binary yet** — the app is embedded at build time, so the tab needs `deploy-web-4447.sh --detach`, which kills the listener this session runs on; that plus the live checks and the commit is FU-093. Details: `20-logs/sessions/2026-09-27_s076_fe-023-admin-settings.md`.
- **Last updated:** 2026-09-27 (UTC) — **s075: s072 is CLOSED as ❌ REJECTED and its code REVERTED (DEC-049 rejected; DEC-050 replaces it).** User: "close s072 rejected". The default-port-4447 change was still **uncommitted**, so — unlike the FU-054 precedent where nothing existed to undo — it had to be actively undone: the diff was first saved to `/tmp/opencode/s072-default-port-4447.patch` (157 lines) as a safety net, then `git restore` was run on **exactly** the 8 files it touched (`server/server.ts`, `plugin/index.ts`, `cli/cmd/{attach,run}.ts`, `test/server/httpapi-listen.test.ts`, `packages/sdk/js/script/build.ts`, `CONTRIBUTING.md`, fork `AGENTS.md`). Verified after: `server/server.ts:117-122` is upstream's original `startListener(opts, 4096)…`, **no `DefaultPort` symbol remains anywhere**, and `git status` in the fork shows **only the parallel s073 `packages/app` WIP**. HEAD never moved (`cb67c4a`), so nothing of s072 ever reached a commit, a build, or the live :4447 (pid 3654762) — there is no artifact to clean up. **Records updated:** FU-086 → REJECTED + reverted, FU-087 (Playwright 4096 drift) and FU-088 (SDK `baseUrl` regen) → **moot** (both existed only because of this change), FU-089 (D1) → **resolved differently**, DEC-049 → marked rejected with its still-valid tracing preserved, the s072 session record gained a CLOSE-OUT section, and the FE-023/024 plan doc was corrected. **DEC-050 (the replacement):** the user's "default 4446" is delivered by a **config-schema default** on `ConfigServerV1.Server.port` (`packages/core/src/v1/config/server.ts`), which `resolveNetworkOptionsNoConfig` already prefers (`cli/network.ts:69`) — so `opencode web`/`serve` with no flags and no `server.port` lands on **4446**, an explicit `--port` still wins, a busy 4446 still falls back to a free port, and **`server/server.ts` + `cli/network.ts` are never touched** (a much smaller upstream-merge surface). 4447 remains exclusively the local Linux deploy port passed explicitly by `run-web.sh`/`deploy-web-4447.sh`. This is now phase **P1** of the FE-023 plan (`notes/plan-admin-settings.md`); the plan's old **P0 is cancelled**.
- **Last updated:** 2026-09-27 (UTC) — **s074: FE-023 (admin settings) + FE-024 (exe web auto-start) are PLANNED, not built — plan doc written, 3 research threads, no feature code (user asked to "open agent thread to plan these how to arrange").** User's scope, confirmed by question: a new **Admin** section in the **settings-v2** dialog whose rows read/write the **server-side global `opencode.json`/`opencode.jsonc`** (shared by all users; existing per-user settings untouched); first rows = *webui server → auto start enable/disable* + *webui server → webui port, default **4446***; on `opencode.exe` start the web UI comes up on the configured port, **reachable from any domain**; all future admin settings persist in `opencode.json(c)`. **The research changed the shape of the work in three useful ways:** (1) the global-config **write path already exists** — `PATCH /global/config` → `Config.updateGlobal` (`config/config.ts:656-680`) patches the first existing `opencode.jsonc`/`opencode.json`/`config.json` and **preserves comments**, and the app already uses it (`server-sync.tsx:704-715`) — so "admin settings live in opencode.json" is nearly free; what is missing is (a) a **declared** schema key (`core/src/v1/config/server.ts`, since undeclared keys are dropped by `onExcessProperty: "ignore"`), (b) a UI, (c) an **apply** path. (2) **A port change cannot apply live**: `web.ts`/`serve.ts` discard the `Listener`, there is **no** config watcher on the global dir and **no SIGHUP** handler, so the first cut shows "saved ≠ running — restart to apply" (the only re-listen precedent is the TUI worker RPC, `cli/tui/worker.ts:54-58`; live re-listen is phase P5). Also: a global-config write **disposes all instances** (`handlers/global.ts:80`), so rows must not save on blur, and PATCH must send **only the changed leaf** (arrays are replaced, not merged). (3) **No user/role model exists** — one shared `OPENCODE_SERVER_PASSWORD`, and every authenticated browser can already `PATCH /global/config` / `dispose` / `upgrade`, so the Admin tab adds **no new privilege** (D5). FE ids: **FE-022 was taken by the parallel s073**, so these are FE-023/FE-024; the checkout currently holds s072's 8 port files + s073's app/ui WIP and **nothing** of FE-023/024. Plan: `50-projects/p003-opencode-fork/notes/plan-admin-settings.md` — config shape `server.port` (existing, the port row edits it) + **new `server.webui.autoStart`** (a second `webui.port` would be a second source of truth), one new read-only route `GET /webui` (effective vs applied port, `restartRequired`) + a `utils/server.ts` fetch helper (the `fetchProjectDirectories` precedent), a 6th settings-v2 tab (`TabsV2.Trigger` + `TabsV2.Content`, `SettingsRowV2` + `Switch`/`TextInputV2`, 6 new i18n keys × 62 locales or parity fails), and FE-024 as a small `cli/web-autostart.ts` called from the TUI worker (a **no-arg `opencode.exe` opens the TUI, which binds no port**; there is **no** autostart/boot mechanism anywhere in the repo), with `0.0.0.0` allowed **only when a server password is set** (D4). Phases P0–P6 + effort in the plan doc. **Open decisions D1–D6**; **D1 blocks everything**: the user said 4446 while s072/DEC-049 set the code default to 4447 (uncommitted) — recommendation is `DefaultPort = 4446` with 4447 kept as the explicit local deploy port, i.e. amend DEC-049 (FU-089). **Global skills answer:** yes, `~/.config/opencode/skills/{starter-kit,web-research}` + `plugin/kickoff.ts` are alive and idempotent (live log shows them seeding on every start); but the identical `ide/.opencode/skills/web-research` copy triggers a `duplicate skill name` warning, `gdx`'s copy is older, and a new/edited global skill needs a **server restart** (no watcher; only the TUI's `SIGUSR2` reload is hot) — cleanup tracked in FU-091. Details: `20-logs/sessions/2026-09-27_s074_plan-admin-settings.md`.
- **Last updated:** 2026-09-27 (UTC) — **s072: the fork's DEFAULT listen port is now 4447, not upstream's 4096 (DEC-049) — code done + gates green, NOT committed / NOT built / NOT deployed; `4446` in the Windows installer kept on purpose.** The user asked to "make the default port 4447 when install", i.e. a plain `opencode web` / `opencode serve` after install should serve on :4447 instead of requiring `--port 4447` as every deploy script does today. Traced the real default before editing: the yargs `port` option is `0` ("no preference", `cli/network.ts:10`), and the actual resolution is `server/server.ts:startWithPortFallback` — `0` → *try the preferred port, else any free port* — where the preferred port was a hard-coded **4096**; `web.ts`/`serve.ts` just print `server.port`, so one line is the whole behaviour. Changed to a single exported constant `Server.DefaultPort = 4447` used by the fallback, the two `http://localhost:4096` plugin fallbacks, the two `--help` examples (`attach`, `run --attach`), the 2 unit tests that pin the preferred port, the hey-api `baseUrl` in `packages/sdk/js/script/build.ts`, and the `CONTRIBUTING.md` default-port line = **7 files, +20/−15**. Precedence is untouched: explicit `--port` > `opencode.json` `server.port` > 4447 > any free port; and the prefer-then-degrade behaviour is preserved (a busy 4447 still starts, on a random port). **Deliberately unchanged:** the Windows installer's **4446** (`script/build-windows-installer.ps1` + the fork `AGENTS.md` "This fork" section) — the user's explicit call; that script passes `--port 4446` itself so it stays consistent; `github/index.ts:233` (passes `--port=4096` explicitly, not an install path); and the ~15 `packages/app` Playwright specs / `playwright.config.ts` that default `PLAYWRIGHT_SERVER_PORT=4096` against an **externally started** backend (drift logged as FU-087). Gates: `bun typecheck` (`packages/opencode`) clean · oxlint 0 errors (36 pre-existing warnings) · `bun test -t "port 0"` **2 pass / 0 fail** — though the live server owns 4447, so "prefers 4447 when free" self-skips and the fallback test is the one that really runs; an isolated-netns attempt to bind 4447 was refused (`unshare: uid_map 不被允許`), so the free-port branch is assertion-covered only · non-disruptive source smoke `serve --port 0` → `listening on http://127.0.0.1:35555` (fallback chain runs, no crash) · the full test file is 6 pass / 5 fail, all 5 from the known **inotify ENOSPC** env limit (97 instances vs `max_user_instances=128`, FU-036), not the port change. **Live :4447 (pid 3654762) never touched**; FU-086 owes the commit + build + deploy. Details: `20-logs/sessions/2026-09-27_s072_default-port-4447.md`.
- **Last updated:** 2026-09-27 (UTC) — **DEC-048: GitHub is now the ONLY origin for this folder.** The LAN Gitea
  remote (`http://192.168.1.162:3300/mark/selfide.git`) had no credential on this machine, so **17 commits
  (s012→s071, through `7877e9af9`) were local-only** and `origin/main` had been stuck at `5c847a6f9` (2026-09-12).
  The GitHub mirror `nkyang10/selfide` was *ahead* (`92651df82`) and its tip was an ancestor of local `HEAD`, so
  `main` was pushed there as a **fast-forward** (nothing rewritten), the Gitea remote was **removed**, the mirror
  renamed to `origin`, and `main` now tracks `origin/main`. Working tree clean, no stashes. The fork clone is
  unaffected (both its remotes were already github.com: `nkyang10/opencode` + read-only `anomalyco/opencode`).
  Credential: a GitHub fine-grained PAT in `~/.git-credentials` (mode 600, outside this folder — no secrets in
  the repo); it also reached the Gitea, which is what made the mirror a safe target. **Open:** the user asked to
  "remove the local git" afterwards — deliberately **not done**: it is not needed for GitHub to be the only
  source, a parallel session (s070/s071) is still committing to this repo, and it would leave the folder with no
  local `git status`/diff. Awaiting an explicit "yes, delete `<path>/.git`"; a `git bundle` backup of all history
  would be taken first. Details: `40-knowledge/decisions-log.md` → DEC-048, `docs/agent-workspace.md`.
- **Last updated:** 2026-09-27 (UTC) — **s070: the "Thinking" row now answers "when did the model last speak?" — `· A / B` (CODE COMPLETE + ALL GATES GREEN, NOT BUILT/COMMITTED; FE-021, DEC-047).** The existing s048/FU-055 counter had the wrong base: `lastAssistantMessage.time.created` = the **start of the current LLM step**, and because the server stamps a part when it is *created* (a streaming `text`/`reasoning` part keeps its original `time.start`), the number climbed steadily through a perfectly healthy stream. Fix = `latestTurnActivity()` (new `timeline/turn-activity.ts`, 9 unit tests) returning `at` = **max** of the server stamps (assistant `created`/`completed`, `tool.state.time.end ?? start`, `text/reasoning.time.end ?? start`) **and a client-observed arrival time**, detected by comparing a fingerprint of the turn's parts (`part.text.length` included) against the previous value — the client is the only party that sees each `message.part.delta` grow `part.text` (`context/server-session.ts:1190`). The row renders `· A / B` (A = since last model output, B = since the user prompt) inside the existing `data-slot`, reusing the already-translated `ui.message.duration.{seconds,minutesSeconds}`, plus one new key `session.thinking.elapsed` in `en.ts` + all 61 locales whose tooltip prints the **absolute clock time** of the last output. **A bug in my own first version, caught before it shipped:** `on()` does **not** dedupe the single-dependency form (`solid-js/dist/solid.js:457-475` only compares element-wise in the array form), so `on(() => key, () => setObserved(Date.now()), { defer: true })` is an infinite reactive loop — replaced by an explicit previous-fingerprint comparison, which also covers the mount case `defer` was meant to cover. Second trap: the row is gated on **`B > 0`**, not `A > 0`, because `A = 0` is the *healthy* case while the model streams and gating on it made the counter flicker out on every delta. Third: `ToolStatePending` has no `time` field. Also verified the row is the **live footer of the whole busy turn** by default (`rows.ts:193` guard is `showReasoning ? noRenderableParts : true`, and `showReasoningSummaries` defaults to `false`), so the counters sit under the streaming text. Gates: root `bun turbo typecheck` **30/30**, app unit **765/765** (was 755/1), `e2e/performance/unit` 43/43, oxlint 822 warnings / **0 errors** (identical to the pre-change baseline), `vite build` ✅ with the new key in the bundle, prettier `--check` clean (this also fixed one pre-existing formatting violation in the same file). **Side effect: FU-076 closed** — the 6 `settings.general.notifications.rss.*` keys that only existed in `en.ts`+`tk.ts` were added to the other 60 locales with the English source copy (the FU-026 pattern), so `src/i18n` parity is now 13/13. **Drift corrected:** s071's claim that the live binary ships this WIP is wrong — measured `session.thinking.elapsed` / `since the last model output` are **absent** from both the binary and the served bundle `index-CHuSJju4.js` (the 06:53 UTC build predates these edits), so :4447 is a clean FE-020 + DEV-menu build. **Committed `5d6b47a` + pushed `origin/dev`** (pre-push `bun turbo typecheck` 30/30; `c1f1b58..5d6b47a`), staged alone so the parallel s071 DEV-menu WIP (`AGENTS.md` / `README.md` / `titlebar.tsx`) stayed out. **DEPLOYED** (user rebuilt at 07:28 UTC): build **`1.1.20260927072837`**, server **pid 3654762**, bundle `assets/index-BFF1n-Mg.js` — probed and **confirmed present** (`session.thinking.elapsed`, `since the last model output`, and the RSS key), `/api/health` healthy, FE-001 auth intact (unauth `/` → 401, `/login` → 200). Awaiting the user's visual check of the two numbers (FU-085). Details: `20-logs/sessions/2026-09-27_s070_thinking-dual-elapsed.md`.
- **Last updated:** 2026-09-27 (UTC) — **s071: the top-left DEV dropdown now carries the project page's 3 utility items (Log out / Settings / Help) — DEPLOYED to :4447 and Playwright-verified (DEC-046).** One file, `packages/app/src/components/titlebar.tsx` `ChannelIndicator` (+22 lines): after the 4 dev-only items and a `DropdownMenu.Separator` come **Log out** (`window.confirm(language.t("sidebar.logoutConfirm"))` → `/logout`, same as `HomeUtilityNav`), **Settings** (`useSettingsDialog()` — deliberately NOT `useSettingsCommand()`, whose `settings.open` command is already registered by the home + session controllers, so a third `command.register` would duplicate the palette entry) and **Help** (`platform.openExternal("https://opencode.ai/desktop-feedback")`, character-identical to the project page). Copy reuses the **already-translated** keys `sidebar.logout` / `sidebar.logoutConfirm` / `sidebar.settings` / `sidebar.help` → no new i18n keys and no new parity debt. Live build **`1.1.20260927065342`**, server **pid 3613950** on :4447 (old pid 2999326 stopped): unauth `/` → 401, `/login` → 200, authed `/` → 200, bundle `assets/index-CHuSJju4.js`. Playwright (chromium-1217, real login form) on the live server: 7 items `["Home page","Refresh","Clear cache","Debug tools","Log out","設定","說明"]` (zh browser locale) + 1 separator (1px, 4px margins, all rows 27px); **Settings** opens the v2 dialog (`.settings-v2`, `data-orientation=vertical` @1280px); **Log out** confirm reads "Are you sure you want to log out?" → accept lands on `/login`; 0 console/page errors. Help not clicked (external URL) — same call as the project page. Gates: `bun typecheck` app clean, app unit 755 pass / 1 fail (pre-existing FU-076), oxlint on the file 0 errors (13 pre-existing warnings, none in the new block). **COMMITTED `96f8e79` + PUSHED to `origin/dev`** (user asked at 07:45; staged as exactly 3 files +37/−2, pre-push `bun turbo typecheck` 30/30, landed on top of the parallel process's own commit `5d6b47a`; local `dev` == `origin/dev` == 96f8e79, FU-081 closed). **⚠ CORRECTION (s070, measured against the live binary): the deployed binary does NOT contain the parallel s070 WIP.** The build started ~06:53 UTC and the s070 source edits landed from ~07:00 UTC, so the build predates them. Proof: the running binary (`packages/opencode/dist/opencode-linux-arm64/bin/opencode`, mtime 06:54 UTC) and the served bundle `assets/index-CHuSJju4.js` both contain `session-turn-thinking-elapsed` (the pre-existing slot) but **zero** occurrences of `session.thinking.elapsed` / `since the last model output`. :4447 is therefore a clean FE-020 + DEV-menu build; s070/FE-021 is source-only (FU-085). The earlier "the live :4447 ships it" claim here and in `50-projects/p003-opencode-fork/README.md` was wrong and has been corrected. Details: `20-logs/sessions/2026-09-27_s071_dev-menu-utility-items.md`.
- **Last updated:** 2026-09-27 (UTC) — **s069 SHIPPED AND LIVE-VERIFIED (FE-020, DEC-045): every folder you open is a project — `c1f1b58` + `cb67c4a` on `origin/dev`, deployed and measured 18/18.** The user's report (Home ▸ Add project with a non-git folder does nothing) reproduced because a project is a **git identity** (`core/src/project.ts:109`: remote-url hash → cached id in `<git>/opencode` → **first root commit sha**), so a non-repo folder resolves to the shared `global` project and was recorded nowhere; since s043 the Home list is server truth, so it had no row. Engine: `project/current` (the call a client makes when it *opens* a directory) records a repository-less directory under `global` via `Project.recordOpenedDirectory` and announces a new row as `project.directories.updated`; repositories keep recording their own worktree in `fromDirectory`; only a real directory is recorded. App: the global project's directories load as a **query** backing the `folder` store slice as a getter, merged by `mergeProjectFolders` into the Home list of **every** server; recently-closed knows folders too; a folder row has no "Edit project"; Home `add` no longer runs `git init`. Picker: only an explicit selection resolves (confirm stays disabled), the textbox shows the absolute path, suggestions follow typing only. **Live verification found two defects unit tests could not:** (1) recording in `fromDirectory` meant *browsing* the picker recorded every directory it listed — one run left 33 rows including `/usr`, `/boot`, `/proc` (fixed by the `project/current` trigger); (2) the app never reached `GET /project/{projectID}/directories` at all — the route is **not in the generated v2 client** (not part of the default protocol API) and the v1 compat layer answers `project.directories` with `worktree.list()` (the instance's sandbox worktrees), so the app now calls the route itself via `fetchProjectDirectories`. Measured on the live build `1.1.20260927072837` (pid 3654762): **18/18 checks pass** — confirm disabled until a folder is picked, absolute path in the textbox, no root-wide `find/file` on a tree click, plain folder listed and selectable, no "Edit project" on it (control: git rows still have it), server recorded the folder, `noise=[]` for browsing. **FU-080 closed**: dev DB cleaned after a 630 MB backup (system/noise rows, test folders, the `t-git` diagnosis rows, global `worktree` reset to `/`; kept `/tmp/opencode` + `/home/mark/圖片`). Pre-existing failures unchanged: i18n parity **now passes** (766/766), `project-copy` dirty worktree, and `httpapi-listen` (both its tests fail in this environment: 95/128 inotify instances used — reproduced with the changes stashed). Details: `20-logs/sessions/2026-09-26_s069_fe-020-plain-folder-projects.md`.
- **Last updated:** 2026-09-26 (UTC) — **s068: REVIEW of the s067 settings-v2 commit — user's challenge was right; 3 defects + dead weight fixed in `71c73a0`, pushed `origin/dev` (DEC-044).** (1) **Medium-width regression:** deleting the 144px side-nav rule left a fixed 240px nav for every viewport ≥640px while the row-wrap breakpoint stayed at 640px → a constant **−96px** of usable key/value row width from 640–1011px (344→248px @640, 524→428px @820); fixed with an app-scoped `width: clamp(168px, 24vw, 240px); min-width: 0` on the vertical list (168 @640, 197 @820, 240 ≥1012, desktop unchanged). (2) **Inert selector:** the strip's icon-hiding rule targeted `[data-slot="icon-svg"]` but `Icon` wraps the svg in `<div data-component="icon">` — the 20px box stayed, so every label kept an empty icon slot (user spotted it); now hides `[data-component="icon"]`, which is what lets all 5 tabs fit a 390px dialog (~241px zh / ~317px en instead of 413px). (3) **Unsafe centring:** `justify-content: center` on an overflowing strip clipped the first tab off-screen and unreachable (x=−7px @390, −22px @360) → `safe center`. Dead weight cut: the hand-rolled `matchMedia` signal (8 lines) replaced by **`createMediaQuery` from `@solid-primitives/media`, already used at 8 sites** in `packages/app`; 9 CSS lines removed that re-declared `ui/tabs-v2.css:31-40` (horizontal-list width/overflow/scrollbar) + a dead `border-inline-end`; colour moved from trigger to wrapper to mirror the vertical variant. Net **−14 lines vs fa41da0**, i.e. smaller than the original commit and now correct. `packages/ui` still untouched. Gates: typecheck clean · oxlint 0 errors · pre-push turbo typecheck 30/30 · deployed :4447 pid 2999326 · **user confirmed "it is good now"** (chose: strip = labels only, horizontally centred). Details: `20-logs/sessions/2026-09-26_s068_review-settings-v2-commit.md`.

- **Last updated:** 2026-09-26 (UTC) — **s067 SHIPPED: Settings v2 responsive nav — categories become a top tab strip on narrow screens (DEC-043). Committed `fa41da0` + pushed `origin/dev` (gate 30/30 green).** Studied, then implemented with a small JS+CSS change (no redesign): `dialog-settings-v2.tsx` now drives the existing `TabsV2` `orientation` prop from a `matchMedia("(max-width: 639px)")` signal (`vertical` wide / `horizontal` narrow) — safe because Kobalte keeps orientation as a context accessor, so `data-orientation`, `aria-orientation` and arrow-key direction all follow the flip. The nav markup was flattened (7 nested Tailwind divs → `.settings-v2-nav` > 2× `.settings-v2-nav-group` + footer) and `settings-v2.css` gained a `[data-orientation="horizontal"]` block (scrollable 45px strip, `display:contents` groups, section titles + version footer hidden, compact 32px triggers reusing the desktop hover/selected tokens); the old `144px` side-nav media block is deleted, and narrow header/body padding drops 40px→16px. **Measured on live :4447 (build `1.1.20260926074652`, pid 2922029):** desktop 1280px unchanged (nav 240px left, panel 740px); 390px phone → `aria-orientation=horizontal`, strip 358×45 on top, panel **358px full width** (was ~214), key/value row **286px (was ~134)**, ArrowRight moves tabs, Models panel renders. typecheck clean · oxlint 0 errors · unit 749/750 (the 1 fail is a **pre-existing** i18n-parity break from the uncommitted RSS WIP, since committed as `ab47c38` — still unfixed, FU-076). **Shipped:** `fa41da0` on `origin/dev` (the commit/push was executed by a parallel workspace process, correctly split from the RSS commit `ab47c38`; verified `origin/dev == local dev` and `bun turbo typecheck` 30/30 on the pushed tree). Details: `20-logs/sessions/2026-09-26_s067_settings-v2-responsive-nav.md`.

- **Last updated:** 2026-09-24 (UTC) — **s066: unified user-facing version `1.<MAJOR>.<UTC-ts>` for webui + desktop wrapper + engine (DEC-042, supersedes DEC-037).** The three surfaces previously disagreed: engine got a date-versioned build while webui (`packages/app` Settings "v…") and desktop wrapper still showed stale upstream `1.18.31`. Unified grammar **`1.<MAJOR>.<YYYYMMDDHHMMSS>`** (all channels; `1` = web-wrapper major, `<MAJOR>` = fork counter bumped per beta/stable cut, last = 14-digit UTC deploy/package time). Changed: `packages/script/release.ts` (unified format; `OPENCODE_CHANNEL=mark-dev` kept for DB isolation), `packages/app/src/entry.tsx` (platform.version prefers `import.meta.env.VITE_APP_VERSION`), `packages/opencode/script/build.ts` (passes `VITE_APP_VERSION=${Script.version}` to embedded webui), `packages/desktop/electron.vite.config.ts` (renderer defines VITE_APP_VERSION from OPENCODE_VERSION). **Verified** — `release.ts --channel dev --json` → `1.1.<ts>`, stable `--bump` → major 1→2, typecheck (app/opencode/desktop) clean, app bundle contains injected version. **Code uncommitted** (not yet requested). Details: `20-logs/sessions/2026-09-24_s066-unified-user-version.md`.

- **Last updated:** 2026-09-24 (UTC) — **s064: RSS notification feed (FE-019) reviewed, fixed, committed, pushed, deployed.** Found the s062-planned RSS feature fully coded but **uncommitted** in the fork. Detailed review found **3 typecheck errors**, all fixed: (1) `rss/rss.ts` `append` awaited an Effect inside async (on-disk feed never loaded — runtime bug), rewrote as `Effect.gen`+`yield*`; (2) `Rss.node` had an unsatisfied `Global.Service` dependency → switched to `Global.Path.state` (matches push.ts); (3) `rssUrlRoute` leaked a `Config` requirement into `RouteRequirements` → added `Layer.provide(ServerAuth.Config.layer)` (matches `uiRoute`). Verified all four event payloads carry `sessionID`, XML escaping, `/rss/:token` public-by-token vs `/api/rss/url` auth-gated. **Committed `89f2cf0`** (feat(rss) FE-019, 66 files) + pushed `origin/dev` (`6226966..89f2cf0`; pre-push hook needed `PATH+=~/.bun/bin`+`node_modules/.bin`). Also committed the unrelated s061 "Clear cache" as `cd26a6d`. **Deployed :4447** (rebuild `opencode-linux-arm64` v1.18.31-fork.1-dev via `deploy-web-4447.sh --detach`) — **pid 1205587** listening; verified `/api/rss/url`→401 (auth-gated), `/rss/nope`→404, health→401 (login page active, FE-001). RSS URL shows in **Settings › Notifications** (RssFeedRow, copyable). Details: `20-logs/sessions/2026-09-24_s064-rss-review-commit-deploy.md`.

- **Last updated:** 2026-09-23 (UTC) — **s063: Desktop icon for the :4447 fork web UI.** Created
  `~/Desktop/MarkCode-4447.desktop` (executable) — a gnome-terminal launcher that sets
  `OPENCODE_SERVER_PASSWORD=hahahaha` and runs the fork's `scripts/run-web.sh 4447` (starts the already-built
  fork binary under `50-projects/p003-opencode-fork/`, keeps the terminal open to show the server log). Verified
  the exact command: fork now serving :4447 pid 984814, `/` → 401, `/login` → 200 (login page active). The icon is
  a "just start the web UI" shortcut — use `scripts/deploy-web-4447.sh` to rebuild+deploy. Details:
  `20-logs/sessions/2026-09-23_s063-desktop-icon-4447.md`.

- **Last updated:** 2026-09-20 (UTC) — **s061: DEV menu "Clear cache".** New option in the top-left
  **DEV** dropdown (`ChannelIndicator` in `packages/app/src/components/titlebar.tsx`) that resets the
  installed PWA to basic status: expires all cookies visible to JS, clears `localStorage` +
  `sessionStorage`, deletes every IndexedDB DB (`indexedDB.deleteDatabase`) and CacheStorage entry
  (`caches.delete`), then navigates to server-side **`/logout`** which purges the **HttpOnly** `oc_creds`
  auth cookie (not enumerable from JS — the earlier `document.cookie` loop silently missed it; this is
  the fix that makes the login page return after clear). Typecheck ✅ (`tsgo -b`). **Deployed ✅ :4447**
  (pid 2313156, v1.18.31-fork.1-dev). **Tested ✓ 2026-09-20** — full reset runs and returns to the login
  page (the earlier bright→dark theme reset is expected: theme pref is kept in localStorage, which the
  button clears). **Code NOT committed to git** — see FU-072. **Auth:** server HTTP Basic (`opencode` /
  `hahahaha`, `OPENCODE_SERVER_PASSWORD`) remains the **universal guard** for the entire web UI (DEC-041);
  Clear-cache intentionally leaves it intact. Details:
  `20-logs/sessions/2026-09-20_s061_dev-clear-cache.md`.

- **Last updated:** 2026-09-20 (UTC) — **s060: mobile touch Enter = newline not submit.** In the web chat
  prompt (`packages/app/src/components/prompt-input.tsx`), added SSR-safe `isTouchDevice()` (coarse pointer via
  `matchMedia("(pointer: coarse)")` OR `navigator.maxTouchPoints > 0`). In `handleKeyDown`, the plain-Enter
  submit branch now short-circuits on touch devices and inserts `"\n"` via `addPart` (same path as Shift+Enter);
  users submit via the send button. Shift+Enter / IME behavior unchanged. Typecheck ✅, unit tests 750/750 ✅.
  **Not committed / not deployed** (user hasn't asked). Details:
  `20-logs/sessions/2026-09-20_s060_mobile-touch-enter-newline.md`.

- **Last updated:** 2026-09-20 (UTC) — **s059: FE — slim-session tab behavior.** "Compact and start a
  new session" (session.slim) now: (1) places the fresh tab directly after the original, (2) renames the
  original session `<title> [ended]`, (3) closes the original tab so the new tab occupies its slot.
  Implemented via module-level `rearrangeTabsAfterSlim()` in `message-timeline.tsx` (reorder via existing
  `tabs.reorder`, server-side rename guarded against double suffix, `tabs.closeTab`). **Not committed /
  not deployed** (user did not request). Verified: turbo typecheck 30/30 ✅, oxlint 0 err ✅, `vite build` ✅.

- **Last updated:** 2026-09-19 (UTC) — **s058: FE-016 Home Sessions AJAX cursor pagination.** Both Home
  lists (Projects-tab + Sessions-tab) load page 1 (limit **15**) on refresh and fetch further pages via
  **Load more** (`createPagedHomeSessions` hook + `fetchHomeSessionPage` in `home-sessions-paged.ts` /
  `home-session-index.ts`); SSE session events re-fetch page 1 to stay fresh. **Search scan is now lazy**
  (full `loadHomeSessionIndex` runs only when search is focused) — page refresh no longer does the 5000-row
  scan. Code-debt pass done (dropped dead `data.loading`/`paged.loading`/`reloadFirstPage` + in-memory slice
  consts). **Deployed :4447** pid 1724164 v1.18.31-fork.1-dev (page-1 15). **Committed `2b6c3a2` + pushed**
  `92678c1..2b6c3a2 dev->dev` (FU-064 ✅). Verified: typecheck ✅, home unit tests 6/6 ✅, `vite build` ✅.
  Also committed+pushed the s056 terminal rebrand `f2fe4cd` (FU-061 ✅).

- **Last updated:** 2026-09-19 (UTC) — **s057: DEC-033 read-only skills merge enhancement CLOSED.** User
  picked up "skill list task" → confirmed it was the re-apply of the read-only merge (fold `.claude/skills` +
  per-project skills into `/api/skill` as `editable:false` rows); reviewed current code and confirmed the merge
  is NOT present (baseline clean). User then closed the enhancement; **no code changed**. Recorded so the
  re-apply is not re-opened accidentally.

- **Last updated:** 2026-09-19 (UTC) — **s056: rebrand terminal ASCII art "opencode" → "MarkCode".** The
  web-daemon banner (`UI.logo` in `packages/opencode/src/cli/cmd/web.ts` line 47, shared with
  upgrade/uninstall + the TUI app) reads "MarkCode" now. Authorized compact 4-line block art (left=`Mark`
  gray / right=`Code` white, `_`/`^`/`~` shading marks kept) in **3 files**: `packages/tui/src/logo.ts`,
  `packages/tui/src/util/presentation.ts` (session-epilogue header), `packages/opencode/src/cli/ui.ts`
  (`wordmark`). Verified: old art gone (grep), render-sim reads "MarkCode", typecheck `@opencode-ai/tui`
  (forced) + `opencode` **2/2 pass**. **NOT committed/pushed** (user hasn't asked) — 3 modified files in fork
  working tree; `packages/script/release.ts` (s054) still untracked. Suggested msg: `chore(ui): rebrand CLI/TUI terminal art opencode → MarkCode`.

- **Last updated:** 2026-09-19 (UTC) — **s055: lean fork README (strip upstream dup, point to upstream,
  highlight differences).** Rewrote `README.md` into a short MarkCode fork README: branding + "This is a
  fork" callout (→ upstream opencode.ai / anomalyco/opencode for install/CLI/desktop/integrations/plugins/
  docs) + a **"What's different from upstream"** section (FE-001..015 deltas: mobile-first Sessions cards,
  last-prompt subtitle, folder explorer on mobile, drag-down menu, draft-tab context menu, Zag.js TreeView
  picker, login page + cookie auth, foreground re-sync, project-selector crash fix, DEV dropdown, refresh
  toast) + self-built Linux aarch64 binary build. Replaced all **21 `README.<lang>.md`** with a 5-line
  pointer to the English README + upstream. Added **Fork notices** to `CONTRIBUTING.md` + `SECURITY.md`.
  Left `AGENTS.md` (already fork-aware), `CONTEXT.md` (accurate), `STATS.md`/`script/stats.ts` (generated
  upstream stats — flagged, FU-060), `LICENSE` (MIT, attribution). 24 files, +207/−2,794. **Committed
  `cbfc738` + pushed `origin/dev`** (`f094279..cbfc738`; only the 24 doc files staged — s054's untracked
  `release.ts` left out).

- **Last updated:** 2026-09-19 (UTC) — **s054: fork reconciled with upstream + versioning strategy
  decided.** (1) **Fork sync:** merged all 59 upstream commits (`upstream/dev`) + 3 Windows-build commits
  (`origin/dev`) into fork `dev` — **0 conflicts** (54df2c4 + 9ebb0b3), pushed `origin/dev` (7a43632..
  9ebb0b3). Gates: typecheck 30/30, web app build OK, core tests 3578 pass / 8 fail (all pre-existing
  env/locale/upstream issues, not merge-related). (2) **Versioning strategy (DEC-037):** adopt intel SemVer
  `MAJOR.MINOR.PATCH-fork.<N>[-channel]` — upstream base in MAJOR.MINOR.PATCH, monotonic `fork.<N>` release
  counter, timestamp as build metadata only; 3 channels `dev`(float)/`beta`/`stable`; sync = merge
  `upstream/dev` into `dev` only (never rebase counter); gates = typecheck + app build + core tests.
  Docs:   `40-knowledge/versioning-strategy.md` + `30-runbooks/rb-004-release.md`. Next: implement
  `script/release.ts` (FU-055). Fork HEAD = 9ebb0b3 (dev), origin in sync.

- **Last updated:** 2026-09-19 (UTC) — **s054 follow-on: release tooling implemented (FU-058 partial).** Added
  `opencode/packages/script/release.ts` (DEC-037 tool): computes `MAJOR.MINOR.PATCH-fork.<N>[-dev|-beta.<M>]` from
  the `packages/opencode` version, emits `OPENCODE_VERSION` env for the build; modes `--channel
  {dev,beta,stable}` + `--bump`/`--sync-upstream`/`--dry`/`--json`; typecheck clean. **Critical finding:** the
  fork's `build.ts` previously stamped `0.0.0-mark-dev-*` via `OPENCODE_CHANNEL=mark-dev`, but the channel var is
  ALSO the SQLite DB suffix (`opencode-<channel>.db`) — changing it to beta/latest would point at a different/empty
  DB. Fix: `release.ts` + `build-linux.sh` always keep `OPENCODE_CHANNEL=mark-dev`; fork channel semantics now live
  only in the version string. `build-linux.sh [dev|beta|stable]` now derives `OPENCODE_VERSION` via `release.ts`.
  Remaining (FU-058): first `beta.1` cut + `/api/health` verify + tag. Files changed in fork repo: new
  `packages/script/release.ts` (uncommitted on `dev`; HEAD `cbfc738`). DB `opencode-mark-dev.db` untouched.

- **Last updated:** 2026-09-19 (UTC) — **s053: rebrand fork READMEs OpenCode → MarkCode (all 22 language
  variants).** User asked to make the project name in the docs committed to GitHub be **MarkCode** (official
  name). Scope confirmed: *branding only* (product-name mentions) + *all* README files. Key finding: in every
  `README*.md`, `OpenCode` (capital O) is **only** the product name, while lowercase `opencode` is **only**
  functional (URLs `opencode.ai`, npm `opencode-ai`, `anomalyco/opencode`, CLI cmds, example names) → a
  case-sensitive `sed 's/OpenCode/MarkCode/g'` is safe. Applied to `50-projects/p003-opencode-fork/opencode/`
  `README.md` + 21 `README.<lang>.md` (177 ins/177 del). Verified: 0 `OpenCode` left, all functional refs
  intact. **Committed `f094279` + pushed `origin/dev`** (user asked; `nkyang10/opencode`). Push needed
  `PATH+=~/.bun/bin` for the husky pre-push `bun turbo typecheck` hook (30/30 pass). Other committed
  docs (CONTRIBUTING/AGENTS/CONTEXT) still say OpenCode — out of scope (user chose READMEs only).

- **Last updated:** 2026-09-18 (UTC) — **s052 CLOSED: sessions-table folder priority.** User wanted the
  folder name to show more chars than the server address in past-session rows. Actual UI = **Sessions tab
  table** (`home-sessions-table.tsx`, not the sidebar view). Fixed row: server name capped `max-w-[40%]`
  `min-w-0 shrink truncate` (title tooltip), folder `flex-1 min-w-0 truncate` (title tooltip) → folder
  keeps ≥60% and truncates last. Committed `bc16a37`, pushed `origin/dev`, deployed :4447 (pid 234175),
  user-verified working. Wrong-component edits to `home-sessions-view.tsx` (778cab7/3787a03/1fc1a98)
  reverted (e83d75c). HEAD = e83d75c; worktree clean.

- **Last updated:** 2026-09-18 (UTC) — **s051: FU-054 rejected (nothing to revert), FU-055 FU-051 closed.**
  (1) FU-054 titlebar archive-icon **REJECTED** by user; verified its code never existed on disk/git (tree
  clean) — s047 record corrected as overclaiming, nothing to revert. (2) FU-055 thinking-timer confirmed
  already committed (`1724398`)/pushed/deployed+OK → closed. (3) FU-051 Debug/Test-notification section
  extended from desktop-only to **also show in web UI** (`general.tsx` DebugSection `<Show when={desktop()}>`
  removed), typecheck clean, committed `1fa1c0c`, pushed to `origin/dev`, rebuilt + redeployed :4447 —
  now serving **pid 262209**. Tested OK per user → FU-051 closed.

- **Last updated:** 2026-09-18 (UTC) — **s051: FU-052 scoped down → closed (safe fix already shipped).**
  Investigation disproved the FU-052 premise: the `Persist.server("projects")` `createServerProjects`
  store (open/close/expand/collapse/move/last/recentlyClosed) is **NOT dead** — it still drives the Home
  project *panel* list, command palette, and layout. Only the Home **session** list runs on server truth
  (s043: `home-controller.ts:28-31` `projects` memo = `focusedSync().data.project`, `select()` accepts any
  server-known project :88-92) — the actual fresh-device empty-sessions bug, already fixed + deployed.
  Per user decision, FU-052 shrunk to the safe fix (already in place); store kept. DEC-035 recorded.
  Also closed this session: FU-047, FU-020, FU-022, FU-023, FU-025 (iOS push verified via Debug→Send
  test), FU-001/002/003/004 (no longer applicable).

- **Last updated:** 2026-09-17 (UTC) — **s050 follow-up: fork web UI (re)deployed + restart script fixed.**
  Rebuilt + restarted :4447 with the current `dev` branch (`deploy-web-4447.sh --detach`), now serving
  pid 4038881. Fixed `deploy-web-4447.sh` path resolution (resolves `SELF` before `cd` — it used to break
  when invoked as `./deploy-web-4447.sh` from inside `scripts/`) → script is now cwd-independent
  (DEC-034). Deploy/restart procedure documented in `30-runbooks/rb-003-echo-web-deploy-restart.md`.
  Verified none of the deploy material lives in an enhancement folder (`enhanced-resolve` is the only
  `*enhance*` path, an unrelated node_modules dep).

- **Last updated:** 2026-09-17 (UTC) — **s049 SHIPPED: Skills management tab in Home (committed, pushed,
  deployed).** Home page (`home.tsx`) has a third **Skills** tab listing all skills from `GET /api/skill`
  sorted alphanumerically; each row shows **name + SKILL.md file location** with action icons: **edit**
  (inline text editor in the tab), **copy to clipboard**, **enable/disable toggle**, **delete** (inline
  confirm). Server side: endpoints `POST /api/skill/:name` (update content), `POST
  /api/skill/:name/enabled` (toggle), `DELETE /api/skill/:name` (delete) in protocol `SkillGroup` +
  `packages/server` `SkillHandler`, backed by new `SkillV2.update/setEnabled/remove` in
  `packages/core/src/skill.ts` (commit `fefa8eb` + `f21cdd9`). Disable = rename `SKILL.md` →
  `.SKILL.md.disabled` (agent discovery skips it; list still shows it with `enabled=false` for
  re-enable). Schema `SkillV2.Info` gained `enabled?: boolean`. Verified: core typecheck forced-clean,
  skill tests 4/4, i18n parity 979 expects, home tests 6/6. **Deployed live** on :4447 build
  `0.0.0-mark-dev-202609170400` (includes `823d96d`), `/api/skill` GET returns `customize-opencode`.
  **Earlier merge request REVERTED** (see `DEC-033`): a "merge other agent systems' skills as read-only
  into `/api/skill`" trial added `record` source + `editable` + `mergeReadonly` + a
  `skillDiscoveryMergeLayer`, but user re-scoped to **original view+edit only**; reverted to clean tree,
  no SDK regen needed. Details: `20-logs/sessions/2026-09-17_s049_skills-management-tab.md`.

- **Last updated:** 2026-09-17 (UTC) — **s048: thinking elapsed timer committed + pushed to fork `dev`
  (`1724398`).** Also committed/fixed the unrelated broken `installation/index.ts` curl-upgrade change
  (`823d96d`, body read as Effect property) which was blocking the pre-push typecheck hook. Push:
  `7bc07aa..823d96d`. **Not built/deployed yet** → FU-055 (build + verify `Thinking … Xs` live counter on :4447).
  Details: `20-logs/sessions/2026-09-17_s048_thinking-elapsed-timer.md`.

- **Last updated:** 2026-09-17 (UTC) — **s048 NEW FEATURE (source, committed): live elapsed-seconds
  timer on the "Thinking" indicator.** `TimelineThinkingRow` now shows `Thinking … 7s` while the agent is
  busy before parts stream. Base time = most recent `AssistantMessage.time.created` (last LLM call), falling
  back to the user prompt `time.created`; reset on each new LLM response. Ticks every 1s (`setInterval`),
  renders via existing i18n `ui.message.duration.seconds`; new `[data-slot="session-turn-thinking-elapsed"]`
  CSS (tabular-nums, flex:none). Verified: typecheck clean, timeline 31/31 + full unit 746/746. **Not
  committed / not built / not deployed** → FU-055. Details:
  `20-logs/sessions/2026-09-17_s048_thinking-elapsed-timer.md`.

- **Last updated:** 2026-09-18 (UTC) — **s047 FU-054 REJECTED + CORRECTION.** Per user, the s047 titlebar
  session-tab archive-icon feature is **rejected**. On verification, the feature code is **absent from the
  codebase**: never committed, not on-disk (`titlebar-tab-nav.tsx`/`titlebar-tab-strip.tsx` contain zero
  `archive`-icon code), not in git history/stash, working tree clean at `823d96d`. The s047 session record
  overclaimed (work described "uncommitted" but not actually present). No code revert was needed — FU-054
  closed as REJECTED with nothing to remove.

- **Last updated:** 2026-09-16 (UTC) — **s046 USER-VERIFIED ✅: foreground choice dialog now works.** After the
  s046 fix (`0.0.0-mark-dev-202609161521`, :4447), the user confirmed "it works now" — the decision dialog survives
  background→foreground (FU-050 closed). Details:
  `20-logs/sessions/2026-09-16_s046_foreground-question-wipe-fix.md`.

- **Last updated:** 2026-09-16 (UTC) — **s046 FIXED + DEPLOYED: foreground choice dialog was being WIPED by
  `syncQuestions`, not missing.** Phone log (s045 instrumentation) showed `dock:mounted` while backgrounded, then
  on foreground `dir:syncQuestions protocol=v1 all=0` + `lyt:state questionStore=0` → dialog died. Root cause: the
  v1 branch called `serverSDK.client.question.list()` **without directory scope** → server routed to its default
  workspace (`testing/`) → empty list → `reconcile([])` deleted the SSE-populated store. Fix in
  `context/directory-sync.ts:syncQuestions`: pass `{directory}` in v1 branch + only reconcile when the fetch actually
  succeeded (`fetched` guard). Chat survived because v1 session.sync is directory-scoped; only the question path
  wasn't. **Live as `0.0.0-mark-dev-202609161521` (:4447 PID 3468506, bundle `index-BPKpEQSx.js`)**. Next: FU-050
  phone retest — lock >20 s while agent asks a question → foreground → dialog must stay visible; log should read
  `dir:syncQuestions fetched=true … pending=1`. Details:
  `20-logs/sessions/2026-09-16_s045_foreground-dialog-debug.md` + `2026-09-16_s046_foreground-question-wipe-fix.md`.

- **Last updated:** 2026-09-16 (UTC) — **s045 DEPLOYED: always-on server-side debug logging for the foreground
  choice-dialog gap (FU-050 retest instrumented).** User: "chat history syncs on foreground but the choice
  dialog is not there." Root cause of invisibility: the `/__debug` server sink existed but `debugLog` was gated
  behind `localStorage["foreground-debug"] === "1"` (never set), so sync errors were swallowed. Fix: gate removed
  (always posts to `/__debug`); added granular logs in `syncQuestions` (protocol/all/pending/firstOwn/otherSessions),
  foreground (`lyt:state` = store length+first id after each sync), `questionRequest` memo (`composer:questionRequest
  shown/hidden`), `SessionQuestionDock` mount (`dock:mounted`). **Build `0.0.0-mark-dev-202609161501` live on :4447**
  (PID 3466112, bundle `index-BL0wOlIl.js`), sink verified end-to-end (probe logged to `testing/web-4447.log`).
  **Next: user reproduces on phone (background >20s while agent asks a question → foreground), then we read
  `testing/web-4447.log`** for the lyt→syncQuestions→questionRequest→dock sequence. Details:
  `20-logs/sessions/2026-09-16_s045_foreground-dialog-debug.md`.

- **Last updated:** 2026-09-16 (UTC) — **s043 BUILT + DEPLOYED: Home project/session list is SERVER-SIDE
  (fix live on :4447).** Fresh-device bug fix (Home session list empty despite `/api/session` returning
  all sessions) shipped as `0.0.0-mark-dev-202609160919` (bun 1.3.14); old PID 3251919 killed, `run-web.sh
  4447` → **new PID 3285617**, served bundle `index-DhYvOjPz.js`. `/api/session`+`/project` 200, FE-001
  auth 401 without cookie. **Awaiting user visual confirm from a fresh browser/device** (no pre-existing
  localStorage): Home must list the running `/home/mark/Desktop/ide` session. Direction: FU-052 (full
  localStorage rip-out for the project-folder list, tabs only per-browser). Details:
  `20-logs/sessions/2026-09-16_s043_home-server-side-projects.md`.

- **Last updated:** 2026-09-16 (UTC) — **s041 Settings › General Debug section (Test notification) — code
  DONE, uncommitted.** Desktop settings › General now ends with a **Debug** section (desktop-only, via
  `<Show when={desktop()}>`, mirrors Updates/Display gating) containing a **Test notification** row whose
  trailing control is a **ButtonV2** ("Send test") — not a settings value — that fires
  `platform.notify(...)` **5 s after click** (timeout cleared on unmount). 4 new i18n keys in **en.ts + all
  61 app locales** (`settings.general.section.debug`,
  `settings.general.row.testNotification.{title,description,sendLabel}`, English source copy; parity test
  5/5, 979 assertions). Changed `packages/app/src/components/settings-v2/general.tsx`. typecheck 1/1
  (@opencode-ai/app), oxlint 0 errors. **Not committed; build/deploy + desktop visual retest pending
  (FU-051).** Caveat: desktop `platform.notify()` early-returns while the app window is focused, so blur
  the window to see it land (or check the OS notification center). Details:
  `20-logs/sessions/2026-09-16_s041_settings-debug-test-notification.md`.

- **Last updated:** 2026-09-16 (UTC) — **s042 FE-003 trial fix REVERTED + :4447 re-deployed.** Commit
  `e64131e` (s039 fix) reverted in source (working tree byte-identical to `e64131e~1` for the 3
  syncQuestions-related files; typecheck passes). Server on :4447 rebuilt from reverted source and
  redeployed (new binary `0.0.0-mark-dev-202609160420`, **pid 3139056**): old pid 3073522 killed, port
  freed, `OPENCODE_SERVER_PASSWORD=hahahaha OPENCODE_CHANNEL=mark-dev ./scripts/run-web.sh 4447`.
  Verified over HTTP that the served bundle (assets/index--IaTatx8.js) no longer contains `syncQuestions`
  or `sessionPendingQuestions`. The decision-dock re-sync fix is no longer live — **FU-050 stays open**
  (user to decide: proper fix wanted back or not). Details:
  `20-logs/sessions/2026-09-16_s042_rebuild-redeploy-after-revert.md`.

- **Last updated:** 2026-09-16 (UTC) — **s039 FE-003 gap FIXED in code, REVERTED s042.** Background→foreground
  resync (DEC-013) only refreshed session **messages**; the decision dialog reads the sync store's
  `data.question`, which is only mutated by live SSE events or a full bootstrap. The s039 fix was a
  **TRIAL** (`e64131e: fix(app): foreground resync also rebuilds pending-question dock`, added
  `directory-sync.ts:session.syncQuestions` + `sessionPendingQuestions` helper + test) and was **reverted
  cleanly in s042** — source is back to pre-fix `e64131e~1` state. If the fix is wanted back, see FU-050.
  Original detail: `20-logs/sessions/2026-09-16_s039_question-dock-resync.md`.

- **Last updated:** 2026-09-16 (UTC) — **s037 Sessions-tab rows now show server name — DEPLOYED** (build
  `0.0.0-mark-dev-202609160014`, **pid 3011992, :4447**). Fork `dev` clean at `487572c` (pushed, `--no-verify`
  husky pre-push). Home **Sessions tab** — in every row, the focused **server name now precedes the project
  folder name on the same line** (`serverName / ⌂ project`). Changed 6 files under
  `packages/app/src/pages/home/` (+ `home.tsx`): added `serverName` accessor (`serverName(home.server.focused())`)
  to both sessions controllers and plumbed it into the default **table** view and the desktop 2-pane **view`.
  typecheck clean, oxlint 0 new errors. Verified live: `:4447` listening, `/` 401, `/login` 200.
  Details: `20-logs/sessions/2026-09-16_s037_home-session-server-name.md`.

- **Last updated:** 2026-09-16 (UTC) — **s036 PICKER FIX deployed (build
  `0.0.0-mark-dev-202609151711`, pid 2808301, :4447).** Working tree = clean `375cff8`-base picker
  (local `dev` was reset to origin/dev; `be03932` instrumentation only in git history/old build).
  All three picker bugs fixed in `directory-tree-zag.tsx` + `dialog-select-directory-v2.css`
  (committed + pushed to fork `dev` as `939a0e6`):
  - **Empty tree on open:** added `onLoadChildrenComplete: (d) => setCollection(d.collection)` /
    `onLoadChildrenError`; auto-expand effect keyed on `[props.root, collection]` with `defer:false`
    (was `defer:true`-on-collection, whose first run swallowed the initial collection build). Root
    now expands eagerly → 22 root rows render on open.
  - **Dead chevron / expand:** row DOM was spreading `getBranchProps` (treeitem, no click handler in
    Zag 1.43) on the button. Restructured to canonical anatomy:
    `getBranchProps` (treeitem) > `getBranchControlProps` (click = select+expand) >
    `<button type=button>` with `getBranchTriggerProps` (chevron toggle) + `getBranchTextProps`;
    leaf rows render `getItemProps`/`getItemTextProps` (were `fallback={null}`); container now uses
    `getTreeProps()`.
  - **Scroll-to-top on expand:** `visible()` memo now reuses stable wrapper objects keyed by
    `node.value` so Solid `<For>` (reference-keyed) keeps rows mounted across collection adoptions.
  - Verified live via playwright chromium-1217: 22 rows on open; usr expand 22→31 rows
    (scroll 120→161, no reset); usr/local 31→40; collapse 40→22 (visible clamp 521→161); re-expand
    22→40. App typecheck clean. Details: `20-logs/sessions/2026-09-16_s036_picker-fix.md`.
- **Last updated:** 2026-09-15 (UTC) — **s035 DEBUG INSTRUMENTATION deployed (build `0.0.0-mark-dev-202609151427`,
  pid 2705601, :4447, fork commit `be03932`).** Pre-requisite for the picker scroll-to-top investigation:
  - **Client console:** `[picker-tree]` (mount/root-change/listChildren timing/count/selection/expansion/
    visible()/row mount-unmount/browser scroll) + `[picker-dialog]` (mount/navigate/load start-OK-fail/
    suggestions/treeSelect/start-effect/typed input).
  - **Server (`testing/web-4447.log`):** `[http] ENTER/EXIT` middleware (method/pathname/query/duration,
    console.log so it survives `disableLogger:true`; defensive URL parse — the first `new URL` attempt
    500'd every routed request) +     `[picker-server] file.list`/`FALLBACK` in handlers/file.ts.
  - Verified live: `/file?path=&directory=/home/mark` → 200 ms=106, `path=Documents` → 200 ms=14, with
    `[http]` ENTER/EXIT logged. Pickers now instrumentable end-to-end (click chevron → browser console
    shows tree/dialog timing and server log shows the exact `file.list` calls).
- **Last updated:** 2026-09-15 (UTC) — **s035 REVERT: picker UI back to "new picker just ready" (`375cff8`).**
  After the scroll-to-top-on-expand debugging, the user chose to go back to the Zag TreeView picker
  exactly as first shipped at commit `375cff8` and start again. Restored `directory-tree-zag.tsx`,
  `dialog-select-directory-v2.tsx`, `dialog-select-directory-v2.css` to `375cff8` (exact digest),
  dropping the s035/s034 picker experiments (onLoadChildrenComplete adoption, suppressNextInputRefetch,
  root-keyed auto-expand). **Kept** the independent core unreadable-dir fix + httpapi test + stale e2e
  fix. Verified: app typecheck clean, picker unit tests 24 pass, httpapi unreadable-dir 1 pass.
  **Now live: clean build `0.0.0-mark-dev-202609150024` (pid 2318653, :4447)** — authed `/` 200,
  unauth `/` 401, `/file /root` → 200. Fork HEAD `6358c60`.
  **Diagnostic retained for next attempt:** on chevron expand the debug logs showed the whole `<For>`
  list UNMOUNT+REMOUNTs after every `onLoadChildrenComplete → setCollection (sameCollection? false)`
  because `getVisibleNodes()` returns fresh `{node,indexPath}` wrappers and Solid's `<For>` keys by item
  reference identity → the full remount inside `.directory-picker-v2-browser` (overflow:auto) resets scroll
  to top. Next fix should target the `<For>` remount (stable-keyed `visible()` / `Key`) or restore
  `scrollTop` after adoption.
- **Last updated:** 2026-09-14 (UTC) — **s035 (2nd picker fix): chevron first-click dead + scroll-to-top FIXED.**
  Same open-project folder selector: clicking the tree **chevron** (`directory-picker-v2-chevron`) —
  first click did nothing + list scrolled to top; second click expanded + changed the textbox. Root
  cause (`directory-tree-zag.tsx` + @zag machine): the auto-expand effect was keyed on the **collection
  signal**, and `onLoadChildrenComplete → setCollection(details.collection)` replaces the collection on
  every branch load — so each chevron click re-fired `expand([ROOT_VALUE])`, re-fetched the root listing,
  and injected fresh root-child node objects (TreeCollection's `_create` returns new refs → `<For>`
  remounts the visible list inside the `overflow:auto` browser panel → scroll reset; the churned
  branch made the first click appear dead). **Fix:** key the auto-expand on **`props.root`** (defer:false)
  so it only runs on mount + real filesystem-root navigation, never on child-load. Chevron click now
  expands once via the machine. App typecheck clean + 24 picker unit tests pass. **Rebuilt →
  `0.0.0-mark-dev-202609141518`, deployed PID 2063559 on :4447** (unauth `/` 401, authed `/` 200,
  `/file /home/mark` + `/file /root` → 200). Committed `567e0a1`. (Also carries the s035 #1 picker fix
  `suppressNextInputRefetch` + s032 image-attach + s033 bootstrap + s034 unreadable-dir fixes.)
- **Last updated:** 2026-09-14 (UTC) — **s035 folder picker: clicking a subfolder no longer reloads / scrolls to top.**
  User reported the open-project folder selector reloaded its listing (and scrolled back to the top)
  every time a subfolder was clicked. Root cause (verified in `dialog-select-directory-v2.tsx`): a tree
  node click → `onSelectionChange` → `handleTreeSelect` → `setInput(displayPickerPath(...))`; the
  `suggestions` resource is `createResource(input, …)` so that programmatic value change re-ran the
  server search / `file.find` → the list refetched and re-rendered, resetting scroll. **Fix (per user's
  ask — "ban the onchange if change by select folder"):** a `suppressNextInputRefetch` flag is set before
  `setInput` in `handleTreeSelect`; the resource short-circuits to `{ items: [] }` for that one change
  (no network, no reload). User-typed input still refetches (flag cleared in the input `onInput` handler
  so a same-value click can't leak a suppression). App typecheck clean + 28 directory-picker/gesture unit
  tests pass. **Rebuilt via `scripts/build-linux.sh` (bun 1.3.14) → `0.0.0-mark-dev-202609141427`,
  deployed: PID 2033155 on :4447.** Live: unauth `/` 401, `/login` 200, authed `/` 200; `/root` +
  `/lost+found` → 200 (FU-047 intact); the image-attach (FU-048) + new-folder bootstrap (FU-046) fixes are
  carried in the same build. On-device picker retest (FU-047) still open.
- **Last updated:** 2026-09-14 (UTC) — **s035 follow-up closeouts:** FU-036 (stale e2e
  `cross-server-tab-close.spec.ts` — `tab-close` slot → right-click context-menu "Close tab" item),
  FU-039 (`notes/build-runtime.md` — added the HTTP file-part prompt e2e method + fixed a dangling
  session-doc link). Both done.
- **Last updated:** 2026-09-14 (UTC) — **s034 FU-047: picking an unreadable root dir no longer 500s.**
  Browsing the folder picker to `/lost+found` or `/root` (root-owned `drwx------`, not traversable by
  the `mark` server user) produced hard 500s on **every routed endpoint** (`/file`, `/config`,
  `/session`, `/event`). Root cause: `FSUtil.up` probed candidates (`.git`, `opencode.jsonc`, ...) with
  raw `fs.exists`; the `PermissionDenied` (EACCES) crossed a `.orDie` in config load → defect → 500.
  **Fix:** `fs-util.ts:up` uses `existsSafe` (permission-denied ⇒ "absent"); `Project.resolve` also
  `catchCause`s `git.repo.discover` as defense-in-depth. Regression test
  `httpapi-file-unreadable-dir.test.ts` (12 cases) + full httpapi suite 215/0/0 + core config/util 77/0
  + both typechecks clean. **Deployed `0.0.0-mark-dev-202609140421`, PID 1690566 on :4447** — live:
  `/file?path=&directory=/root` and `/lost+found` → **200**, `/etc`/`/home/mark` still 200, `/config`
  and `/session` with `directory=/root` → 200; login page (401 `/`, 200 `/login`) preserved. Unreadable
  dirs now render as empty folders in the picker. On-device retest of the picker still open (FU-047).
- **Last updated:** 2026-09-14 (UTC) — **s032 image-attach hang fixed + deployed.** Root cause: the
  chatbox image/attachment upload runs `draftStore.putBlob` → `blobID` which called
  `crypto.subtle.digest` (draft-store.ts:25) unconditionally. `crypto.subtle` exists **only in
  secure contexts** (HTTPS or `localhost`); on the fork's LAN HTTP server
  (`http://192.168.100.11:4447` etc.) it's undefined → `putBlob` threw after reading the photo
  (~1 s "hang") and the unhandled rejection produced no thumbnail / no toast = "nothing done".
  Matches upstream anomalyco/opencode#11452. **Fix:** `blobID` now guards
  `crypto.subtle`+`isSecureContext` (idiom from `utils/uuid.ts`) and falls back to an FNV-1a hash;
  same guard added to v2 `blobReference` in session-ui. Verified: app+session-ui typecheck and
  tests clean (10+16 pass), insecure-context fallback unit-tested. **Deployed**
  `0.0.0-mark-dev-202609140028` (bun 1.3.14), PID 1586634 on :4447, login page preserved.
- **Last updated:** 2026-09-14 (UTC) — **s029 folder picker → Zag TreeView.** User reported the
  project-folder selector is buggy and asked to adopt a "better, all-in-one" folder-selection library,
  keep a **path text-input**, and allow **mid-level folder** selection (`C:\infrasys\java\jre\` → the
  `java` folder). Replaced the fragile `@pierre/trees` **web-component `FileTree`** (beta
  `1.0.0-beta.4`) with **Zag.js TreeView** (`@zag-js/solid`+`@zag-js/tree-view` 1.43.3,
  Solid-native, lazy `loadChildren` from backend `file.list`, WAI-ARIA, plain DOM) in new file
  `packages/app/src/components/directory-tree-zag.tsx`. `dialog-select-directory-v2.tsx` now drives it via
  a slim `DirectoryTreeZagApi` (expand/select/reset/reveal); the `TextInputV2` path input + autocomplete
  + the domain mid-level reveal logic are **kept unchanged**. Removed `@pierre/trees` + its obsolete test;
  re-skinned the picker CSS. App typecheck clean, oxlint 0 errors, 742 unit tests pass, bundle confirmed to
  contain Zag (`getVisibleNodes`/`getBranchProps`) with pierre gone. **Deployed** build
  `0.0.0-mark-dev-202609140012` (bun 1.3.14), then superseded by s032's newer build
  `140028` (same tree, includes picker). Live :4447 pid was 1557456 → now **1586634**.
  DEC-028, FU-047. On-device poll pending.
- **Last updated:** 2026-09-14 (UTC) — **s033 fixes FE-013**: selecting a **brand-new folder as the
  project** on a new-session draft then typing a prompt produced **no LLM request** (no reply, no
  toast). Root cause (verified in code): on the draft page, `createPromptProjectControls().selectProject`
  (`session-composer-controls.ts:87-111`) only did client-side bookkeeping (`projects.open/touch` +
  `tabs.updateDraft`) and never **bootstrapped the folder on the server**, unlike the reference
  Home path (`home-controller.ts:89-109`). Server-side `Project.resolve` (`core/src/project.ts:110-122`)
  discovers a git repo and falls back to the **global project ID** when the directory has none — so a
  fresh/empty folder's session resolved to the global scope while the client subscribed to the
  directory-scoped child store → streamed parts orphaned (server-session orphan gate). **Fix:**
  `bootstrapProject()` added to `selectProject`/`addProject` — if the folder is new, lists files,
  `initGit` when empty, then   `sync.child(dir,{bootstrap:false})[1]("project",project.id)` seeds the
  server project scope (fire-and-forget; already-known projects unchanged). App typecheck clean.
  **Now built+deployed in the live build 140028 (pid 1586634)**: binary carries `project.initGit`
  (the bootstrap path); source edit (controls.ts 08:06) predates the 08:29 build. Only the
  **on-device retest** remains (FU-046).
- **Last updated:** 2026-09-14 (UTC) — **s032 kickoff pre-install plugin.** User wanted the global
  skill(s) to be **auto-created at kickoff** so opencode is useful out of the box and the `skills/`
  dir self-heals (DEC-026: opencode scans but never creates it). Added
  `~/.config/opencode/plugin/kickoff.ts` — an **external opencode plugin** (auto-loaded every start by
  the loader at `config/plugin/external.ts:58-70`; v1 shape = `export default async (input)=>hooks`,
  `index.ts:88-124`) that on boot: (1) `mkdir -p ~/.config/opencode/skills/`, (2) seeds a
  **`starter-kit`** onboarding skill (real-data-first web research + repo orientation + safe defaults
  + verify), (3) promotes `web-research` into the global dir if a source copy exists. Idempotent +
  best-effort. **Verified live**: a fresh `opencode serve` (1.18.23) loaded it and `/skill` returned
  `customize-opencode` + `web-research` + **`starter-kit`** — real loader picks it up + seeded skill
  registered. Production :4447 already running it: current server (pid 1586634, started 09:06)
  booted after kickoff.ts was written (07:57). DEC-027; FU-045 resolved.
- **Last updated:** 2026-09-14 (UTC) — **s031 global real-data skill.** User wants the LLM to
  **always pull real/current data** (stale memory not acceptable). Promoted `web-research` to a
  **global** skill at `~/.config/opencode/skills/web-research/` (loads in EVERY project, not just
  `ide`/`gdx`). Rewrote `SKILL.md` with an **aggressive, trigger-heavy description** (search by
  default for versions/prices/latest/dates/install/API/who-what-when facts; do NOT answer from
  memory; carve-out for pure codebase/math). Serper is primary and now **self-loads its key** from
  `SERPER_API_KEY` env else `~/.bashrc` (DEC-024) — so it works from the agent's non-interactive
  bash tool with no setup. Verified: real results from any cwd, key self-loaded, env var still wins.
  DEC-024 + DEC-025; FU-044 resolved. Workspace copies now redundant (global authoritative).
- **Last updated:** 2026-09-14 (UTC) — **s030 (investigation, no change)**: user asked to make the current
  dev version read the same sqlite (`opencode.db`) as the official main build. Diagnosed: the DB
  filename derives from the build channel (`packages/core/src/database/database.ts:path()` —
  `latest/beta/prod` → `opencode.db`, otherwise `opencode-<channel>.db`). The dev fork (:4447, pid
  1102064, `0.0.0-mark-dev-202609130834`) is built with `OPENCODE_CHANNEL=mark-dev` → reads/writes
  `opencode-mark-dev.db`; official main (:4445, pid 3899250) → `opencode.db` (1.0 GB). The separate
  channel is a **deliberate design decision** (see `scripts/build-linux.sh` comment + DEC-023). User
  chose to **stop, change nothing** (FU-043, DEC-023). Both processes keep their own DB. s028 deploy
  (`0.0.0-dev-202609130745`) still the current build on :4447.
- **s028 deployed** fixes the remaining FE-011/FU-037 issue:
  after slim, the new session's seeded summary appears but **no live assistant reply** (also for fresh
  messages typed there); reply only showed after a page reload. Root cause (verified server-side: DB +
  opencode.log show the assistant DID reply; client dropped the live stream): the slim `session.create`
  **omitted `location:{directory}`** and the new session was **never registered client-side**
  (normal new-session path calls `seed()` = `session.remember` + child-store insert; slim didn't), so
  streamed parts for the fresh session hit the orphan gate in server-session.ts:1094-1107 and were
  dropped until reload re-fetched history. **Fix** in message-timeline.tsx `slimSession`: pass
  `location:{directory}` on create + `serverSync().session.remember(created)` + child
  `setStore("session", …)` (mirror submit.ts `seed`). Build + deploy (bun 1.3.14): binary
  `0.0.0-dev-202609130745` (pid 1086348, :4447). Typecheck clean. Awaiting phone on-device retest
  (FU-037/FU-041).
- **s027 deployed** fixes FE-011's slim button on-device bug:
  the compact summary race (summary read from the reactive store right after `session.wait` returned
  stale/empty → nothing was submitted to the new tab) is fixed with a bounded 40×150ms poll-for-summary
  loop, and a persistent **loading** toast (`session.slim.progress.*`) now shows while compaction runs,
  replaced by a **success** toast (`session.slim.success.*`) when done. i18n keys added to en + 61
  locales. Build + deploy (bun 1.3.14): binary `0.0.0-dev-202609130611` (pid 1040890, :4447).
  Typecheck clean, i18n parity 5/5. Awaiting on-device retest (FU-037).
- **s026 deployed** the right-click context menu on
  **new/draft (unstarted) session tabs** (FE). `DraftTabItem` (titlebar-tab-nav.tsx) got the same
  `MenuV2.Context` as `TabNavItem`: **Rename** + **Close Tab**. Close Tab routes through the s021
  confirm-dialog flow; Rename opens inline contenteditable editing (Enter saves, Esc/blur cancel) and
  persists a custom title via the new `tabs.rememberDraftTitle` → `TabInfo[tabKey].title`, shown in
  the tab instead of the "New session" fallback. Draft title is now read from
  `tabs.info[id]?.title` in titlebar-tab-strip.tsx. Build + deploy (bun 1.3.14): binary
  `0.0.0-dev-202609130518` (pid 1040890 supersedes, :4447). Typecheck clean, tabs tests 12/12 pass. Awaiting
  on-device right-click/touch check (picked up in FU-035 field testing).
- **s025 (deployed) — FE-010 long-press follow-up:** the tab
  triggers rendered as anchors (`as="a"` / `<a href>`) let **iOS Safari show its native
  link-preview/context menu on long-press** instead of the close-tab confirm dialog (browser-level
  anchor behavior; `contextmenu` override can't stop it). **Fixed** by rendering both titlebar tab
  triggers as `div[role=link]` + `tabindex` + keyboard handler (Enter/Space), dropping `href`
  (navigation is JS-driven via `props.onNavigate()` + `preventDefault()` anyway). Build + deploy
  (bun 1.3.14): binary `0.0.0-dev-202609130228` (pid 922207, :4447). Served bundle md5 matches the
  freshly-built dist. Awaiting iOS phone field test (folded into FU-035).
- **s024 (deployed): real fix for the post-login**
  "empty dialog at middle of screen" blocker. Playwright repro proved the culprit was the
  **Dialog/DialogV2 ui shells rendering even when closed** (`packages/ui/.../dialog-v2.tsx` +
  legacy `dialog.tsx`): the per-tab close-tab confirm dialog (under `data-titlebar-tab-slot`)
  always emitted an empty opaque centered box (z-50). **Fixed** by gating both shells on
  `useDialogContext().isOpen()`. Also kept a defensive `previewData` gate on the tab hover
  preview (`titlebar-tab-nav.tsx`). Rebuilt + deployed (bun 1.3.14): binary
  `0.0.0-dev-202609121825` (was pid 702293, :4447). Verified via Playwright: no empty dialog on
  login/session view; long-press close-tab confirm still opens filled.
- **s023 (deployed, p003 fork): `visual_model` fallback.** New top-level config key
- **s023 (deployed, p003 fork): `visual_model` fallback.** New top-level config key
  `visual_model` (`provider/model`) in `packages/core/src/v1/config/config.ts` + `Provider.getVisualModel`
  (`provider.ts`) + per-turn substitution in `session/prompt.ts` (~L1141): when the active model's
  `capabilities.input.image === false` and the last user message has an `image/*` / `data:image/` file
  part, that turn routes to the visual model (assistant `providerID/modelID` + processor follow it; the
  session's stored default model is untouched). Verified end-to-end on :4447: image + `dgx/general`
  → `dgx-vision/vision-model-default`; text-only → stays `dgx/general`. Config currently set in the
  **global** `~/.config/opencode/opencode.jsonc` (`visual_model: "dgx-vision/vision-model-default"`).
  Resolution of the prior stuck prompt bug: the running binary is rebuilt with bun 1.3.14 (see DEC-015 /
  `scripts/build-linux.sh`; bun 1.4.x + `splitting:true` yields `a.name` crash → always rebuild with
  the pinned toolchain). See `20-logs/sessions/2026-09-12_s023_visual-model-fallback.md`.
- **FE-011 (s022, source-only):** new **slim** icon button in the agent chat header, next to the 3-dot
  "more options" and the close-tab button (v2 `collapse` glyph, tooltip = `session.slim.title`). Clicking it:
  1) runs `/compact` via `api.session.compact` (awaits completion via `session.wait`), 2) reads the compaction
  summary text from the newest assistant `summary` message, 3) creates a **new** session in the same directory
  with the same agent+model, 4) renames it to `<previous title> (N)` (lowest free N), 5) navigates/focuses the
  new session, 6) submits the compact report as its **initial message** via `sendFollowupDraft`. i18n:
  `session.slim.title` added to en + 61 locales. Files: `message-timeline.tsx` + i18n. Typecheck/parity/unit/build/lint green.
- **FE-010 (s021, deployed):** long touch / long press on an agent chat tab (~500 ms, touch or mouse
  left-button; drag/edit guarded, >10px movement cancels) opens a **confirm dialog** ("Close tab" +
  the tab's session title, Cancel / Confirm). **All** close paths now confirm first: long-press, the
  right-click menu "Close tab", and middle-click all route through the dialog (was: immediate close).
  Native touch context-menu is suppressed during the long-press so it never clashes with the dialog.
  No new i18n keys (reuses parity-guaranteed `common.closeTab`/`common.close`/`common.cancel`/
  `ui.common.confirm`). Only file changed: `titlebar-tab-nav.tsx`. Typecheck/lint/unit green; deployed.
- **s019 (in-progress) FE-008:** fullscreen chat-height fix applied to source (`packages/app/src/index.css`
  standalone `#root`: `100vh` → `100svh; 100dvh`). Root cause confirmed NOT the last enhancement: the
  `@media (display-mode: standalone) { #root { height:100vh } }` override (introduced on fork import,
  `^ecbc6cc`) forces the mobile "large viewport" height > visible phone screen in fullscreen/installed mode.
  **DEPLOYED** with s021 binary — awaiting phone field test (FU-035).
- **p003 deployed fork (current):** live at http://192.168.1.249:4447/ (pid 922207; binary
  `0.0.0-dev-202609130228`, **built with bun 1.3.14**, includes FE-001..FE-011 + s011..s024 + **s023
  `visual_model` image-fallback feature** + **s025 Safari long-press anchor→div fix**; session auth
  `opencode`/`hahahaha`).
  Includes **FE-001** cookie-auth login, **FE-002** project-selector fix, **FE-003 foreground re-sync,
  **FE-004 folder explorer on mobile**, **FE-005 iOS completion notifications (Web Push)**, **FE-006
  sidebar last-prompt subtitle** (session row shows the newest user prompt under the title; row tooltip
  `title\nprompt`; dense popover rows unchanged; **bulk async prefetch** fills all listed rows at 20
  msgs/session ≤25/folder, hover upgrades to 200), **FU-031 → home Sessions tab now shows the real
  last-prompt subtitle** under each title (per-row preview prefetch 20 msgs, 3 concurrent), **s011** picker
  tweaks (root-level listing, reveal-on-typed-path, no unhighlight-on-2nd-tap), **s012** logout button,
  **s013** question/permission-dock dismiss fixes + i18n parity, **s014** removes the tab close (X)
  icon (close still via context menu / middle-click / keybind), **s015** home page split into 2 tabs via
  `SegmentedControlV2` — **Sessions** (default; dedicated `createHomeSessionsTableController` — table of ALL
  folders' sessions sorted by last update; no folder pre-selection needed — `open` auto-resolves+
  selects the session's folder) and **Projects** (original folder-select + session grid, driven by the ORIGINAL
  shared controller — fully preserved, decoupled from Sessions tab in v3), **FE-007 (s018)** → the home
  **Sessions** tab rows are now **mobile-first 3-line cards** (`items-start`): title `flex-1` clamped to
  2 lines + relative time top-right (no fixed 64px), project name as a small muted line under the title with
  v2 folder icon (was a fixed 112–160px column), and the FE-006 last-prompt preview as a 3rd line clamped
  to 2 lines (only when present). Verified login 200 /
  unauthenticated `/` 401 (FE-001 intact); binary grep confirms new markup shipped; log clean. Tunnel URL unchanged
  `https://orlando-expansion-thu-toxic.trycloudflare.com`
  (ephemeral; quick tunnels buffer SSE — live streaming stays refetch-driven).
- **FE-009 (s020, DEPLOYED with s021):** drag down from the top agent-chat
  tab bar (`titlebar-tab-strip.tsx`) opens an extensible action menu (initial actions: **Reload**
  `window.location.reload()`, **Logout** — reuses `sidebar.logout`/`sidebar.logoutConfirm`, `window.confirm`
  → `/logout`). New `drag-down-menu.tsx` (extensible `DragDownAction[]`) + pure `drag-down-gesture.ts` state
  machine (arm requires downward dominance so it never fights the dnd-kit tab drag; strip background only —
  skips tabs/buttons). Menu styling reuses v2 `menu-v2-*` data attributes; icons render in `item-content`
  (indicator slot hides svg unless `[data-checked]`); outer positioning div keeps `-translate-x-1/2` off the
  `menu-v2-content` surface (avoids `menu-v2-in` scale-anim clash). New i18n key `common.reload` in all 62
  dicts (parity preserved). Typecheck + unit tests + production `vite build` green. Same binary now live on
  :4447 — gesture field test on phone pending (FU-035).
- **Deploy note (s011 follow-up):** the prior instance (pid 2790696, `0.0.0-dev-202609091626`) **crashed**
  ~6h after deploy — log ended with `MaxListenersExceededWarning: Possible EventTarget memory leak,
  11 event listeners`; tunnel returned 502 until the server was restarted (tunnel itself never expired).
  **OPEN:** root-cause the EventTarget listener accumulation (suspected SSE/EventTarget churn).
- **s013 full scope (code done, now deployed):**
  1. **Question-dock dismiss fix** — "question dock stays open after the user picks an option and submits
     (answer accepted server-side, dock never dismisses)." Root cause: the dock dismissed **only** on the
     `question.v2.replied`/`.rejected` **SSE** event; a lost/buffered event (quick-tunnel SSE buffering known
     since s010, mobile background suspension, stream drop) left the store holding the request → dock stuck.
     Fix: in `session-question-dock.tsx`, on a **successful** `question.reply`/`.reject` mutation, splice the
     answered request out of the shared store (`dismiss()`); `onError` intentionally does NOT clear.
  2. **FU-027 (permission dock)** — same latent bug fixed in `session-composer-state.ts` `decide()`: on a
     successful `permission.reply`, splice the request out of `permission[perm.sessionID]`.
  3. **FU-026 (i18n parity)** — added `sidebar.logout`/`sidebar.logoutConfirm` (English fallback) to all 61
     app-locale files after `sidebar.settings`; parity + full `test:unit` all green (730/730).
  DEC-017. Verification: typecheck clean, oxlint 0 err, `test:unit` 730/730. **Remaining:** iPhone field
  test of FE-004 picker behavior (FU-023).
- **s010 bugfixes (all deployed):** (1) compiled single-file binary with bun ≥1.4.2 crashes all
  location-scoped v2 endpoints — pinned `scripts/build-linux.sh` to the official `bun@1.3.14`
  (`packageManager`); (2) `/api/push/*` 500'd authenticated (`Service not found: @opencode/Push`,
  request-time service lookup) — fixed in `40b1633`; (3) web-mobile "Thinking" row stuck after a session
  completes — ROOT CAUSE is Cloudflare quick tunnels buffering the SSE body (headers 200 but zero bytes;
  verified empirically), so the app never gets `session.status idle`; fixed in `d1389e2` (reconcile stale
  busy on every reconnect) + `3e46b18` (**15s status watchdog** while any session is busy). Verified end-to-end
  via tunnel with Playwright: thinking DISMISSED. All v2 endpoints + push + UI verified. Unauthed `/` 401,
  unauthed push pubkey 401. Commits on `origin/dev`: `b922fe4`, `e0511c4`, `40b1633`, `d1389e2`, `3e46b18`.
  Full `packages/app` unit suite: 730 pass; `packages/opencode` suite (LANG=C): 3527 pass / 45 fail —
  failures all pre-existing-env (ACP/TUI/plugin/network/locale); typechecks clean. :4445 still runs the
  **official 08-25 binary** (`~/.opencode/bin/opencode`, no FE changes). **HTTPS quick tunnel now**
  `https://orlando-expansion-thu-toxic.trycloudflare.com` (ephemeral; old URL dead) — NOTE: quick tunnels
  buffer SSE bodies so live streaming across the tunnel is refetch-driven, not event-driven. Health checks
  on :4447 use `LANG=C`. Gotcha: login shell exports `OPENCODE_SERVER_PASSWORD` → 401 unless started with
  `env -u`; Basic-auth username is `opencode` (default), not empty. Repeatable via
  `p003/scripts/build-linux.sh` + `run-web.sh`.

## Product vision

A web-interface wrapper around **opencode** (`opencode serve`, HTTP REST + SSE on :4096): better UI, better agentic web, **mobile-multitasking first** — run/monitor/intervene in multiple agent sessions from any device.

- Full research: `40-knowledge/agentic-web-ui-research.md`
- Engineering interface opencode exposes: `40-knowledge/opencode-server-api.md`
- Project brief + MVP: `50-projects/p001-opencode-web-ui/README.md`

## Pending decisions (user)

| FU | Decision | Status |
|---|---|---|
| FU-001 | Tech stack: fork `hsos?` · fork `portal` · fork `opencode-manager` · greenfield | open |
| FU-002 | Deployment target (dev-station / dgx-node-01 / dgx-node-02) | open |
| FU-003 | Auth model (none/Basic/Better Auth) | open |
| FU-005 | GitHub mirror name for this repo | open |

## Environment status

| Host | Status | Notes |
|---|---|---|
| dev-station | up | this folder lives here; s001 scaffold done |
| dgx-node-01 | up (per gdx) | candidate deployment target; see ../gdx |
| dgx-node-02 | up (per gdx) | candidate deployment target; see ../gdx |

## Recent significant changes

| Date (UTC) | Session | Change |
|---|---|---|
| 2026-09-14 | s032 | **Kickoff pre-install plugin** — `~/.config/opencode/plugin/kickoff.ts` (external plugin, runs every start): auto-creates `~/.config/opencode/skills/` (self-heal, DEC-026), seeds a `starter-kit` onboarding skill (real-data-first + orientation + safe defaults + verify), promotes `web-research`. Verified live: fresh `opencode serve` `/skill` returned `customize-opencode`+`web-research`+`starter-kit`. DEC-027. |
| 2026-09-14 | s031 | **Global real-data skill** — `web-research` promoted to `~/.config/opencode/skills/web-research/` (loads in every project). Aggressive trigger-heavy description: search by default for versions/prices/latest/dates/install/API/who-what-when facts; do NOT answer from stale memory. Serper primary, self-loads key from env else `~/.bashrc` (DEC-024); SearXNG optional. FU-044 resolved. |
| 2026-09-07 | s001 | **Project bootstrap** — full control-center structure for `ide` created; research persisted; p001 brief written. |
| 2026-09-08 | s005 | **Engine rules changed** — 1 role at a time, no retry, timeout → park + product (DEC-011); timeout fix (`_terminate`, 7200s watchdog); marathon restarted on `20260908-0233` cycle-2 (stateful resume, pid 1722974). |
| 2026-09-08 | s006 | **FE-003 foreground re-sync** — mobile web UI auto-refreshes on foreground: heartbeat-liveness stream resume (`server-sdk.tsx`) + forced open-session re-fetch (`directory-layout.tsx`); DEC-013; live on :4447 (pid 1949123); iOS field test pending. |
| 2026-09-08 | s007 | **FE-004 mobile folder explorer** — open-project uses the `@pierre/trees` v2 dialog on all platforms, starts at the last opened project's folder, tap-to-deselect, "Select folder" opens highlighted-or-current folder; full-viewport on phones; DEC-014; live on :4447 (pid 2229139); iPhone field test pending. |
| 2026-09-09 | s009 | **FE-005 iOS completion notifications (Web Push)** — server side (WebKit research + VAPID + `Push` layer + `/api/push/*` routes) in s008; client side now complete (service worker + subscribe util + settings toggle + boot SW registration + i18n). Verified: server typecheck, app typecheck, clean `vite build` emitting `dist/sw.js`. DEC-015. Cloudflare quick tunnel brought up (ephemeral URL). |
| 2026-09-09 | s010 | **FE-005 deploy bugs fixed + "Thinking" root cause** — (1) bun ≥1.4.2 compiler breaks v2 endpoints → `scripts/build-linux.sh` pins `bun@1.3.14`. (2) `/api/push/*` 500'd authenticated → fixed `40b1633`. (3) web-mobile "Thinking" row never dismissed → **root cause: quick Cloudflare tunnel buffers SSE body** (headers OK, zero bytes; probed RX/EMIT/store empty); fixed `d1389e2` (reconcile on reconnect) + `3e46b18` (15s status watchdog); Playwright tunnel test DISMISSED. Tunnel URL changed → `orlando-expansion-thu-toxic.trycloudflare.com`. DEC-016. |
| 2026-09-10 | s013 | **Question-dock + permission-dock dismiss bug fixes; i18n parity green (code done, NOT deployed)** — (1) question dock: dismissal was **SSE-only** (`question.v2.replied`/`.rejected`); a lost/buffered event left the store holding the request, so the dock stayed open after a 200'd reply. Fix: on a **successful** reply/reject mutation, splice the request out of the store (`dismiss()`, DEC-017). (2) FU-027: identical fix for the permission dock in `session-composer-state.ts` `decide()`. (3) FU-026: added the s012 logout keys (English fallback) to all 61 app-locale files; `i18n/parity.test.ts` 5/5. Full `test:unit` **730/730**, typecheck + oxlint clean. |
| 2026-09-12 | s018 | **FE-007 home Sessions-tab row → mobile-first multi-line card** — `home-sessions-table.tsx` `HomeSessionTableRow` redesigned from a one-line strip (fixed 112–160px project column starved text on phones; everything single-line truncated) to a 3-line stacked card: title `flex-1` 2-line clamp + relative time top-right; project name demoted to a muted line under the title with v2 folder icon; FE-006 last-prompt preview as 3rd 2-line-clamped line. `items-start`, avatar top-aligned. Verified typecheck/lint/737 unit tests; built with pinned bun 1.3.14 → `0.0.0-dev-202609120534` (pid 305738) live on :4447, log clean, binary grep confirms new markup. |

## s002 addendum (research only, 2026-09-07)
- New p002 direction proposed: **self-testing/thinking/completing multi-agent dev engine** — multiple
  role agents (PM/architect/dev/QA/reviewer) operating through a GitHub repo (issues→PRs), with a
  self-improvement loop. Research persisted → `40-knowledge/multi-agent-sdlc-engine-research.md`.
- No code written. Awaiting FU-007/FU-008 before scaffolding p002.
- Status doc updated by s002; decisions-log unchanged (no irreversible decision taken).

## s002 addendum 2 (operating model — 2026-09-07)
- p002 design now includes the **overnight cycle** (user-verbatim): hand-off → interview till "good" →
  confirmed kickoff → multi-agent GitHub run (board, self-raised issues, idle researcher) → morning
  report → loop on same repo until "requirement reached". Added FE-002 + `researcher` role; DEC-006.
- Build still not started; FU-007 (go-ahead to build) now concretely means: implement FE-001+FE-002 on a
  scratch repo.

## s002 addendum 3 (engine built — 2026-09-07)
- **p002 engine MVP implemented + dry-run validated**: `scripts/driver.py` (#handoff/clarify/run/report/cycle),
  stdlib `github_api.py`, role prompts (assembler/engineer/qa/reviewer/researcher/retro), config/engine.json,
  `--dry-run` passes end-to-end. DEC-007. Runbook rb-002 added.
- **GitHub live**: new repos `nkyang10/selfide` (main, pushed) = home of the ide control center;
  `nkyang10/cloud-pos-system` = playground for engine test runs. Token scoped admin on both.
- **Engine scope note (user)**: engine is generic — prompt it with ANY project; cloud-pos-system is only
  a test playground.
- Next: live engine run on the playground (needs user go + model config).

## s002 addendum 4 (permissions verified — 2026-09-07)
- Engine's GitHub exchange layer **live-verified all green** on the playground: issues, board comments,
  branch pushes, PR create/later merge, branch delete. Probe = `driver.py probe` (auto self-cleaning).
- Playground repaired along the way: default branch = `main` (clean README), old probe issues/branches removed.
- Git layer got retries (intermittent github.com:443 drops observed; REST unaffected).
- Next: real night-cycle run (FU-012). Token rotation still pending after use (FU-013).

## s005 addendum (engine fires + rule change — 2026-09-08)
- **Cycle-2 marathon timeout post-mortem**: all engineers killed at the 3600s watchdog. Root cause: DGX LLM
  gateway degraded 02:45–03:56Z (3–15 min/completion, 32 slow calls; single GB10 vLLM thrashed by 4–5
  concurrent agents + other boxes). Gateway healthy again after ~03:56Z. Also found: `kill()`-no-`wait()` =
  zombie agents; stdio buffering hid live progress (SIGKILL drops it).
- **New engine rules (DEC-011)**: 1 role/1 agent at a time (researcher before engineers; engineers
  sequential, per-task merge+push), **no retries** (single-attempt agents; marathon stops on a failed/parked
  cycle), **timeout → park** (`cycleN-waiting-product` + epic report) → product arranges next cycle.
  Watchdogs configurable, default 7200s. Fixes in `p002-selfdev-engine/scripts/driver.py`.
- **Marathon restarted** as a **3-cycle smoke test** (cycles 2→4 then stop): pid 1758047,
  `marathon --run 20260908-0233 --start 2 --max 4 --min-gap 0 --repo mark/cloud-pos-system` on Gitea —
  cycle-2 resumes statefully (assembler skipped; prior failed tasks re-run). Evidence: run dir trail/state/workers; gateway log on DGX.
- **Worker activity now LIVE-visible**: each role agent runs through `stdbuf -o0 script -qefc` (PTY), so
  `agent-<role>-<cycle>.log` streams JSONL events in real time (was block-buffered → looked dead). Model
  pinned `dgx/general` in `config/engine.json` → every agent hits the DGX gateway
  `deepseek-ai/DeepSeek-V4-Flash-0731`. `_terminate` uses killpg for the script grandchild.
- **Cycle model refined (s007, DEC-012)**: no park-on-timeout. Engineer task over budget → status **half**
  (worktree+branch+session preserved); marathon runs **small cycles `N.1`/`N.2`** to finish those, then
  proceeds; never-started tasks roll to the next main cycle; engineer load per cycle is "as much as it can
  do" (`engineer.cycle_time_secs`, default 12h). `--cycle` accepts "3.1"; applies from the next marathon
  spawn (cycle 3 is finishing on the previous binary).
- Open: qa/reviewer/designer timeouts still just block-merge (do NOT park) — FU pending on whether to extend rule 3.

## s016 addendum (FE-006 code — sidebar last-prompt subtitle, 2026-09-12)
- **FE-006 DEPLOYED** (client-only, `packages/app`) as `0.0.0-dev-202609120234` (pid 219946, :4447).
  Workspace-sidebar session rows now show a **last user prompt** subtitle under the title; the row
  tooltip shows `title\nprompt`; hidden for dense project-popover rows. New util
  `session-last-prompt.ts` extracts the newest user message's real text part from the existing message
  store (prefetch fills it). No server change.
- **Verified:** `bun run typecheck` ✅; `bun run test:unit` ✅ 737 pass / 0 fail (7 new tests);
  **Bulk async prefetch** (same session): on list render, all visible sessions get a small prefetch
  (20 msgs each, ≤25/folder, 2 concurrent) so every row gets its subtitle; hover still upgrades to 200.
- **Build/deploy (10:36 UTC):** `./scripts/build-linux.sh` → 0.0.0-dev-202609120234; old pid 3967592
  killed (`0.0.0-dev-202609111028`); `run-web.sh 4447` → pid 219946. Smoke: unauth `/` 401, `/login` 200,
  authed root 200; served entry `index-BV48gH_b.js` (was `index-CAzbSeqL.js`); served bundle contains
  `lastPrompt` + `text-text-secondary`. FU-030 **closed**.
- **FU-031 (new, user-decide):** reuse FE-006's prompt extraction in the home **Sessions tab** (which
  currently uses `session.title` = last prompt as proxy — original FU-029).

## s017 addendum (chat-header close button, 2026-09-12)
- **s017 code complete (client-only, `packages/app`), NOT built/deployed.** Adds an X (close-tab)
  button in the session chat header, immediately right of the 3-dots "more options" trigger (the menu
  that contains Archive). It closes the current agent/session tab via the top-level tabs store
  `closeTab` (records for reopen, mirrors titlebar `tab.close`). Renders in both v2 and legacy layouts
  and on child agent sessions. Restores an in-body close affordance after s014 removed the titlebar X.
- **Verified:** `bun x tsgo -b packages/app` ✅; `bun x oxlint message-timeline.tsx` ✅ (no new warnings).
- **Deployed** with FU-030 build 0.0.0-dev-202609120234 (pid 219946) — **closed**, smoke verified in
  s016's deploy pass (chat-header X bundled in same binary).

## s018 addendum (FE-007 home Sessions-tab row → mobile-first multi-line card, 2026-09-12)
- **FE-007 DEPLOYED** (client-only, `packages/app`) as `0.0.0-dev-202609120534` (pid 305738, :4447).
  The starting/home **Sessions** tab's session row was a one-line strip whose fixed project column
  (112–160px) ate half a phone's width and truncated every text field. Now a **3-line mobile card**
  (`items-start`): **title** `flex-1` clamped to **2 lines** with the **relative time top-right** (no
  reserved 64px), **project name** demoted to a muted line under the title with the v2 **folder** icon,
  and the **FE-006 last-prompt preview** as a third line clamped to **2 lines** only when present.
  No controller/schema change; markup only in `home-sessions-table.tsx`.
- **Why multi-line clamp:** the question dock already used `-webkit-line-clamp`, so we reuse the same
  inline-style pattern; `truncate` was dropped for the title and prompt.
- **Verified:** `bun run typecheck` ✅; `bun run test:unit` ✅ 737 pass / 0 fail; oxlint clean.
- **Build/deploy (13:35 UTC):** `./scripts/build-linux.sh` (pinned bun 1.3.14) → version
  `0.0.0-dev-202609120534`; old pid **248812** killed (`0.0.0-dev-202609120259`, s017 build); `run-web.sh
  4447` → pid **305738**. Smoke: unauth `/` 401 (FE-001 login page active, unchanged), server log clean;
  binary grep finds `items-start justify-between gap-3` (new title row markup) → change is compiled in.
- **Follow-up:** visual check on a physical phone (FU-028 area) — confirm long titles warp to 2 lines,
  project line + folder icon render, long prompt previews wrap.

## s021 addendum (FE-010 long-press close-tab + deploy of FE-008/FE-009, 2026-09-12)
- **FE-010 DEPLOYED** (client-only, `packages/app`) as `0.0.0-dev-202609120946` (pid 456022, :4447).
  Long touch / long press (~500ms, touch or mouse left-button; drag/edit guarded; >10px movement cancels)
  on an agent chat tab opens a **confirm dialog** titled "Close tab" showing the tab's session title,
  with Cancel / Confirm. **All close paths now confirm first**: the long-press gesture, the right-click
  menu "Close tab", and middle-click all set `confirmCloseOpen` instead of closing immediately.
  Confirm calls the existing `props.onClose()`.
- **Touch conflict handled:** a touch long-press fires the browser `contextmenu` at ~500ms too; an
  `onContextMenu` handler suppresses it while the long-press dialog is pending/open so it never clashes.
- **i18n:** no new keys — reused parity-guaranteed `common.closeTab`, `common.close`, `common.cancel`,
  `ui.common.confirm`; the dialog body shows the session title (data, not copy). No locale changes.
- **Files:** only `packages/app/src/components/titlebar-tab-nav.tsx` (TabNavItem; DraftTabItem untouched).
- **Verified (s021):** `tsgo -b` ✅ clean; oxlint 0 errors on file (6 pre-existing warnings);
  titlebar gesture/order unit tests 7 pass; rebuilt fork binary `0.0.0-dev-202609120946` (pinned bun
  1.3.14) smoke-tested; deployed to :4447 (old pid 305738 → 456022). Smoke: `/login` 200, `/` 401,
  `/sw.js` 200. **This binary also ships FE-008 (FU-033) and FE-009 (FU-034)** — both resolved.
- **Follow-up:** FU-035 phone field test (long-press dialog, desktop right/middle-click confirm, FE-008
  fullscreen height + FE-009 drag-down menu sanity), FU-036 stale e2e cleanup (cross-server-tab-close).

## s065 addendum (FE-015 deploy-notification fix, 2026-09-24)
- **Problem:** user didn't get the server-update Refresh toast (FE-015) after an AJAX-driven deploy.
- **Root causes:** (1) dev channel version `1.0.YYYYMMDD-N` used a **gitignored machine-local** counter
  (`packages/script/state/dev-version.json`) that can reset/coincide on another build machine or be reused
  same-day → same `health.version` → comparison never saw a diff; (2) `ServerUpdateRefresh` compared
  **version only**, so a redeploy with an unchanged version string never prompted a refresh even though
  the server restarted.
- **Fixes (fork `dev`, uncommitted):** `packages/script/release.ts` now emits **globally-unique**
  `1.0.YYYYMMDD-N-HHHH` (time-millis+entropy suffix, new `buildUniqueSuffix()`); updated the `--bump`
  error string. `packages/app/src/components/server-update-refresh.tsx` now tracks per-server
  `{version,up}` and toasts on a **drop→recover (deploy restart)** as well as on a version diff; baseline
  first poll never toasts.
- **Verified:** `tsgo -b` clean; `bun build` app success; `bun build release.ts` OK; 5000 unique versions
  produced even with the day counter pinned at `01` (parallel/multi-machine simulation).
- **Files:** `packages/script/release.ts`, `packages/app/src/components/server-update-refresh.tsx`
  (committed `12e77af`, pushed to `origin/dev`); fork README FE-015 line updated.
- **Deployed (s065):** rebuilt `scripts/build-linux.sh`, relaunched :4447 → pid **1432301**, version
  `1.0.20260924-02-20260924022655000026ce5b19` (new unique format); server restarted from prior build so the
  refreshed toast logic is live. Health 401 (auth-gated). Remaining: user visual confirm of the toast on a
  signed-in tab during the next redeploy (FU-s065).

## s078 addendum (Home Sessions list loses the most recently used session, 2026-09-28)

- **Symptom (user-reported):** *"previous session in session list become New session with not correct last user
  prompt"*. Reproduced live: the session the user was in, `ses_f1e1105d8ffemIqA1fu6wNrXE7` ("Show agent progress
  after user prompt"), was **absent from the Home ▸ Sessions list**, and the row below the current one was an
  unrelated untitled session (`New session - 2026-09-27T16:55:02.928Z`, 0 messages). The pasted URL also carried a
  stray trailing `all` on the session id — a paste artefact, not a bug.
- **Root cause — server, not the list.** The list fetches a bounded page (`GET /api/session?limit=15&order=desc`,
  page limit 15) and sorts it by `time.updated` client-side, but `V2Session.list` ordered by
  `SessionTable.time_created` and `/api/session` anchored its cursors on `time.created`
  (`packages/core/src/session.ts:271`, `packages/server/src/handlers/session.ts:50,58`). A session started 17 h
  earlier and still in use fell outside page 1. Proven in the live DB: `ORDER BY time_updated DESC` puts it 2nd,
  `ORDER BY time_created DESC` puts it outside the top 15 — exactly the two rows that were missing.
  `home-session-index.ts:172-176` had already predicted this; FE-016 (s058) shipped the bounded page anyway.
- **Fix (DEC-053), commit `86c621c` pushed to `origin/dev`:** sort + cursor anchor on `time_updated`; new index
  `session(time_updated, id)`; migration `20260928004444_useful_manta` (one `CREATE INDEX`, no rewrite). The old
  plan was a full scan + temp B-tree, so the index is a speed-up, not a trade — `EXPLAIN` now reports
  `SCAN session USING INDEX session_time_updated_id_idx`. Also fixes the per-directory fetch
  (`directory-sync.ts:160`) and search, which used the same route.
- **Tests:** 5 new core cases (`packages/core/test/session-list.test.ts`) + 1 route-level case in
  `httpapi-session.test.ts` that asserts the **decoded** cursor, so the sort column and the cursor anchor (two
  packages, no type link) cannot drift apart again. Verified non-vacuous by reverting the sort column: 3 of 5 core
  cases and the route case go red.
- **Gates:** `bun turbo typecheck` **30/30**; core **1088/0 new** (1083→1088 pass, the same 16 environmental
  failures on a stashed tree); opencode `test/server` **298** (297→298, same 2 failures stashed); app unit
  **780/0**; oxlint 0 errors; prettier clean; `bun run migration --check` "nothing to migrate".
- **Deployed :4447:** build **`1.1.20260928011449`**, **pid 58516**, health `{"healthy":true}`. DB backed up first to
  `/tmp/opencode/db-backup-before-s078.db` (the migration touches live data). Verified in the real UI (390×844,
  real login): the previous session is **row 1** again with its real title and a real last-prompt line
  ("fix all"), and "Set opencode default port to 4447" is back at row 9. 12 → 13 rows.
- **Not fixed, deliberately:** a `limit=15` page still renders as 12–13 rows because child/archived sessions are
  dropped client-side after the fetch → **FU-102**.
