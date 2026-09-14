# Session s029 — Replace buggy folder-picker tree with an all-in-one library

- **Date:** 2026-09-14 (UTC)
- **Branch:** `dev` (p003-opencode-fork)
- **Goal (user):** The project-folder selector in the web UI is buggy. Research and adopt a "better,
  all-in-one" folder-selection library. Keep: (1) a text area/input to type the folder path, and
  (2) the ability to select any-level (mid-level) folders such as `C:\infrasys\java\jre\` (the `java`
  folder being a mid-level folder).

## Result (DEPLOYED)

- **Build:** `0.0.0-mark-dev-202609140012` (184 MB, bun 1.3.14), PID 1557456, :4447.
  (First deploy `0.0.0-mark-dev-202609132217` shipped the core swap; second redeploy added a
  stale-root reveal hardening.) **Drift note:** pid 1557456 was killed 2026-09-14 09:06 by s032;
  the picker is now served by pid 1586634 (s032 build `0.0.0-mark-dev-202609140028`, same tree —
  `dir-picker-root` marker confirmed present in that binary).
- **Change:** Replaced the fragile **`@pierre/trees`** web-component `FileTree` (beta
  `1.0.0-beta.4`) with **Zag.js TreeView** (`@zag-js/solid` + `@zag-js/tree-view` 1.43.3).
  - New component `packages/app/src/components/directory-tree-zag.tsx` — Solid-native, no shadow
    DOM, lazy `loadChildren` from backend `file.list`, WAI-ARIA keyboard nav, `data-state` CSS hooks.
  - `dialog-select-directory-v2.tsx` rewritten to drive the Zag tree via a slim `DirectoryTreeZagApi`
    (expand/select/reset/reveal). **Path text-input (`TextInputV2`) + autocomplete suggestions +
    mid-level reveal logic preserved unchanged** (the domain layer already handled Windows paths,
    `~`, drive roots, and mid-level folder reveal).
  - `dialog-select-directory-v2.css` re-skinned for the Zag row/chevron DOM.
  - Removed `@pierre/trees` dep + its obsolete `pierre-tree.test.ts`.
- **Verification:** app typecheck clean; oxlint 0 errors; 742 app unit tests pass (incl. the 24
  picker/domain tests); app `vite build` succeeds; binary bundle confirmed to contain the Zag
  picker (`getVisibleNodes`/`getBranchProps`/`dir-picker-root`) with all `@pierre/trees` code gone.

## Requirement coverage

1. All-in-one library ✓ — Zag TreeView (framework-agnostic, chakra/ark-backed, actively maintained).
2. Text area to input folder path ✓ — kept the existing `TextInputV2` + suggestions.
3. Any-level (mid-level) folder selection ✓ — `reveal()` expands each ancestor from the filesystem
   root and selects the leaf (e.g. `C:/infrasys/java/`), matching `directory-picker-domain` logic.

## Open

- FU-047 (new): on-device retest of the picker (phone + desktop) for mid-level selection and the
  reveal UX. Owner: user, due 2026-09-15.

## Links

- `packages/app/src/components/directory-tree-zag.tsx` (new Zag tree widget)
- `packages/app/src/components/dialog-select-directory-v2.tsx` + `.css` (rewritten dialog)
- `packages/app/src/components/directory-picker-domain.ts` (unchanged domain reveal logic)
- `40-knowledge/decisions-log.md` **DEC-028** (Zag adoption, `@pierre/trees` dropped)
- `40-knowledge/directory-picker-lib-options.md` (earlier library research)
- `10-status/open-followups.md` FU-047
- **Parallel-session note:** s033 (`new-folder-no-LLM`) independently edits
  `session-composer-controls.ts` / `draft-store.ts` / `attachments.ts` in the same working tree —
  do not commit or revert those; they are a separate in-flight fix (FE-011/FE-013).
