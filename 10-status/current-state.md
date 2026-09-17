# Current Project State

> Snapshot of the last known state. Updated by the agent at the end of EVERY session.
> If reality differs from this file, fix it immediately (drift check).

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

- **Last updated:** 2026-09-17 (UTC) — **s047 NEW FEATURE (source, uncommitted): Archive icon on open
  titlebar session tabs.** Each open session tab in the titlebar now shows an archive `icon-button-v2`
  (`data-action="titlebar-tab-archive"`) on its trailing edge (hover-reveal). Click → `window.confirm`
  (new `common.archiveConfirm`, added to all 60 locale dicts) → on accept: `archiveHomeSession` marks the
  session archived server-side (`session.update({time:{archived}})` → Home session list filters it out via
  `!s.time?.archived`) and `notifySessionTabsRemoved` closes the open tab(s). Reuses the same plumbing as the
  home session-list archive. Verified: typecheck clean, i18n parity + archive + session-events tests pass. **Not
  committed / not built / not deployed yet** → FU-054. Details:
  `20-logs/sessions/2026-09-17_s047_titlebar-tab-archive.md`.

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
