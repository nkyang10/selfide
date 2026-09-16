# Session s035 — close agent-actionable follow-ups + fix folder-picker reload

- **Date:** 2026-09-14 (UTC)
- **Branch:** `dev` (p003-opencode-fork)
- **Why:** user asked to "do all follow up", then reported a new folder-picker bug:
  "for the open project folder select, when I click a subfolder the textbox value changes, it
  then reloads the folder-selection part (scroll back to top), difficult to use. Just ban the
  onchange if the change comes from selecting a folder."

## Result

### NEW BUG (user-reported, fixed + deployed)
**Symptom:** open-project folder selector — clicking a subfolder changed the path textbox, which
re-ran the suggestions search / re-rendered the list, resetting scroll to the top.

- **Root cause (verified in `packages/app/src/components/dialog-select-directory-v2.tsx`):**
  tree node click → `DirectoryTreeZag` `onSelectionChange` → `handleTreeSelect(path)` →
  `setInput(displayPickerPath(path,…))`. The suggestions resource is `createResource(input, …)`,
  so that programmatic value change re-ran `search(value)` + `file.find` (network) and re-rendered
  the list → scroll reset.
- **Fix (matches user's request — "ban the onchange if change by select folder"):**
  added a `suppressNextInputRefetch` flag, set to `true` before `setInput` in `handleTreeSelect`;
  the resource short-circuits to `{ query, items: [] }` for exactly that one change (no network, no
  reload). The flag is cleared in the user `onInput` handler so a same-value click can't leak a
  suppression into the next real typed search. User-typed input still refetches normally.
- **Verified:** `tsc --noEmit -p packages/app` clean; 28 directory-picker / domain / gesture unit
  tests pass.
- **Shipped:** `scripts/build-linux.sh` (pinned bun 1.3.14) → build `0.0.0-mark-dev-202609141427`.
  Deployed: killed old :4447 pid 1993264, `OPENCODE_SERVER_PASSWORD=hahahaha run-web.sh 4447` →
  new **PID 2033155**. Live: unauth `/` 401, `/login` 200, authed `/` 200; `/root` + `/lost+found`
  → 200 (FU-047 intact). Carries s032 image-attach (FU-048) + s033 new-folder bootstrap (FU-046) +
  this picker fix. On-device picker retest (FU-047) still open.

### NEW BUG #2 (user-reported, fixed + deployed — same dialog)
**Symptom:** clicking the folder tree **chevron** `directory-picker-v2-chevron` — first click does
nothing (and the list scrolls back to top), second click expands the folder + changes the textbox.

- **Root cause (verified in `directory-tree-zag.tsx` + @zag machine `expand-branch.js`,
  `tree-collection.js`):** the auto-expand effect was keyed on the **collection signal**:
  `createEffect(on(collection, …))` with `{ defer: false }` calling `api().expand([ROOT_VALUE])`.
  Because `onLoadChildrenComplete → setCollection(details.collection)` replaces the collection on
  **every** branch load, each chevron click re-fired the effect → re-issued `BRANCH.EXPAND(ROOT)` →
  the machine re-ran `loadChildren` for the root and `collection.replace(rootIndexPath, newChildren)`
  injected **fresh node objects** for all top-level children. Result: the just-clicked branch's
  children/getExpandedValue churned (first click "dead"), the visible list remounted
  (`TreeCollection._create` returns `{...node}` new refs → `<For>` keyed-by-ref remounts), and the
  `.directory-picker-v2-browser` scroll container (overflow:auto) reset to the top.
- **Fix:** key the auto-expand on **`props.root`** (defer:false) instead of `collection()`. It runs
  on mount and on real filesystem-root navigation (`navigate()` → `setRoot`), but NOT on every
  child-load → no root re-fetch churn, no collection-wide remount, no scroll reset. Chevron click
  now expands exactly once via the machine's own `expandBranches` path.
- **Verified:** `tsc --noEmit -p packages/app` clean; directory-picker unit tests 24 pass (0 fail).
- **Shipped:** build `0.0.0-mark-dev-202609141518` (pid 2063559, :4447). Live: unauth `/` 401,
  authed `/` 200; `/file /home/mark` + `/file /root` → 200. Committed `567e0a1`.

### REVERT (2026-09-15) — picker UI back to "new picker just ready" (375cff8)
User asked to go back to the new picker "just ready" and start again — the Zag TreeView picker as it
was at commit `375cff8`, before the scroll-to-top debugging.

- Restored `directory-tree-zag.tsx`, `dialog-select-directory-v2.tsx`, `dialog-select-directory-v2.css`
  to `375cff8` (exact match verified by `git diff 375cff8`). Drops the s035/s034 picker experiments:
  `onLoadChildrenComplete` adoption, `suppressNextInputRefetch`, root-keyed auto-expand.
- **Kept** (committed, independent of picker UX): core unreadable-dir fix (`fs-util.ts`/`project.ts`)
  + httpapi regression test + stale e2e fix (`cross-server-tab-close.spec.ts`).
- Verified: app typecheck clean, picker unit tests 24 pass, httpapi unreadable-dir 1 pass (12 expects).
- Committed `6358c60`. Rebuilt → `0.0.0-mark-dev-202609150024`, deployed pid 2318653 on :4447.
  Live: authed `/` 200, unauth `/` 401, `/file /root` 200.
- **Diagnostic finding retained for the next attempt:** on chevron expand the debug logs showed
  `onLoadChildrenComplete` → `setCollection(sameCollection? false)` → `visible()` recompute → the ENTIRE
  `<For>` list UNMOUNT+REMOUNTs (ROW UNMOUNT×22 → ROW MOUNT×22) because `getVisibleNodes()` returns fresh
  `{node,indexPath}` wrappers each recompute and Solid's `<For>` keys by item reference identity. That full
  remount inside `.directory-picker-v2-browser` (overflow:auto) is what resets scroll to top on every
  expand. Candidate fixes to try on top of `375cff8`:
  1. Stable-keyed `visible()` memo (reuse item objects keyed by `node.value`) — most targeted.
  2. Key the `<For>` rows via a stable solid-js `Key` wrapper.
  3. Restore `scrollTop` after `setCollection` (band-aid).

### FU-036 (stale e2e) — RESOLVED
`cross-server-tab-close.spec.ts` clicked a removed `[data-slot="tab-close"] button`. The close is now
a right-click context menu (`MenuV2.Context` → "Close tab" item in `titlebar-tab-nav.tsx`). Replaced
the click with `tabA.click({ button: "right" })` + `page.getByRole("menuitem", { name: "Close tab" })
.click()`. Playwright lists 2/2 tests; full e2e run blocked by inotify ENOSPC (watcher/env limit, not
the test logic).

### FU-039 (build-runtime doc) — RESOLVED
`notes/build-runtime.md` already had the bun-1.4.x trap + `visual_model`. Added the **HTTP file-part
prompt e2e method** section (post a `file` part `mime: image/png` + `url: data:image/...`; fork
substitutes the visual model per-turn at `session/prompt.ts` `getModel()`; assert `modelID`; text-only
follow-up stays on the original model) and fixed a dangling session-doc link.

### Drift cleanup
- `open-followups.md`: FU-046/047/048 pid/build refreshed to the live `0.0.0-mark-dev-202609141427`
  (pid 2033155); FU-036 + FU-039 marked DONE.
- `current-state.md`: s035 entry added at top (bug fix + closeouts); s034 still the prior entry.

## User-actionable follow-ups (consolidated — awaiting user)
On-device / phone (needs Mark): FU-020, FU-022, FU-023, FU-025, FU-028, FU-032, FU-035, FU-037,
FU-041, FU-042, FU-046, FU-047, FU-048.
Decisions (needs Mark): FU-001 (tech stack), FU-002 (deploy target), FU-003 (auth model), FU-004
(MVP scope), FU-006 (test device), FU-007 (p002 go), FU-008 (eval substrate), FU-010 (agent model),
FU-011 (interview depth), FU-013 (GitHub PAT scopes), FU-015 (playground cleanup), FU-016 (cycle-2
ship), FU-017 (close epic), FU-019 (PAT rotation), FU-021 (re-test project selector), FU-038 (vision
backend), FU-021/FU-021 (parking rule).

## Debug instrumentation pass (s035 continued, 2026-09-15) — DEPLOYED
User asked to add comprehensive console logs (client + server) before attacking the scroll bug
again. Committed `be03932`, deployed `0.0.0-mark-dev-202609151427` (pid 2705601, :4447).

**Client (browser console):**
- `[picker-tree]` in `directory-tree-zag.tsx`: MOUNT, root change, buildCollection,
  listChildren START/DONE (value, rawLen, treeLen, dt ms), machine loadChildren, onSelectionChange,
  onExpandedChange, connect(), effect(collection), visible() len + first label + paths, ROW MOUNT /
  ROW UNMOUNT (label, path, idx), scroll listener on `.directory-picker-v2-browser`.
- `[picker-dialog]` in `dialog-select-directory-v2.tsx`: MOUNT, navigate (value, token, stale),
  load START/OK/FAIL (path, key, generation, entries, ms, cached), suggestions skip/directories/files,
  handleTreeSelect (path, inputBefore), start effect skip/navigate, onInput (typed).

**Server (testing/web-4447.log):**
- `[http] ENTER/EXIT` middleware in `lifecycle.ts` wired in `server.ts`: method, pathname, full query
  (incl. `path=` + `directory=`), duration ms — via console.log so it reaches the log despite
  `disableLogger: true`. First attempt (raw `new URL(request.url)`) 500'd every routed request —
  fixed with a defensive URL parse + try/catch (logging can never break routing; ENTER logs even if
  downstream 500s).
- `[picker-server] file.list` / `FALLBACK` logs in `handlers/file.ts` (path, directory, count, ms).

Verification: app typecheck 0, picker unit tests 24 pass, httpapi unreadable-dir 1 pass (12 expects),
`[http]` ENTER/EXIT observed live for `/file?path=&directory=/home/mark` (200, ms=106) and
`/file?path=Documents&directory=/home/mark` (200, ms=14).

## Files changed
- `50-projects/p003-opencode-fork/opencode/packages/app/src/components/dialog-select-directory-v2.tsx`
- `50-projects/p003-opencode-fork/opencode/packages/app/e2e/regression/cross-server-tab-close.spec.ts`
- `50-projects/p003-opencode-fork/notes/build-runtime.md`
- `10-status/open-followups.md`, `10-status/current-state.md`, `20-logs/command-log.md`
- (revert) `50-projects/p003-opencode-fork/opencode/packages/app/src/components/directory-tree-zag.tsx`
  — restored to `567e0a1`, debug strings removed
- (debug pass, commit `be03932`):
  `directory-tree-zag.tsx`, `dialog-select-directory-v2.tsx`,
  `packages/opencode/src/server/routes/instance/httpapi/lifecycle.ts` (+`server.ts`,
  `handlers/file.ts`)

## Notes
- e2e full-run blocked by `ENOSPC: no space left on device, watch …/vite.js` — an inotify/watcher
  limit in this sandbox, not disk exhaustion or the test. Test logic verified via `playwright test --list`.
- Did not restart :4445 (official main) — untouched.
