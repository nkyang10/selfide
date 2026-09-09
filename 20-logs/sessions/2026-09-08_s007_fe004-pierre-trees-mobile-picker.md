# s007 — FE-004 (proposed): mobile uses the @pierre/trees folder explorer in the open-project dialog

- **Date:** 2026-09-08 (UTC)
- **Project:** p003-opencode-fork (app = `packages/app`)
- **Type:** research + implementation
- **Status:** implemented, tested, built, **live on :4447** (0.0.0-dev-202609081709, pid 2229139); iPhone field test pending (user)

## Request (user intent)

Replace the folder-selection part of the open-project dialog with a typical Windows-style folder
explorer. User confirmed two refinements:
1. **Interaction:** use `@pierre/trees` on mobile too (reuse the component the desktop v2 dialog already
   uses — v1.0.0-beta.4, already a dependency).
2. **Start path:** the **last opened project's folder** (not filesystem root / not `~`).

Original spec behaviour to preserve: highlight a folder → "Open this folder" opens it; no highlight →
opens the current folder; clicking the highlighted folder unhighlights it.

## Research (online, per request)

- `@pierre/trees` = file-tree component by The Pierre Computer Company (`pierrecomputer/pierre`),
  Apache-2.0, docs trees.software, published on npm. Purpose-built file tree: virtualization,
  lazy-load-on-expand, selection, search, drag-drop. Already in `packages/app` (and used for the file
  sidebar + desktop v2 dialog). **Chosen.**
- Alternatives checked (SolidJS): `milahu/solidjs-treeview-component`, Zag.js tree-view, kobalte Tree,
  shadcn-tree, 21st.dev file-trees — all generic trees, none a drop-in file-explorer with server-side
  lazy listing; would need the same integration work we already have for @pierre/trees.

## Code findings

| Area | File | Fact |
|---|---|---|
| Picker dispatch | `components/directory-picker.tsx` | v2 dialog only used when `platform.platform === "desktop" && settings.general.newLayoutDesigns()`; web/mobile falls back to **v1** (`dialog-select-directory.tsx`, a search-list — the thing the user dislikes on phone). On our build, `newLayoutDesignsDefault = true`, so dropping the desktop gate is enough. |
| Explorer dialog | `components/dialog-select-directory-v2.tsx` | `@pierre/trees` `FileTree` web component: click folder = single-select + toggle-expand (drill-down) (`rowClickPlan.js`: `selection==="single"`, `toggleDirectory: true`); Ctrl/⌘-click = toggle. `pickerMode("directory").result(root, selected)` = `selected || nativePickerPath(root)` — **already** the "highlighted wins, else current folder" rule. Selection cleared via `onInput` too. |
| Deselect | `@pierre/trees .../FileTreeItemHandle` | exposes `deselect()`, `toggleSelect()`, `select()`. Rows carry `data-item-path`. So tap-to-unhighlight = capture-phase click on the tree container; if tapped path === current selection → `tree.getItem(path)?.deselect()` + stopPropagation (blocks the tree's own re-select+expand). |
| Last opened project | `context/server.tsx` `createServerProjects` | `last()` = `store.lastProject[scope]`, updated by `projects.touch(dir)` on navigation (`pages/layout.tsx:1166,1686`). `useServer().projects.forServer(ServerConnection.key(conn))` gives the per-server store. Server `GET /path.directory` is static (instance cwd) — not the UI's last-opened project, so we use `last()` instead. |
| Mobile sizing | `packages/ui/src/v2/components/dialog-v2.css` | `size="large"` = fixed 640×480 → overflows a phone. Fix via `:has(.directory-picker-v2)` media query (full `100dvh`, ≤680px). |

## Implementation plan

1. `components/directory-picker.tsx`: gate v2 on `settings.general.newLayoutDesigns()` only (remove desktop check).
2. `components/dialog-select-directory-v2.tsx`:
   - `start`: `props.start || lastOpened() || path.directory || path.home || fallback...` where
     `lastOpened() = useServer().projects.forServer(ServerConnection.key(props.server)).last()`.
   - Tap-to-unhighlight: capture-phase `click` on the tree container; walk `event.composedPath()` to find
     `data-item-path`; if `policy.selection(root(), path) === selected()` → `tree.getItem(path)?.deselect()`
     + `event.stopPropagation()`.
3. `components/dialog-select-directory-v2.css`: mobile full-viewport media query for the picker dialog.
4. Typecheck + tests, rebuild binary, swap :4447 (user confirm), iOS field test.

## Verification
- `bun typecheck` (app), `bun test` (unit + browser suites).
- Rebuild `--single`, confirm new bundle live on :4447.
- Phone test: open-project → bottom of tree starts at last-opened project → tap folders to drill down →
  tap a folder to highlight → tap it again → unhighlights (no icon) → "Select folder" opens highlighted or
  the current folder.

## Implementation (DONE, user GO "Yes, swap now")

### Code (3 files)
- `components/directory-picker.tsx` — use `DialogSelectDirectoryV2` on **every** platform (dropped the
  `platform.platform === "desktop"` gate; falls back to v1 search-list only when `newLayoutDesigns` is off).
- `components/dialog-select-directory-v2.tsx`:
  - `start` memo now prefers the **last opened project's folder**:
    `props.start || lastOpened() || path.directory || path.home || fallback…`, where
    `lastOpened() = useServer().projects.forServer(ServerConnection.key(props.server)).last()`.
  - **Tap-to-unhighlight:** capture-phase `click` listener on the tree container; reads the tapped row's
    `data-item-path` via `composedPath()`; if it equals the current selection →
    `tree.getItem(path)?.deselect()` + `stopPropagation()` (blocks the tree's native re-select+expand).
    This gives the touch-only "click the highlighted folder to unhighlight" the lib only provides via Ctrl/⌘-click.
- `components/dialog-select-directory-v2.css` — mobile media query (≤680px) makes the picker dialog
  full-viewport (`100dvh`) via `:has(.directory-picker-v2)`, so the 640×480 fixed size can't overflow a phone.

### Already correct (confirmed, no change needed)
- "Open this folder" semantics: `pickerMode("directory").result(root, selected)` =
  `selected || nativePickerPath(root)` — highlighted folder wins, else the current folder. The footer
  button `dialog.directory.action.selectFolder` is that "Open this folder" button.
- Click-to-drill-down: @pierre/trees plain click on a folder = select + toggle-expand.

### Research outcome (online)
`@pierre/trees` (pierrecomputer/pierre, Apache-2.0, trees.software) confirmed as the component to use —
purpose-built file tree (virtualization, lazy load, selection), already a dependency, used by the desktop
v2 dialog and the file sidebar. Generic SolidJS trees (solidjs-treeview-component, Zag tree-view, kobalte,
shadcn-tree, 21st.dev) checked — none are drop-in file explorers with server-side lazy listing; they'd need
the same integration.

### Verification (all green)
- `bun typecheck` → clean.
- Unit suite `./src` → 726 pass / 0 fail; browser suite `./test-browser` → 41 pass / 0 fail.
- Rebuild `bun ./packages/opencode/script/build.ts --single --skip-install` → smoke OK,
  `0.0.0-dev-202609081709`. New app bundle `index-CYFDBbly.js`; FE-004 markers (`tappedRowPath`,
  `lastOpened`) confirmed in `dialog-select-directory-v2-*.js.map`.
- Live swap (user confirmed): old pid 1949123 → new pid 2229139; `GET /` 200 + new bundle; login/logout
  200; SSE connected + heartbeat.

### Pending (user)
**iPhone field test:** open-project → explorer should start at the last-opened project folder → tap folders
to drill down (expand) → tap one arrow-highlighted folder → "Select folder" puts it in the "current folder"
strip → tap the highlighted folder again → unhighlights → "Select folder" then opens the current folder.
Also verify the dialog fits the phone screen (full-viewport on ≤680px).
