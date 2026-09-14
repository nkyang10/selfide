# Directory-picker library options for the opencode web UI (s029)

## Date
2026-09-14 (UTC), session s029. Trigger: user reported the folder/project selector is buggy and
asked for a "better, all-in-one library" + keep text-path input + allow mid-level folder selection.

## Context
- Component: `50-projects/p003-opencode-fork/opencode/packages/app/src/components/dialog-select-directory-v2.tsx`
- Renders the browse tree via `@pierre/trees` (web-component `FileTree`, beta `1.0.0-beta.4`) —
  the fragile/buggy surface (imperative + shadow-DOM traversal).
- Stack: SolidJS 1.9.10, bun workspace with a `catalog:` for pinned versions.
- Domain logic (`directory-picker-domain.ts`) already handles Windows paths, `~`, drive enumeration,
  and mid-level folder reveal. The text path input + suggestions already satisfy the path-input +
  mid-level requirements; only the tree widget needs replacing.

## Candidates reviewed
- **react-arborist** — React-only, virtualized tree. Mismatch (app is Solid).
- **react-d3-tree / react-sortable-tree / @react-awesome-query-builder** — D3 or React-only, not a
  folder picker, largely unmaintained.
- **@pierre/trees** (current) — beta web-component, buggy integration in this repo.
- **Zag.js TreeView** (`@zag-js/solid` + `@zag-js/tree-view`) — framework-agnostic state machine,
  Solid bindings, native lazy loading, keyboard nav, programmatic expand for mid-level reveal.

## Decision (RECOMMENDED)
**Zag.js TreeView v1.43.3** (all `@zag-js/*` packages consistent at 1.43.3).
- peerDependency `solid-js >=1.1.3` — compatible with the app's solid 1.9.10.
- Lazy loading: `loadChildren` + `onLoadChildrenComplete` + `childrenCount` (maps to backend
  `file.list`).
- Selection + `api.expand`/`api.select` (for the mid-level reveal like `C:\infrasys\java\jre`).
- Plain DOM rendering, WAI-ARIA keyboard nav, `data-state`/`data-depth` CSS hooks.
- Backed by chakra-ui / Ark ecosystem — actively maintained.

## Build note
- Build must use pinned **bun 1.3.14** (scripts/build-linux.sh). bun 1.4.x produces a broken graph
  (see `notes/build-runtime.md` from s023).
