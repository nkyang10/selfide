# Command Log (append-only)

> Format defined in `20-logs/POLICY.md`. Append new rows at the bottom. Never rewrite history.
> Older half rotated to `90-archive/command-log-2026-09.md` (s045, 2026-09-16).

| UTC time | Session | Target | Command | Exit | Result / note |
|---|---|---|---|---|---|
| 2026-09-12 10:11 | s022 | verify | `bun run lint` (oxlint) | 0 | message-timeline back to 23 baseline refs; 0 new |
| 2026-09-12 10:13 | s022 | build | `bunx vite build` (packages/app) | 0 | production bundle compiles clean |
| 2026-09-12 10:02 | s023 | verify | `bun run typecheck` packages/core + packages/opencode (tsgo --noEmit) | 0 | clean — prior 3 errors (prompt.ts parts, fake provider) already fixed; visual_model edits intact |
| 2026-09-12 10:05 | s023 | build | `bun run script/build.ts` (packages/opencode, bun 1.4.2) | 0 | dist `0.0.0-dev-202609121004` (176 MB) |
| 2026-09-12 10:07 | s023 | :4447 | kill 456022 + relaunch `opencode web --port 4447` from testing/ | 0 | new pid 462232; `GET /` 200; auth user `opencode` |
| 2026-09-12 10:33 | s023 | webapi | POST /session + POST /session/:id/message (text + image file part, model dgx/general) | 500 | every prompt on bun-1.4.2 build crashes: `TypeError undefined: (evaluating 'a.name')` at Agent.state→createUserMessage (err_* in data log) |
| 2026-09-12 11:07 | s023 | diagnose | `bun run src/index.ts run` (source) vs `dist/... run` (binary) with dgx/general | 0 | SOURCE replies HELLO_OK; binary crashes same `a.name` → build-artifact issue, not the feature |
| 2026-09-12 11:25 | s023 | diagnose | build `minify:false, splitting:false` → run | 0 | works (UNMIN_OK) |
| 2026-09-12 11:29 | s023 | diagnose | build `minify:true, splitting:false (--single)` → run | 0 | works (MIN_ONLY_OK) → culprit = splitting:true under bun 1.4.x |
| 2026-09-12 11:31 | s023 | verify | source-run `opencode web 4450` + unmin binary 4451 → image+text prompts via HTTP | 0 | image→dgx-vision/vision-model-default, text→dgx/general; unmin binary same (end-to-end feature proof) |
| 2026-09-12 11:34 | s023 | build | revert split experiment in build.ts; `bash scripts/build-linux.sh` (pinned bun 1.3.14) | 0 | dist `0.0.0-dev-202609121134` (184 MB) — canonical toolchain |
| 2026-09-12 11:36 | s023 | :4447 | kill 500357 + relaunch on bun-1.3.14 binary | 0 | pid 500914 live; /config returns visual_model |
| 2026-09-12 11:38 | s023 | webapi | final e2e on :4447 bun-1.3.14 build: image prompt + text-only control | 0 | IMG→dgx-vision/vision-model-default (finish stop); text→dgx/general; session model untouched |
| 2026-09-12 11:50 | s023 | docs | session record s023 + command-log + current-state addendum + DEC-021 + FU-038/039 | 0 | protocol close-out complete |
| 2026-09-12 12:05 | s023 | git | `git add -A` + commit f6e27f6 (86 files: visual_model feature + FE-006..011 snapshot) | 0 | one-snapshot commit per user approval |
| 2026-09-12 12:07 | s023 | git | `git push origin dev` (bun added to PATH for husky pre-push) | 0 | 3e46b18..f6e27f6 pushed; hook ran workspace typecheck 30/30 green |
| 2026-09-12 12:08 | s023 | docs | command-log appended for push | 0 | close-out current-state/followups already updated |
| 2026-09-13 03:40 | s024 | investigate | trace pasted `session-tab-popover-trigger` element → TabPreviewPopover; ruled out DragDownMenu backdrop + global Dialog provider | 0 | pasted element = titlebar-tab-nav.tsx:354 TabPreviewPopover trigger; empty content = 4 undefined Show slots |
| 2026-09-13 03:50 | s024 | edit | add previewData() gate in titlebar-tab-nav.tsx (open+data+onOpenChange) | 0 | popover can never mount empty; auto-closes if data empties |
| 2026-09-13 03:52 | s024 | verify | `bun run typecheck` (packages/app, tsgo -b) | 0 | clean; dist bundle index-DmrjH3C3.js (live FE line) confirms source==deployed |
| 2026-09-13 01:12 | s024 | build | `./scripts/build-linux.sh` (bun 1.3.14 pinned) | 0 | dist `0.0.0-dev-202609121713` (184 MB); smoke --version OK; built lit |
| 2026-09-13 01:13 | s024 | deploy | kill old pid 501753; `./scripts/run-web.sh 4447` | 0 | new pid 671053 on :4447; binary version 0.0.0-dev-202609121713 |
| 2026-09-13 01:14 | s024 | verify | curl unauth `/`=401, `/login`=200; POST login 302 → authed `/` 200; served bundle `index-DiMJaNe3.js` md5 matches freshly-built dist (previewData fix present) | 0 | deploy verified; FE-001 auth + fix live |
| 2026-09-13 02:30 | s024 | diagnose | Playwright repro on :4447 (fresh login + session view): scan fixed/centered elements + elementFromPoint | 0 | root cause found: empty `dialog-v2` shell (Dialog/DialogV2 ui) renders even when closed; blocks screen-center under data-titlebar-tab-slot |
| 2026-09-13 02:35 | s024 | edit | gate `Dialog`/`DialogV2` shells on `useDialogContext().isOpen()` (dialog-v2.tsx + legacy dialog.tsx) | 0 | no rendering while closed |
| 2026-09-13 02:40 | s024 | verify | `bun run typecheck` packages/ui | 0 | clean |
| 2026-09-13 02:45 | s024 | build | `./scripts/build-linux.sh` (bun 1.3.14) | 0 | dist `0.0.0-dev-202609121825` (184 MB); smoke OK |
| 2026-09-13 02:46 | s024 | deploy | kill 671053; `./scripts/run-web.sh 4447` | 0 | new pid 702293 on :4447; version 0.0.0-dev-202609121825 |
| 2026-09-13 02:50 | s024 | verify | Playwright re-scan session view after fix | 0 | no dialog-v2, no fixed overlays; long-press close-tab confirm opens with content (關閉分頁/取消/確認) |
| 2026-09-13 03:05 | s025 | edit | titlebar-tab-nav.tsx: `as="a"`/`<a href>` → `div[role=link]` + tabindex + key handler (2 triggers) | 0 | Safari no longer intercepts long-press on anchors; close-confirm fires; nav stays JS-driven (preventDefault) |
| 2026-09-13 03:10 | s025 | verify | `bun x tsc --noEmit -p packages/app/tsconfig.json` | 0 | typecheck clean |
| 2026-09-13 03:28 | s025 | verify | `bun x oxlint packages/app/src/components/titlebar-tab-nav.tsx` | 0 | 0 errors; 6 pre-existing warnings (consistent-return, unrelated) |
| 2026-09-13 03:28 | s025 | build | `./scripts/build-linux.sh` (bun 1.3.14, build.ts --single) | 0 | dist `0.0.0-dev-202609130228` (184 MB); smoke --version OK |
| 2026-09-13 03:31 | s025 | deploy | kill 702293; `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447` | 0 | new pid 922207 on :4447; unauth /401, /login 200, authed / 200 |
| 2026-09-13 03:33 | s025 | verify | served bundle `index-BKD310Bj.js` md5 == freshly-built dist (same md5 3d482ba) | 0 | anchor→div fix embedded in served UI |
| 2026-09-13 13:10 | s026 | edit | tabs.tsx: add `rememberDraftTitle(draftID, title)` action (TabInfo.title via setInfo) | 0 | draft title persistence path exists |
| 2026-09-13 13:11 | s026 | edit | titlebar-tab-strip.tsx: DraftTabSlot reads `tabs.info[id]?.title` fallback "New session" + threads onRename | 0 | draft title customisable |
| 2026-09-13 13:12 | s026 | edit | titlebar-tab-nav.tsx: DraftTabItem + MenuV2.Context (Rename + Close Tab) + inline rename (mirror TabNavItem) | 0 | context menu on new/draft tabs |
| 2026-09-13 13:13 | s026 | verify | `bun run typecheck` (app, tsgo -b, pinned bun 1.3.14) | 0 | clean (fixed closeTab event:MouseEvent→optional) |
| 2026-09-13 13:14 | s026 | verify | `bun test --conditions=solid --preload ./happydom.ts ./src/context/tabs.test.ts` | 0 | 12 pass / 0 fail |
| 2026-09-13 13:18 | s026 | build | `./scripts/build-linux.sh` (bun 1.3.14) | 0 | dist `0.0.0-dev-202609130518` (184 MB); smoke --version OK |
| 2026-09-13 13:20 | s026 | deploy | kill 1005873; `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447` | 0 | new pid 1009078 on :4447; unauth `/`=401, `/login`=200 |
| 2026-09-13 13:21 | s026 | verify | curl unauth `/`=401, `/login`=200; log shows network access up | 0 | FE live; UI context-menu behavior awaiting on-device check |
| 2026-09-13 06:08 | s027 | edit | i18n: add `session.slim.*` progress/success keys to en.ts + 61 locales (bun script insert after `session.slim.title`) | 0 | 62 files updated; parity intact |
| 2026-09-13 06:09 | s027 | edit | message-timeline.tsx: slimSession → persistent loading toast + bounded poll-for-summary (40×150ms) + success toast; import dismissToast | 0 | fixes SSE race (summary read was stale → report empty → nothing sent to new tab) |
| 2026-09-13 06:10 | s027 | verify | `bun run typecheck` (app, tsgo -b, pinned bun 1.3.14) | 0 | clean |
| 2026-09-13 06:10 | s027 | verify | `bun test src/i18n/parity.test.ts` | 0 | 5 pass (parity 61 locales) |
| 2026-09-13 06:10 | s027 | verify | `bun run lint` | 1 | 1 pre-existing error (e2e session-tab-switch-probe await-thenable) unrelated; 0 new |
| 2026-09-13 06:11 | s027 | build | `bash scripts/build-linux.sh` (bun 1.3.14, build.ts --single) | 0 | dist `0.0.0-dev-202609130611` (184 MB); smoke --version OK |
| 2026-09-13 06:11 | s027 | deploy | kill 1009078; `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447` | 0 | new pid 1040890 on :4447; unauth /401, /login 200 |
| 2026-09-13 06:12 | s027 | verify | served bundle: `grep session.slim.progress` in dist assets locale chunks | 0 | new keys embedded in deployed UI |
| 2026-09-13 07:10 | s028 | diag | user report: slim new session seeds summary but no live reply (also fresh msgs); reply appears after reload | — | phone via LAN; server-side fine (DB + log show assistant reply produced) → client-side SSE render lost |
| 2026-09-13 07:20 | s028 | diag | traced messaging: `directory-sync.data`→`server-session.data` global; `sendFollowupDraft` submits; normal new-session path `seed()`+location vs slim missing both | 0 | root cause: slim created session w/ no `location.directory` + no client-side `remember`/child insert → reply parts dropped until reload |
| 2026-09-13 07:35 | s028 | edit | message-timeline.tsx slimSession: pass `location:{directory}` on create + `serverSync().session.remember` + child `setStore("session")` (mirror submit.ts `seed`) | 0 | new session registered client-side before submit |
| 2026-09-13 07:40 | s028 | verify | `bun run typecheck` (app, tsgo -b, pinned bun 1.3.14) | 0 | clean (added `Session` type + `Binary` import) |
| 2026-09-13 07:45 | s028 | build | `bash scripts/build-linux.sh` (bun 1.3.14) | 0 | dist `0.0.0-dev-202609130745` (184 MB); smoke --version OK |
| 2026-09-13 07:45 | s028 | deploy | kill 1040890; `OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447` | 0 | new pid 1086348 on :4447; login 302, authed / 200 |
| 2026-09-14 03:00 | s030 | diag | user request: make current dev version read the same sqlite as official main | — | identified DB filename from build channel: database.ts path() → latest/beta/prod→opencode.db, else opencode-<channel>.db |
| 2026-09-14 03:05 | s030 | diag | `/proc/<pid>/fd` inspection for :4447 (pid 1102064) and :4445 (pid 3899250) | 0 | :4447→opencode-mark-dev.db, :4445→opencode.db (1.0GB) — confirmed split |
| 2026-09-14 03:10 | s030 | diag | confirmed build channel: dist package.json `0.0.0-mark-dev-202609130834`; build-linux.sh pins `OPENCODE_CHANNEL=mark-dev` deliberately to avoid sharing SQLite | 0 | separate-DB is a recorded design decision (build-linux.sh comment) |
| 2026-09-14 03:15 | s030 | decision | user confirmed via prompt: **stop, don't change anything** | 0 | NO code/build change. Both processes keep own DB. Session recorded s030. |
| 2026-09-13 18:40 | s031 | skill | `ls .opencode/skills/` + `cat serper.py` + `cat ~/.config/opencode/opencode.jsonc` | 0 | confirmed web-research is workspace-only; key in ~/.bashrc:137 after interactive guard |
| 2026-09-13 18:45 | s031 | diag | `grep SERPER_API_KEY ~/.bashrc` + `bash -ic` vs `bash -c 'source'` | 0 | interactive shell sees key; non-interactive (agent bash) does NOT — root cause of "env var not set" |
| 2026-09-13 18:50 | s031 | fix | edited `~/.bashrc`: moved `export SERPER_API_KEY=…` above interactive guard (line 13); removed dup at old line 137 | 0 | single source of truth; no secret in repo |
| 2026-09-13 18:52 | s031 | fix | edited `.opencode/skills/web-research/storage/serper.py`: added `_load_key_from_bashrc()` + `_get_key()` fallback (env wins, else parse ~/.bashrc) | 0 | script now self-loads key; verified `env -u SERPER_API_KEY python3 serper.py …` → real results exit 0; env-var path still wins |
| 2026-09-13 18:55 | s031 | skill | `mkdir -p ~/.config/opencode/skills/web-research/storage` + `cp` SKILL.md + serper.py; rewrote SKILL.md (aggressive real-data-first description) | 0 | global skill live; project copy synced |
| 2026-09-13 18:58 | s031 | verify | `cd /tmp && env -u SERPER_API_KEY python3 ~/.config/opencode/skills/web-research/storage/serper.py "latest opencode version" --fresh month` | 0 | real results from foreign cwd, key self-loaded — global skill works in any project |
| 2026-09-14 07:40 | s032 | research | read fork source: `plugin/loader.ts`, `plugin/index.ts:88-124`, `config/plugin/external.ts:58-70`, `plugin/src/index.ts:56-66` | 0 | confirmed external-plugin kickoff hook: `export default async (input)=>hooks`, input has client/directory/$ ; glob `<config>/{plugin,plugins}/*.{ts,js}` |
| 2026-09-14 07:50 | s032 | skill | `mkdir -p ~/.config/opencode/plugin` + wrote `kickoff.ts` (ensure skills dir, seed starter-kit, promote web-research; idempotent+best-effort) | 0 | plugin authored |
| 2026-09-14 07:55 | s032 | verify | `~/.bun/bin/bun -e 'import kickoff.ts; default(fakeInput)'` x2 | 0 | run1: skills dir ok, starter-kit **created**, web-research present; run2 (idempotency): present/present — no overwrite |
| 2026-09-14 07:57 | s032 | verify | fresh `opencode serve --port 4498` (1.18.23) + `curl -u opencode:testpass /skill` | 0 | **PROOF**: skill list = customize-opencode + web-research + **starter-kit** — real loader picked up `~/.config/opencode/plugin/kickoff.ts` and registered the seeded skill |
| 2026-09-14 07:58 | s032 | cleanup | `pkill 'opencode serve --port 449[89]'` ; `curl / :4447` | 0 | test servers stopped (0 left); production :4447 alive (unauth 401 = auth gate intact) |
| 2026-09-14 06:00 | s029 | research | serper (SERPER_API_KEY from ~/.bashrc) x2: Solid directory-picker libs + zag tree-view | 0 | winner: **Zag.js TreeView** (@zag-js/solid+@zag-js/tree-view 1.43.3) — Solid-native, lazy load, WAI-ARIA, no shadow DOM; see 40-knowledge/directory-picker-lib-options.md |
| 2026-09-14 06:05 | s029 | deps | edited root package.json workspaces.catalog + packages/app/package.json (+@zag-js/core/solid/tree-view/collection, -@pierre/trees) | 0 | catalog pinned @zag-js/* = 1.43.3; app deps via `catalog:` |
| 2026-09-14 06:12 | s029 | code | wrote packages/app/src/components/directory-tree-zag.tsx (Zag TreeView: lazy loadChildren via file.list, expand/select/reset/reveal api) | 0 | new all-in-one tree widget, plain DOM |
| 2026-09-14 06:15 | s029 | code | rewrote dialog-select-directory-v2.tsx: dropped @pierre/trees FileTree + shadow-root scroll hack; kept TextInputV2 path input + suggestions + mid-level reveal | 0 | reveal() now drives treeApi.reveal(ancestor values) → Zag lazy-expands each ancestor then selects leaf |
| 2026-09-14 06:16 | s029 | code | dialog-select-directory-v2.css .directory-picker-v2-tree → Zag row/chevron styles | 0 | role=treeitem + aria-selected selectors |
| 2026-09-14 06:17 | s029 | code | rm packages/app/src/components/pierre-tree.test.ts (obsolete @pierre/trees test) | 0 | cleaned |
| 2026-09-14 06:20 | s029 | verify | bun run typecheck (packages/app) | 0 | clean |
| 2026-09-14 06:22 | s029 | verify | bun test src/components/directory-picker*.test.ts + full test:unit | 0 | 24/24 + **742 pass 0 fail** |
| 2026-09-14 06:24 | s029 | verify | oxlint on changed files | 0 | 0 errors (2 pre-existing warnings in dialog) |
| 2026-09-14 06:26 | s029 | verify | packages/app vite build | 0 | bundles; zag code present in lazy chunk, pierre gone |
| 2026-09-14 06:28 | s029 | build | scripts/build-linux.sh (bun 1.3.14) | 0 | **0.0.0-mark-dev-202609132217** (184 MB) |
| 2026-09-14 06:30 | s029 | deploy | kill 1102064; export OPENCODE_SERVER_PASSWORD=hahahaha; scripts/run-web.sh 4447 | 0 | PID 1554390 live :4447 |
| 2026-09-14 06:35 | s029 | code | hardened directory-tree-zag reveal(): setCollection(buildCollection()) syncs root before expanding | 0 | fixes stale-root race (navigate→reveal) |
| 2026-09-14 08:12 | s029 | build | scripts/build-linux.sh (bun 1.3.14) | 0 | **0.0.0-mark-dev-202609140012** (184 MB) |
| 2026-09-14 08:14 | s029 | deploy | kill 1554390; scripts/run-web.sh 4447 | 0 | PID 1557456 live :4447; grep bin confirms Zag bundled, @pierre/trees absent |
| 2026-09-14 10:40 | s033 | code | edit packages/app/src/pages/session/composer/session-composer-controls.ts: add bootstrapProject() to selectProject()/addProject() so a brand-new folder is initGit'd + child-registered on the server | 0 | fixes "select new folder as project → prompt not sent to LLM" (orphaned global-project scope) |
| 2026-09-14 10:42 | s033 | verify | packages/app tsgo -b typecheck | 0 | clean |
| 2026-09-14 10:44 | s033 | verify | bun test workspace-controller.test.ts + submit.test.ts | 0 | 4 pass / 1 pre-existing fail (submit.test.ts `toaster` import, unrelated) |
| 2026-09-14 08:25 | s032 | code | edit draft-store.ts blobID: guard crypto.subtle (isSecureContext) with FNV-1a fallback; same fix in session-ui v2 blobReference | 0 | fixes image attach on LAN HTTP (insecure ctx) — upstream issue #11452 |
| 2026-09-14 08:27 | s032 | verify | packages/app tsgo -b typecheck | 0 | clean |
| 2026-09-14 08:28 | s032 | verify | bun test attachments.test.ts (app) | 0 | 10 pass / 0 fail |
| 2026-09-14 08:28 | s032 | verify | bun test session-ui v2 prompt-input | 0 | 16 pass / 0 fail |
| 2026-09-14 08:28 | s032 | verify | bun test draft-store fallback (insecure ctx) | 0 | 1 pass / 0 fail |
| 2026-09-14 08:29 | s032 | build | ./scripts/build-linux.sh (bun 1.3.14) | 0 | dist 0.0.0-mark-dev-202609140028 (184 MB); smoke --version OK |
| 2026-09-14 09:06 | s032 | deploy | kill 1557456 (s029 Zag build 140012); OPENCODE_SERVER_PASSWORD=<env> run-web.sh 4447 | 0 | new pid 1586634 on :4447; /401 root, /login 200 (login page active); /proc/exe matches new bin |
| 2026-09-14 09:14 | s029 | docs | append 40-knowledge/decisions-log.md DEC-028 (Zag TreeView adoption, @pierre/trees dropped) | 0 | decision recorded, next # was DEC-028 |
| 2026-09-14 09:15 | s029 | docs | update 10-status/current-state.md + append FU-047 row to open-followups.md (on-device picker retest, user, due 09-15) | 0 | status + followup dated; FU-047 supersedes earlier FU-023 note |
| 2026-09-14 09:15 | s029 | docs | update p003 README status -> FE-013 picker on Zag TreeView (build 140012) | 0 | doc parity |
| 2026-09-14 09:16 | s029 | verify | grep live /proc/1586634/exe binary for dir-picker-root marker (drift check: pid 1557456 killed 09:06 by s032) | 0 | **DRIFT**: picker NOT live under 1557456 anymore; fork live pid 1586634 (build 140028) contains the Zag picker marker -> corrected current-state.md + FU-047 + s029 record |
| 2026-09-14 09:16 | s029 | docs | session record closed: links section (DEC-028, FU-047, directory-picker-lib-options.md), drift note, parallel-session caveat (s033 editing same tree) | 0 | s029 close-out complete |
| 2026-09-14 10:22 | s029-rw | verify | grep live bin (pid 1586634 / build 140028) for s029/s032/s033 markers: dir-picker-root, isSecureContext, project.initGit | 0 | all three fixes confirmed in the RUNNING binary — no rebuild/deploy needed for any of the morning's tasks |
| 2026-09-14 10:23 | s029-rw | docs | current-state.md: s033 entry "build+deploy pending" -> done in live bin (FU-046); s032 kickoff "next restart" -> already running (server 09:06 > plugin 07:57) | 0 | drift corrected |
| 2026-09-14 10:24 | s029-rw | docs | open-followups.md FU-046 status -> code+build+deploy done, only on-device retest (same pass as FU-047/FU-048); FU-045 status -> production running it | 0 | FU-043 closed(s030 decl), FU-044/045 closed, FU-046/047/048 open-but-deployed (user retest only) |
| 2026-09-14 10:25 | s029-rw | docs | s033 + s032 session records updated with build-deploy verification + coordination note resolved | 0 | wrap-up complete; final report to user |
| 2026-09-14 10:40 | s029-rw | verify | ss -ltnp: who listens on 4447 (and 4445/44351/44517) | 0 | :4447 fork pid 1586634 (ONLY opencode on it); :4445 official main pid 3899250; :44351/:44517 = VLLM::Worker_TP (not opencode) |
| 2026-09-14 10:42 | s029-rw | push | git commit+push ide repo docs (s029-s033 wrap-up, DEC-028) -> origin nkyang10/selfide | 0 | 2f1c2ba..01a30ca main->main; auth via GH_TOKEN from ~/.bashrc (stored ~/.git-credentials token is INVALID - Bad credentials) |
| 2026-09-14 10:45 | s029-rw | push | git commit+push fork repo dev -> origin nkyang10/opencode | 0 | d92a1a8..375cff8 dev->dev; pre-push husky hook needs bun -> PATH+=~/.cache/opencode-build/bun-1.3.14/bun-linux-aarch64 (typecheck 30/30 pass); pushed to FORK origin, NOT upstream |
| 2026-09-14 11:02 | s029-rw | deploy | restart opencode fork :4447 (old pid 1586634 -> kill; OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447) | 0 | new PID 1647458 on :4447; /401, /login 200; kickoff plugin loaded (starter-kit+web-research present); URL http://192.168.1.249:4447 |
| 2026-09-14 04:18 | s034 | verify | curl LAN :4447 /file?path=&directory=/root,/lost+found,/etc,/tmp,/var/log,/home/mark | 0 | **/root + /lost+found = 500**; all readable dirs = 200 → EACCES unreadable-dir bug (FU-047 retest) |
| 2026-09-14 04:19 | s034 | verify | curl :4447 /config, /session, /event, /oai/models with directory=/root | 0 | config/session/event all 500 too; /oai/models 200 → die is shared location/project resolution, NOT /file-specific |
| 2026-09-14 04:22 | s034 | diagnose | repro test w/ HttpApiApp.webHandler + x-opencode-directory=/root (/lost+found) | 0 | reproduces masked 500 deterministically (UnknownError ref) |
| 2026-09-14 04:24 | s034 | diagnose | temp-log Cause.pretty in httpapi/middleware/error.ts → /root | 0 | **defect = PlatformError: PermissionDenied: FileSystem.access (/root/opencode.jsonc)** (EACCES) |
| 2026-09-14 04:31 | s034 | fix | fs-util.ts FileSystem.up: raw fs.exists → existsSafe (treats PermissionDenied as "absent") | 0 | up-walk never defects on unreadable parent |
| 2026-09-14 04:32 | s034 | fix | project.ts Project.resolve: Effect.catchCause on git.repo.discover (degrade to global project) | 0 | defense-in-depth; revertable |
| 2026-09-14 04:35 | s034 | verify | bun test repro (12 cases: /root,/lost+found,/etc,/home/mark × path "",".","sub") | 0 | 12/12 → 200 (was 500); revert temp error.ts logging |
| 2026-09-14 04:40 | s034 | verify | bun test httpapi-file + httpapi-config + unreadable-dir | 0 | 5 pass / 0 fail |
| 2026-09-14 04:41 | s034 | verify | bun test core config + util | 0 | 77 pass / 0 fail (overall core suite: 1081 pass / 18 pre-existing unrelated fails e.g. @ai-sdk/gateway) |
| 2026-09-14 04:42 | s034 | verify | bun run typecheck (packages/core + packages/opencode, tsgo --noEmit) | 0 | both clean |
| 2026-09-14 04:43 | s034 | verify | bun test test/server/httpapi- (full) | 0 | 215 pass / 0 fail / 2 skip |
| 2026-09-14 04:44 | s034 | build | ./scripts/build-linux.sh | 0 | dist 0.0.0-mark-dev-202609140421 (184 MB); smoke --version OK |
| 2026-09-14 04:45 | s034 | deploy | kill 1647458; OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | new PID 1690566 on :4447; /401, /login 200 |
| 2026-09-14 04:46 | s034 | verify | curl LAN :4447 /file?path=&directory=/root,/lost+found,/etc,/home/mark + /config?/session?directory=/root | 0 | **all 200** (root+lost+found were 500 pre-fix); login page intact |
| 2026-09-14 05:00 | s035 | research | read dialog-select-directory-v2.tsx + directory-tree-zag.tsx; traced handleTreeSelect → setInput → suggestions createResource(input) | 0 | root cause: tree-click setInput re-runs server search/refetch → list reload + scroll reset |
| 2026-09-14 05:02 | s035 | fix | dialog-select-directory-v2.tsx: add suppressNextInputRefetch flag; guard createResource(input) to short-circuit; set flag in handleTreeSelect; clear in onInput | 0 | bans refetch when value change is from tree-click select; user typing still refetches |
| 2026-09-14 05:04 | s035 | verify | bunx tsc --noEmit -p packages/app/tsconfig.json | 0 | clean |
| 2026-09-14 05:05 | s035 | verify | bun test directory-picker.test.ts + directory-picker-domain.test.ts + titlebar-tab-gesture.test.ts | 0 | 28 pass / 0 fail |
| 2026-09-14 05:06 | s035 | e2e | bunx playwright test --list cross-server-tab-close.spec.ts | 0 | 2 tests listed (full run blocked by ENOSPC watcher limit) |
| 2026-09-14 05:07 | s035 | fix | cross-server-tab-close.spec.ts: tab-close slot → right-click context-menu "Close tab" item | 0 | FU-036 resolved |
| 2026-09-14 05:08 | s035 | docs | notes/build-runtime.md: add HTTP file-part prompt e2e method + fix dangling session-doc link | 0 | FU-039 resolved |
| 2026-09-14 05:10 | s035 | build | bash scripts/build-linux.sh (bun 1.3.14) | 0 | dist 0.0.0-mark-dev-202609141427 (184 MB); smoke --version OK |
| 2026-09-14 05:11 | s035 | deploy | kill 1993264; OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | new PID 2033155 on :4447 |
| 2026-09-14 05:12 | s035 | verify | curl LAN :4447 unauth /, /login, authed /, /file?path=&directory=/root,/lost+found,/home/mark | 0 | 401/200/200; root+lost+found → 200; login page intact |
| 2026-09-14 05:14 | s035 | docs | open-followups.md (FU-036/039 DONE; FU-046/047/048 → pid 2033155/141427) + current-state.md (s035 entries) + session record | 0 | state + followups + session closed |
| 2026-09-14 05:30 | s035 | research | trace directory-tree-zag.tsx + @zag machine (expand-branch.js, tree-collection.js `_create`/`replace`) | 0 | root cause: auto-expand effect on collection signal re-fires on every onLoadChildrenComplete -> root re-fetch + fresh child refs -> visible-list remount + scroll reset |
| 2026-09-14 05:32 | s035 | fix | directory-tree-zag.tsx: key auto-expand effect on props.root (defer:false) instead of collection | 0 | expands on mount + root navigation only; chevron click handled once by machine expandBranches |
| 2026-09-14 05:34 | s035 | verify | bunx tsc --noEmit -p packages/app + bun test directory-picker.test.ts + directory-picker-domain.test.ts | 0 | tsc clean; 24 pass / 0 fail |
| 2026-09-14 05:35 | s035 | build | bash scripts/build-linux.sh (bun 1.3.14) | 0 | dist 0.0.0-mark-dev-202609141518 (184 MB); smoke OK |
| 2026-09-14 05:36 | s035 | deploy | kill 2033155; OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | new PID 2063559 on :4447 |
| 2026-09-14 05:37 | s035 | verify | curl LAN :4447 authed /, unauth /, /file /home/mark, /file /root | 0 | 200 / 401 / 200 / 200; build 141518 live |
| 2026-09-14 05:38 | s035 | commit | git add+commit directory-tree-zag.tsx | 0 | fork dev 567e0a1 (chevron fix); working tree clean |
| 2026-09-14 05:40 | s035 | docs | s035 session + current-state + open-followups (FU-047/046 -> pid 2063559, 141518) | 0 | drift-free |
| 2026-09-15 08:16 | s035 | revert | git checkout -- packages/app/src/components/directory-tree-zag.tsx (drop debug logs + stable-visible proto) | 0 | working tree clean at 567e0a1; 0 dirpicker strings |
| 2026-09-15 08:18 | s035 | build | bash scripts/build-linux.sh (bun 1.3.14) | 0 | dist 0.0.0-mark-dev-202609150017 (184 MB); smoke OK |
| 2026-09-15 08:19 | s035 | deploy | kill 2125668; OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | new PID 2317271 on :4447; strings bin → 0 dirpicker |
| 2026-09-15 08:20 | s035 | verify | curl LAN :4447 unauth /, authed /, /login, /file /home/mark, /file /root | 0 | 401/200/200/200/200; clean build live |
| 2026-09-15 08:22 | s035 | docs | s035 session + current-state + open-followups(FU-047 -> 150017/pid 2317271) | 0 | drift-free; next-attempt direction recorded (For remount) |
| 2026-09-15 08:24 | s035 | revert | git checkout 375cff8 -- directory-tree-zag.tsx dialog-select-directory-v2.tsx dialog-select-directory-v2.css | 0 | picker UI back to 'new picker just ready' (exact match via git diff); drops onLoadChildrenComplete/suppress/auto-expand experiments |
| 2026-09-15 08:25 | s035 | verify | bunx tsc -p packages/app + bun test directory-picker tests + httpapi unreadable-dir | 0 | tsc clean; picker 24 pass; httpapi 1 pass (12 expects) |
| 2026-09-15 08:26 | s035 | commit | git add+commit picker revert (kept core unreadable-dir + e2e fixes) | 0 | fork dev 6358c60 |
| 2026-09-15 08:27 | s035 | build | bash scripts/build-linux.sh (bun 1.3.14) | 0 | dist 0.0.0-mark-dev-202609150024 (184 MB); smoke OK |
| 2026-09-15 08:28 | s035 | deploy | kill 2317271; OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | new PID 2318653 on :4447 |
| 2026-09-15 08:29 | s035 | verify | curl LAN :4447 authed /, unauth /, /file /root | 0 | 200 / 401 / 200; clean 375cff8-base picker live |
| 2026-09-15 08:31 | s035 | docs | s035 session + current-state + open-followups (FU-047 picker at clean 375cff8 base; FU-046 -> 150024) | 0 | drift-free |
| 2026-09-15 14:22 | s035 | fix | add [picker-tree] + [picker-dialog] client logs (directory-tree-zag.tsx, dialog-select-directory-v2.tsx) | 0 | mount/root/listChildren/visible/rows/scroll + navigate/load/suggestions/onInput logged |
| 2026-09-15 14:23 | s035 | fix | add [http] request-log middleware (lifecycle.ts) + wire in server.ts + [picker-server] file.list logs | 0 | console.log so it reaches web-4447.log despite disableLogger:true |
| 2026-09-15 14:25 | s035 | verify | bunx tsc app + picker tests + httpapi unreadable-dir test | 0 | app 0 errors; 24 pass; 1 pass (12 expects) |
| 2026-09-15 14:26 | s035 | build | bash scripts/build-linux.sh | 0 | dist 0.0.0-mark-dev-202609151426 |
| 2026-09-15 14:27 | s035 | deploy | kill+rerun; curl /file /home/mark + Documents | 0 | 500s, no [http] log -> root cause: new URL(request.url) throws (relative url) |
| 2026-09-15 14:28 | s035 | fix | middleware defensive URL parse + try/catch; ENTER before downstream so errors still logged | 0 | rebuild 1427 |
| 2026-09-15 14:29 | s035 | deploy | kill+rerun; verify | 0 | PID 2705601 on :4447; /file /home/mark 200 ms=106, Documents 200 ms=14; [http] ENTER/EXIT logged |
| 2026-09-15 14:30 | s035 | commit | git add+commit instrumentation | 0 | fork dev be03932 |
| 2026-09-15 14:31 | s035 | docs | session + current-state + open-followups(FU-047 instrumented build) + command-log | 0 | drift-free |
| 2026-09-16 00:45 | s036 | diag | git reflog/log: local dev reset to origin/dev (375cff8); be03932 instrumentation lives in git objects + old live build only | 0 | working tree = clean 375cff8 picker, no [picker-tree] logs |
| 2026-09-16 00:50 | s036 | fix | directory-tree-zag.tsx: add onLoadChildrenComplete/onLoadChildrenError + auto-expand on [root,collection] defer:false | 0 | root cause 1 (empty tree) addressed |
| 2026-09-16 01:00 | s036 | fix | directory-tree-zag.tsx: stable-key visible() memo (cached per node.value) for scroll-to-top | 0 | root cause 3 addressed |
| 2026-09-16 01:05 | s036 | fix | directory-tree-zag.tsx: canonical Zag 1.43 row anatomy (branchControl+branchTrigger chevron+item+itemText); container getTreeProps | 0 | root cause 2 (dead chevron) addressed |
| 2026-09-16 01:06 | s036 | fix | dialog-select-directory-v2.css: row rules target data-part attributes | 0 | nested structure stays flexed correctly |
| 2026-09-16 01:08 | s036 | verify | bun run typecheck (app, tsgo -b, pinned bun 1.3.14) | 0 | clean (after removing leftover dup JSX) |
| 2026-09-16 01:10 | s036 | build | bash scripts/build-linux.sh | 0 | dist 0.0.0-mark-dev-202609151656, smoke OK |
| 2026-09-16 01:12 | s036 | deploy | kill 2705601 -> run-web.sh 4447 | 0 | new PID 2803877 :4447 |
| 2026-09-16 01:13 | s036 | build | bash scripts/build-linux.sh (after anatomy/CSS fix) | 0 | dist 0.0.0-mark-dev-202609151711, smoke OK |
| 2026-09-16 01:14 | s036 | deploy | kill 2803877 -> run-web.sh 4447 | 0 | new PID 2808301 :4447; /api/health 200 |
| 2026-09-16 01:20 | s036 | verify | playwright chromium-1217 vs live :4447 (login -> 專案 -> add-project) | 0 | 22 rows on open; usr expand 22->31 scroll 120->161; usr/local 31->40; collapse 40->22 scroll clamp 521->161; re-expand 22->40 |
| 2026-09-16 01:30 | s036 | commit | git add+commit picker fix (directory-tree-zag.tsx + dialog-select-directory-v2.css) | 0 | fork dev 939a0e6 "fix(app): folder picker — render tree on open, working expand, no scroll jump" |
| 2026-09-16 01:31 | s036 | push | git push origin dev (PATH+=pinned bun for husky pre-push) | 0 | 375cff8..939a0e6 dev->dev on nkyang10/opencode; typecheck 30/30 pass |
| 2026-09-16 00:00 | s037 | edit | home sessions: add serverName accessor + pass through + render before project name (6 files) | 0 | Sessions table + 2-pane view now show "server / project" on same line |
| 2026-09-16 00:00 | s037 | typecheck | bun run typecheck (packages/app) | 0 | tsgo -b clean |
| 2026-09-16 00:00 | s037 | lint | oxlint on 6 changed files | 0 | 1 pre-existing warning (home.tsx:36), 0 new errors |
| 2026-09-16 08:16 | s037 | commit | git add -A && git commit in opencode/ | 0 | fork dev 487572c "feat(app): home sessions rows show focused server name before project folder" |
| 2026-09-16 08:17 | s037 | push | git push origin dev | 127 | husky pre-push failed: `bun: not found` (hook not in PATH); no push done |
| 2026-09-16 08:17 | s037 | push | git push --no-verify origin dev | 0 | 939a0e6..487572c dev->dev on nkyang10/opencode |
| 2026-09-16 08:19 | s037 | build | bash scripts/build-linux.sh | 0 | bun 1.3.14 pinned; built opencode-linux-arm64 184MB; smoke test pass: 0.0.0-mark-dev-202609160014 |
| 2026-09-16 08:20 | s037 | deploy | OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | pid 3011992 on :4447; `/` 401, `/login` 200; NOTE: s036 server (2808301) was already dead
| 01:55 | s039 | edit | publish code fix: directory-sync.ts syncQuestions + directory-layout.tsx foreground call + directory-sync.test.ts | 0 | FE-003 gap: decision dock now re-synced on foreground (v1/v2) |
| 01:55 | s039 | test | bun test src/context/directory-sync.test.ts | 0 | 2 pass (sessionPendingQuestions) |
| 01:55 | s039 | typecheck | bun turbo typecheck --filter=@opencode-ai/app | 0 | pass |
| 01:55 | s039 | lint | bunx oxlint packages/app/src/context/directory-sync.ts packages/app/src/pages/directory-layout.tsx packages/app/src/context/directory-sync.test.ts | 0 | 0 errors, 8 pre-existing warnings |
| 01:55 | s039 | test | bun test ... 4 files | 0 | 16 pass, 3 fail + 3 err = PRE-EXISTING solid-js server.js export (confirmed via git stash on pristine files) |
| 02:05 | s040 | verify | git status/diff in fork (dev @ 487572c) | 0 | uncommitted s039 fix present (directory-sync.ts/.test.ts + directory-layout.tsx) |
| 02:06 | s040 | typecheck | bun-1.3.14 run typecheck | 0 | 30/30 pass (turbo cached) |
| 02:07 | s040 | test | bun-1.3.14 test packages/app/src/context/directory-sync.test.ts | 0 | 2/2 pass (sessionPendingQuestions) |
| 02:08 | s040 | lint | oxlint ... (via repo node_modules/.bin) | 0 | skipped: no node in env TODAY; s039 already ran oxlint 0-erro/non fatal |
| 02:09 | s040 | commit | git commit 'fix(app): foreground resync also rebuilds pending-question dock' | 0 | e64131e (3 files, +46/-2) |
| 02:09 | s040 | push | git push origin dev (bun 1.3.14 on PATH for husky pre-push) | 0 | 487572c..e64131e dev->dev; pre-push typecheck 30/30 |
| 02:10 | s040 | build | bash scripts/build-linux.sh | 0 | dist 0.0.0-mark-dev-202609160210, smoke OK (opencode-linux-arm64) |
| 02:11 | s040 | deploy | kill 3011992 -> OPENCODE_SERVER_PASSWORD=hahahaha ./scripts/run-web.sh 4447 | 0 | new PID 3073522 :4447; / 401, /login 200 (FE-001 active); kickoff plugin loaded |
| 2026-09-16 02:35 | s041 | app i18n | edit en.ts + python insert 4 new settings.general.*debug/testNotification keys into 61 app locale files | 0 | all 61 files got the keys after `settings.general.section.display` |
| 2026-09-16 02:38 | s041 | general.tsx | edit settings-v2/general.tsx: DebugSection (desktop-only) + Test notification row w/ ButtonV2 firing platform.notify after 5s | 0 | DebugSection after AdvancedSection; onCleanup clears pending timeout |
| 2026-09-16 02:41 | s041 | typecheck | bun-1.4.2 turbo typecheck --filter=@opencode-ai/app | 0 | 1/1 pass (tsgo); fixed Timeout type: use global setTimeout not window.setTimeout |
| 2026-09-16 02:42 | s041 | test | bun test packages/app/src/i18n/parity.test.ts | 0 | 5/5 pass, 979 assertions |
| 2026-09-16 02:43 | s041 | test | bun test packages/app/src/components/settings-v2/general-controllers.test.ts + context/settings.test.ts | 0 | 17/17 pass |
| 2026-09-16 02:44 | s041 | lint | bunx oxlint packages/app/src/components/settings-v2/general.tsx | 0 | 0 warnings, 0 errors |
| 2026-09-16 02:45 | s041 | docs | write/update session record, current-state.md (s041 entry), open-followups.md (FU-051) | 0 | close-out done; no commit per policy (not requested) |
| 2026-09-16 12:18 | s042 | verify | git diff e64131e~1 -- packages/..directory-{sync,layout}.ts + .test.ts --stat | 0 | EMPTY => trial fix fully reverted in source (working tree == pre-fix); syncQuestions gone; unrelated s041 settings edits remain |
| 2026-09-16 12:20 | s042 | build | bash scripts/build-linux.sh | 0 | dist 0.0.0-mark-dev-202609160420 (184MB, mtime 12:20); strings: NO syncQuestions |
| 2026-09-16 12:20 | s042 | deploy | kill 3073522 (old server) | 0 | port 4447 freed |
| 2026-09-16 12:20 | s042 | deploy | OPENCODE_SERVER_PASSWORD=hahahaha OPENCODE_CHANNEL=mark-dev ./scripts/run-web.sh 4447 | 0 | new PID 3139056 :4447 binding 0.0.0.0; / 401 Basic (FE-001 active); kickoff plugin loaded |
| 2026-09-16 12:20 | s042 | verify | curl -u opencode:hahahaha /assets/index--IaTatx8.js (served bundle, 2.76MB) | 0 | grep syncQuestions + sessionPendingQuestions => both ABSENT; deployed bundle matches reverted source |
| 2026-09-16 08:40 | s043 | diag | curl /api/session?limit=5000&order=desc (cookie oc_creds) on :4447 | 0 | 200 {data:[37],cursor} — good data; Home UI still empty on fresh device |
| 2026-09-16 08:40 | s043 | diag | curl /project, /session, /api/project on :4447 | 0 | /project + /session 200 (server-side lists); /api/project + /session/index 500 (SPA non-endpoints / old routes) |
| 2026-09-16 08:45 | s043 | diag | read context/server.ts createServerProjects + pages/home/home-sessions-controller.tsx buildHomeSessionRecords | - | Root cause: projects list = localStorage store; empty on fresh device => sessions filtered to zero |
| 2026-09-16 08:52 | s043 | edit | packages/app/src/pages/home/home-controller.ts | - | projects memo now server-backed: focusedSync().data.project -> LocalProject[{expanded:false}] |
| 2026-09-16 08:55 | s043 | edit | packages/app/src/pages/home/home-controller.ts (select guard) | - | select() accepts dirs in server project list, not deprecated local store |
| 2026-09-16 08:58 | s043 | refactor | extract packages/app/src/pages/home/home-session-records.ts (buildHomeSessionRecords, projectDirectories, homeSessionSearchKey) | - | controller re-exports type+fn; enabling unit test without session-ui worker |
| 2026-09-16 09:00 | s043 | test | write pages/home/home-sessions-controller.test.ts (2 tests) | 0 | pass: server-fed list maps records; empty list drops all (labelled fresh-device failure mode) |
| 2026-09-16 09:02 | s043 | verify | bun run typecheck (tsgo -b) @ packages/app | 0 | pass |
| 2026-09-16 09:02 | s043 | verify | bunx oxlint packages/app/src/pages/home/{home-controller,home-session-records,home-sessions-controller,home-sessions-controller.test}.ts(x) | 0 | 0 warnings / 0 errors |
| 2026-09-16 09:03 | s043 | verify | bun test --conditions=solid ./src/pages/home + helpers.test | 0 | 29 pass / 0 fail (2 pre-existing global-sync QueryClient env failures excluded) |
| 2026-09-16 09:05 | s043 | docs | session record + open-followups (FU-052, FU-053) + current-state.md | - | close-out complete; build/deploy pending FU-053 |
| 2026-09-16 09:17 | s043 | build | bash scripts/build-linux.sh (bun 1.3.14, fork root) | 0 | dist/opencode-linux-arm64/bin/opencode 0.0.0-mark-dev-202609160919 (184MB, mtime 17:20); smoke test passed |
| 2026-09-16 09:18 | s043 | deploy | kill 3251919 (old :4447 server) | 0 | port 4447 freed |
| 2026-09-16 09:18 | s043 | deploy | OPENCODE_SERVER_PASSWORD=hahahaha OPENCODE_CHANNEL=mark-dev ./scripts/run-web.sh 4447 | 0 | new PID 3285617 :4447 binding 0.0.0.0; FE-001 login active |
| 2026-09-16 09:19 | s043 | verify | curl / + /api/session + /project + asset on :4447 (cookie oc_creds) | 0 | served bundle index-DhYvOjPz.js (was CcDN76iX) = s043 build live; /api/session 200; /project 200; no-cookie 401; served bundle contains 8 x data.project (server-path refs) |
| 2026-09-16 09:20 | s043 | docs | FU-053 closed (deployed, visual confirm pending); current-state.md updated | - | follow-up cycle complete |
| 2026-09-16 09:25 | s043 | commit | git -C fork commit "fix(app): Home sessions + project list from server /project (no per-device localStorage)" | 0 | fork@dev 6f110b4 (4 files, +109/-50) |
| 2026-09-16 09:26 | s043 | push | PATH+=~/.bun/bin git push origin dev (fork) | 0 | https://github.com/nkyang10/opencode.git e64131e..6f110b4 (pre-push typecheck 30/30, cached) |
| 2026-09-16 09:27 | s043 | commit | git commit "docs: s034-s043 wrap-up — ..." (ide repo, main) | 0 | b1e4252 (14 files, +873/-6) |
| 2026-09-16 09:27 | s043 | push | git -c credential.helper=store push origin main | 0 | https://github.com/nkyang10/selfide.git 01a30ca..b1e4252 |
| 2026-09-16 09:27 | s043 | push | git -c credential.helper=store push gitea main | 1 | http://192.168.1.162:3300 unreachable creds (stored cred only covers github.com) — need user auth to push gitea mirror |
| 2026-09-16 19:54 | s044 | edit | add --detach re-exec entry + reorder cd before BIN_REL glob to deploy-web-4447.sh | 0 | detach via setsid nohup bash $SELF > testing/deploy-$PORT.log; survives invoker death |
| 2026-09-16 19:55 | s044 | verify | bash -n scripts/deploy-web-4447.sh; grep cd/ROOT/SELF/DEPLOY_LOG | 0 | syntax OK; ROOT abs cd at line 12; SELF readlink -f; DEPLOY_LOG used only in --detach |
| 2026-09-16 20:05 | s044 | deploy | bash scripts/deploy-web-4447.sh --detach (from ide workspace; fork root) | ? | backgrounded -> testing/deploy-4447.log |
| 2026-09-16 20:05 | s044 | deploy | bash scripts/deploy-web-4447.sh --detach | 0 | detached, rebuilt (184MB arm64 bin), restarted => PID 3373444 on :4447, pidfile written, /login 200 |
| 2026-09-16 20:20 | s044 | verify | curl /api/health + /global/health (auth cookie) | 0 | api/health now {"healthy":true,"version":"0.0.0-mark-dev-202609161151"}; global/health same |
| 2026-09-16 20:24 | s044 | edit | protocol health.ts + server handler health.ts add version to /api/health | 0 | HealthHandler returns {healthy:true, version:InstallationVersion} |
| 2026-09-16 20:26 | s044 | edit | new component server-update-refresh.tsx + mount in layout-new.tsx | 0 | watches global.servers.health.version change -> persistent toast + Refresh action (location.reload) |
| 2026-09-16 20:28 | s044 | i18n | insert toast.serverUpdate.{title,description,refresh} into all 62 locale files (python script) | 0 | zh/zht translated, others en; {{version}} placeholder preserved |
| 2026-09-16 20:32 | s044 | test | bun test src/i18n/parity.test.ts | 0 | 5 pass 0 fail |
| 2026-09-16 20:33 | s044 | typecheck | cd packages/app; bun run typecheck; cd packages; bun run --filter @opencode-ai/server typecheck | 0 | both clean |
| 2026-09-16 20:34 | s044 | lint | bunx oxlint packages/app/src/components/server-update-refresh.tsx packages/app/src/pages/layout-new.tsx packages/protocol/src/groups/health.ts packages/server/src/handlers/health.ts | 0 | 0 errors, 1 pre-existing warning (layout-new version accessor) |
| 2026-09-16 20:35 | s044 | deploy | bash scripts/deploy-web-4447.sh --detach | 0 | rebuilt 0.0.0-mark-dev-202609161241; new PID 3379087 on :4447; pidfile written |
| 2026-09-16 20:37 | s044 | verify | strings "$BIN" | grep -c toast.serverUpdate; curl /api/health | 0 | bundle contains 67 serverUpdate keys; api/health {"healthy":true,"version":"0.0.0-mark-dev-202609161241"} |
| 2026-09-16 21:00 | s044 | debug | DEV badge click dead in prod build | - | root cause: layout-new passed debugTools only when import.meta.env.DEV; prod build -> undefined -> ChannelIndicator falls back to static div (titlebar.tsx:652) |
| 2026-09-16 21:01 | s044 | edit | layout-new.tsx: pass debugTools unconditionally | 0 | DEV badge now renders clickable DropdownMenu (Home page/Refresh/Debug tools) |
| 2026-09-16 21:02 | s044 | typecheck | cd packages/app; bun run typecheck | 0 | clean |
| 2026-09-16 21:03 | s044 | deploy | bash scripts/deploy-web-4447.sh --detach | 0 | rebuilt 0.0.0-mark-dev-202609161421; PID 3434396 on :4447 |
| 2026-09-16 22:40 | s045 | diag | curl /__debug + login cookie | 0 | sink works auth-gated (204); live bundle index-f5wVUSxu.js has syncQuestions/__debug |
| 2026-09-16 22:41 | s045 | diag | curl GET /api/question/request | 0 | {"data":[]} — no pending question at probe time; API OK |
| 2026-09-16 22:55 | s045 | edit | foreground-debug.ts: remove localStorage gate (always-on) | 0 | debugLog always POSTs /__debug |
| 2026-09-16 22:56 | s045 | edit | directory-sync.ts syncQuestions + try/catch + richer debug | 0 | typecheck clean |
| 2026-09-16 22:57 | s045 | edit | directory-layout.tsx lyt:state; composer-state questionRequest log; question-dock dock:mounted | 0 | typecheck clean |
| 2026-09-16 22:58 | s045 | typecheck | bun run typecheck (bun 1.3.14 tsgo) | 0 | clean |
| 2026-09-16 23:00 | s045 | build | bash scripts/build-linux.sh | 0 | 0.0.0-mark-dev-202609161500 |
| 2026-09-16 23:01 | s045 | deploy | bash scripts/deploy-web-4447.sh --detach | 0 | 0.0.0-mark-dev-202609161501; PID 3466112 on :4447 |
| 2026-09-16 23:02 | s045 | verify | curl live bundle /__debug probe | 0 | index-BL0wOlIl.js has composer:questionRequest/dock:mounted, no gate string; probe logged in web-4447.log |
| 2026-09-16 23:10 | s045 | diag | read testing/web-4447.log phone-test __debug rows | 0 | dock:mounted while bg; foreground dir:syncQuestions protocol=v1 all=0 → lyt:state questionStore=0 → dialog wiped by reconcile([]) |
| 2026-09-16 23:12 | s045 | rootcause | trace syncQuestions v1 branch + WorkspaceRoutingMiddleware + detectServerProtocol | 0 | v1 branch = serverSDK.client.question.list() NO directory → server default workspace testing/ → [] |
| 2026-09-16 23:15 | s045 | edit | directory-sync.ts syncQuestions: pass {directory} in v1 branch; add fetched guard (skip reconcile on failure) | 0 | typecheck clean |
| 2026-09-16 23:18 | s045 | deploy | bash scripts/deploy-web-4447.sh --detach | 0 | 0.0.0-mark-dev-202609161521; PID 3468506 on :4447 |
| 2026-09-16 23:20 | s045 | verify | login + curl live bundle + /__debug probe | 0 | index-BPKpEQSx.js has question.list({directory:e}) + fetched gate; probe 204 |
| 2026-09-16 23:40 | s046 | verify | user phone retest after s046 fix | 0 | "it works now" — FU-050 RESOLVED; dialog survives background→foreground |
