# s069 — FE-020: every folder you open is a project (plain non-git folders in the project list)

- **Date:** 2026-09-26 (UTC)
- **Owner:** agent (user: mark)
- **Trigger:** user — "opencode fork project, project folder selector, after selected and dismiss dialog, the path
  seems not propagate return to outside" → then "treat this as a new enhancement and improve"
- **Baseline:** fork `dev` = `71c73a0` (= `origin/dev`, clean tree). **Note:** a parallel workspace process committed
  and pushed s068's work (`71c73a0`) *during* this session's diagnosis — stage only this session's files.
- **Outcome:** (filled at close-out)

## The bug the user hit

Home ▸ Projects ▸ **Add project / 新增專案** → folder picker → pick a folder → confirm → the dialog closes and
**nothing outside changes**. Reproduced live on :4447 (build `1.1.20260926101720`, pid 2997423) with Playwright.

### Root cause

opencode identifies a project by **git identity**, not by folder path
(`packages/core/src/project.ts:109` `ProjectV2.resolve`):

```
const repo = yield* git.repo.discover(input)
if (!repo) return { id: ID.global, directory: path.parse(input).root, vcs: undefined }
const id = remote(repo) ?? previous ?? root(repo)   // remote-URL hash -> cached id -> FIRST ROOT COMMIT sha
```

`packages/opencode/src/project/project.ts:215` (`fromDirectory`) then upserts a row keyed by that id, so **every
non-repo folder collapses into the single `global` row** (whose `worktree` is the placeholder `"/"`), and
`saveProjectDirectory` (`:199`) returns early for the global id, so the folder is recorded **nowhere**.

The Home project list is **server truth** since s043 (`home-controller.ts:28` `focusedSync().data.project`), so a
non-git folder has no row to render — the picker's result silently disappears. Git folders work: a prepared folder
(`/tmp/opencode/t-git`, one commit) was registered instantly as its own project.

### Measured matrix (live :4447)

| picked folder | server result | Home list |
|---|---|---|
| new **git** repo (`/tmp/…/t-git`) | own row, id `4ca7fc19…` = **its first root commit sha** | appears |
| non-git folder (`/tmp/…/t-plain`) | `project/current` → `id: "global"` | **nothing** |
| **empty** folder via composer | `POST /project/git/init` auto-runs (s033), pill updates, session works | not listed (no commits ⇒ no identity) |
| nothing selected + confirm | returns the **tree root `/`** | bogus `/` row added |

Also found (fixed in the same pass):

- **Picker textbox shows a *relative* path after a tree click** (`home/mark/Desktop` instead of `/home/mark/Desktop`)
  because `handleTreeSelect` passed the tree-relative value to `displayPickerPath`. Side effect: the input signal
  change re-ran the suggestions resource → a spurious **root-wide** `GET /find/file?query=home&dirs=true&directory=/`
  on *every* row click (visible in every capture).
- **Confirm with nothing selected resolves to the tree root** (`policy.result` falls back to `root`), which handed
  `/` to the caller and pushed the global placeholder into the project list.

## Plan (user-approved direction: "the list is every folder ever opened, `/` included")

- **Server (additive, no schema/SDK change):** record every resolved directory in `project_directory` (drop the
  global early-return) and publish the already-defined `project.directories.updated` event on insert. The endpoint
  `GET /project/{projectID}/directories` and the client's refetch-on-that-event wiring already exist
  (`server-sync.tsx:585-591`).
- **App:** load the plain folders in the existing bootstrap query set, expose them in the global store, and merge
  them into the Home project list (deduped by path) so `select` + the session list work for them.
- **Picker:** absolute path in the textbox, suggestions driven only by real typing, and no implicit root fallback.

## What was changed (10 files, +152/−31, 2 new)

### Engine (additive, no schema or SDK change)

| file | change |
|---|---|
| `opencode/src/project/project.ts` | `saveProjectDirectory` no longer skips the global project, so **every** resolved directory gets a `project_directory` row; it now returns whether a row was created and `fromDirectory` emits `project.directories.updated` on the **global** bus (same shape as `emitUpdated`) when one was |
| `core/src/project/directories.ts` | re-exports the schema's directories `Event` on the module namespace so the engine can name the event type without a new dependency |

**Rejected first attempt (recorded so it is not retried):** publishing the event from
`ProjectDirectories.create` (core) with `EventV2.node` added to its deps → `ReferenceError: Cannot access
'node' before initialization` (module-init cycle). `core` cannot take that dependency here. The engine layer
already holds `EventV2Bridge` **and** `GlobalBus`, and `emitUpdated` shows the global-bus emit the client's
global-stream branch listens to.

### App

| file | change |
|---|---|
| `context/global-sync/bootstrap.ts` | new `loadProjectFoldersQuery` (query key `[scope, "project-folder"]`) reading `GET /project/global/directories`; added to the bootstrap set and stored in the global store as `folder`; a failure is swallowed so an older server cannot break bootstrap |
| `context/server-sync.tsx` | `folder: string[]` in the global store; `projectFolders()` added to the query-options API next to `projects()` |
| `pages/home/home-project-folders.ts` (new) | `mergeProjectFolders(projects, folders)` + `isPlainFolder(project)` — pure, dedupes by `pathKey` against worktrees **and** sandboxes, keeps server order (newest first) |
| `pages/home/home-controller.ts` | list = `mergeProjectFolders(...)`; `select` accepts a plain folder; `add` **no longer runs `initGit`** (resolving the project is what makes the server record the directory — and it no longer writes into the user's folder) |
| `pages/home/home-projects-view.tsx` | "Edit project" hidden for id-less folder rows (there is no project row to PATCH) |

The event path needed no new client wiring: `server-sync.tsx:585-591` already refetches the bootstrap on
`project.directories.updated`, which is why the engine-side emit is enough to make the row appear live.

### Picker (`dialog-select-directory-v2.tsx` + `directory-picker-domain.ts`)

- **Suggestions now follow typing only.** A `searchInput` signal (set solely by the textbox `onInput`) drives
  the suggestion resource; `input` remains the displayed path. A tree click / navigation / reveal updates the
  path and clears `searchInput`, so the memo's query guard hides the stale list — no `find/file` call per click.
- **The textbox shows the absolute path** — `handleTreeSelect` passes `absoluteTreePath(root(), path)` instead
  of the tree-relative value.
- **No implicit root fallback** — directory-mode `result()` returns only an explicit selection, so confirming
  with nothing picked is impossible (the button stays disabled) instead of handing `/` to the caller.
- `chooseSuggestion` re-selects the folder it navigated to (`pickerRootSelection`), so a dropdown pick is
  confirmable.

## Verification so far

- typecheck: `packages/core`, `packages/opencode`, `packages/app` — clean.
- `packages/app` unit suite **755 pass / 1 fail** — the single failure is the pre-existing i18n parity break
  (FU-076, RSS keys in en+tk only); +6 new tests, no regressions.
- `packages/opencode` `test/project/` **88 pass / 1 skip / 0 fail**.
- `packages/opencode` `test/server/` 297 pass / 2 fail — **both pre-existing**, each re-proven by re-running
  with the change stashed (`httpapi-listen` "does not emit Effect HTTP response logs", `project-copy` dirty
  worktree).
- `packages/core` project-directories/copy/move-session: only the pre-existing project-copy failure.

## NOT done yet (the wrap-up decision)

- **No build, no deploy, no live verification.** The fix is code-complete and type/unit clean, but nothing has
  been rebuilt into the binary, so :4447 still serves the old behaviour. Not committed, not pushed.
- Live proof still owed: pick a non-git folder in Home ▸ Add project → it appears in the list; select it → its
  session list loads; the picker confirm stays disabled until a folder is picked; a tree click shows an
  absolute path and fires no root-wide search.
- **Dev-DB pollution from the diagnosis** (FU-080): `project` row + `project_directory` row for
  `/tmp/opencode/t-git`; the `global` row's `worktree` repointed to `/tmp/opencode/t-plain2` by a diagnostic
  `POST /project/git/init` (the panel showed `t-plain2`); temp dirs `/tmp/opencode/{t-git,t-plain,t-plain2,
  t-empty}`.

## Note on "desktop"

Nothing in this change touches `packages/desktop`. On the desktop platform the folder selector is the **OS
native dialog** (`directory-picker.tsx:26` → `platform.openDirectoryPickerDialog`, gated by
`directoryPickerKind(platform, server) === "native"`), which returns the picked path directly and never had
this defect. The desktop app is the Electron wrapper around the same `packages/app`, so it inherits the fix
when the app is rebuilt into the binary.

---

## Second pass (same day): code integration and structure

Reviewing the first pass before shipping turned up one defect in my own change and three integration gaps.

### The change did not actually record a plain folder

`fromDirectory` passed `data.directory` to `saveProjectDirectory`. `ProjectV2.resolve` collapses a
repository-less directory to the filesystem root (`{ id: "global", directory: "/" }`), so the row that got
written was `("/" , global)` — every plain folder would have merged into the single entry `/`, and the Home list
would still have shown nothing useful. Fixed to record the request when there is no vcs
(`directory: data.vcs ? data.directory : directory`); a repository still records its own worktree.

Regression test: `packages/opencode/test/project/project.test.ts` ▸ *"should record a directory without a
repository for the global project"*. Proven to be a real guard — it fails against the pre-fix line and passes
with it:

```
# with `directory: data.directory` restored
(fail) Project.fromDirectory > should record a directory without a repository for the global project
  expected [ tmp ] to equal [ "/" ]  (recorded the root)
# with the fix
1 pass
```

### Integration gaps closed

- **Multi-server Home.** `home.project.forServer` returned `ctx.projects.list()` (the per-device
  localStorage store), so under the multi-server layout a plain folder known to a remote server was not listed.
  Both the focused list and every server section now go through one `projectsFor(data)` helper
  (`mergeProjectFolders(data.project, data.folder)`).
- **The folder list never refreshed.** Nothing invalidated the `[scope, "project-folder"]` query, and the store
  was written imperatively inside `bootstrapGlobal`, so a folder added after bootstrap only appeared after a
  reload. The `folder` slice is now a **getter over a `useQuery`** (same shape as `path`/`provider`/`config` in
  `server-sync.tsx`), so every refetch — reconnect, `project.directories.updated`, an explicit invalidation —
  lands in the store without a separate write; the imperative write was removed from `bootstrapGlobal`.
- **`add` waits for nothing.** after `project.current` resolves the directory is recorded, so it now awaits
  `queryClient.fetchQuery(ctx.sync.queryOptions.projectFolders())` instead of hoping the event returns.
- **Retry was dead code.** `loadProjectFoldersQuery` had `.catch(() => [])` *inside* `retry(...)`, so a failing
  request resolved empty on the first try and never retried. The catch moved outside `retry`; the failure still
  degrades to an empty list (a server without the endpoint must not break the project list).
- Tidy-ups: `catchCause` uses `Effect.logWarning(...).pipe(Effect.as(false))` instead of a nested
  `Effect.succeed().pipe(Effect.andThen(...))`; the event payload uses `projectID` directly (it is already
  `Project.ID`); the new test helper no longer needs `as unknown as` (oxlint `no-unsafe-type-assertion`).

### Re-verification after the integration pass

- `bun typecheck` at the repo root with the pinned bun 1.3.14 (the `.husky/pre-push` gate): **30/30 tasks
  successful**. Package typechecks for `core`, `opencode`, `app` also clean individually.
- `packages/app` unit: **755 pass / 1 fail** (the same pre-existing FU-076 i18n parity break).
- `packages/opencode` `test/project/`: **89 pass / 1 skip / 0 fail** (the new test is the +1).
- `packages/opencode` `test/server/`: 297 pass / 2 skip / 2 fail — the same two pre-existing failures
  (`httpapi-listen`, `project-copy` dirty worktree), neither touching this change.
- `packages/core` `test/project`: 25 pass / 1 fail (pre-existing project-copy).
- `oxlint` on the changed files: 0 warnings, 0 errors. (The 31 warnings the full app run reports are
  pre-existing; the new files report zero.)

Still not done — unchanged: **no build, no deploy, no live verification, no commit, no push** (FU-079), and
FU-080 (dev-DB cleanup) still needs the user's OK.

---

## Third pass: full-diff review against git (same day)

Reviewed **every** hunk of the working tree against `71c73a0` (13 modified + 2 new files), traced the engine
path end to end and each app call site. Findings, all fixed:

1. **The recorded directory was not validated** (engine, real defect). `fromDirectory` records *whatever path a
   request named*, so a stale tab, a typo, or a path that has since been deleted left a permanent row — and a
   row is a **visible entry in the Home project list** that can never be opened. `saveProjectDirectory` now
   requires `fs.isDir` (the same check the sandbox list uses two screens above). New test: *"should not record a
   path that is not a directory"*.
2. **A closed plain folder disappeared from "recently closed"** (`context/global.tsx`). That list filters the
   per-device history against what the server knows, and it only consulted `data.project` — a plain folder has
   no project row, so closing one produced an entry that was immediately filtered out. The filter now also takes
   `data.folder`.
3. **`pickerMode().result(root, selected, valid)`** — after removing the root fallback, `root` was a parameter
   nothing read, in *both* modes, which is exactly the shape that invites the bug I shipped first ("looks like
   there should be a root default"). Dropped from the type, both implementations, the 3 call sites and the tests:
   the contract is now literally `result(selected, valid)`. The one `consistent-return` warning inside the
   function I own is gone (`if (!valid) return undefined`).
4. **`isPlainFolder` was test-only dead code** — the view guarded "Edit project" with a raw `props.project.id`.
   The view now uses the helper, so the tested helper is the one that decides.
5. `pickerRootSelection` was inserted directly above this file's mid-file import block (the file is a pre-existing
   merge of two modules); moved next to `pickerMode`.

**Verified while reviewing, not changed:** the recording really does happen on the web path —
`instance-context.ts:29` boots with `store.load({ directory })` and no pre-resolved project, so `fromDirectory`
runs for the `project/current` call that Home `add` makes; `ProjectHttpApi.current` just reads the booted
context. `displayName`/`getProjectAvatarSource` already tolerate an id-less row (basename + no avatar), and
`projectForSession` / the session-table controllers already guard `project.id ?` — the codebase treated
`LocalProject` as possibly id-less before FE-020.

**Known, pre-existing, deliberately not touched here** (each needs its own decision):
- The **sidebar** project list is still the per-device store while Home is server truth (asymmetric since s043),
  so a folder added on another device is invisible in the sidebar until it is added locally.
- **Drag-to-reorder** writes the per-device store, but the list renders in server order, so reordering has been
  inert since s043 (drag handles included).
- "Close project" only clears the per-device entry, so a closed project (or folder) stays in the list — correct
  for server truth, but it means Close is a *selection* action, not a removal.
- Plain folders are appended **after** the projects, so a folder you just opened sits at the bottom.
- FU-076 (i18n parity) and the two server test failures remain open and unrelated.

Gates after the review: root `bun typecheck` 30/30 (pinned bun 1.3.14) · app unit 755/1 (FU-076) ·
`test/project/` 90 pass / 1 skip / 0 fail · `test/server/` 297 pass / 2 pre-existing fails · oxlint: the only
warning attributable to this change is fixed; everything else is pre-existing (checked warning-by-warning
against my changed line ranges).
