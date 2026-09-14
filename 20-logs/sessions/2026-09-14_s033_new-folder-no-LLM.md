# Session s033 — Fix: selecting a new folder as project → prompt not sent to LLM

- **Date:** 2026-09-14 (UTC)
- **Branch:** `dev` (p003-opencode-fork)
- **Goal (user):** "when select a new folder as project to work on, when i input prompt, it
  didn't send request to llm. verify and fix."

## Symptom

On the new-session draft page (`/new-session?draftId=…`), selecting/setting a **brand-new folder**
as the project (via the project selector / "add project" directory picker) and then submitting a
prompt produces **no LLM request and no assistant reply**. The visible prompt goes in but nothing
comes back (no toast, no streamed parts).

## Root cause (verified by code trace)

When a **brand-new folder** is picked on the draft page, `createPromptProjectControls().selectProject`
(`pages/session/composer/session-composer-controls.ts:87-111`) only does **client-side** bookkeeping:

- `target.projects.open(worktree)` — updates the in-memory frontend project list
- `target.projects.touch(worktree)` — marks it recent
- `tabs.updateDraft(draftId, { directory })` — remounts the draft SDK to the new directory

It never **bootstraps the directory on the server**.

Compare with the reference implementation for adding a project from Home
(`pages/home/home-controller.ts:89-109`, `project.add`): when the folder is empty it calls
`ctx.sdk.client.project.initGit({ directory })` (creates a git repo) and then registers it with
`ctx.sync.child(directory, { bootstrap:false })[1]("project", project.id)` (seeds the server-sync
child store so the directory is a known project scope).

Because the draft path skips that bootstrap, the server has **no project/directory scope registered**
for the new folder. A session created there (`location:{ directory }`) therefore hits the client-side
orphan gate on streaming (see FE-011 / server-session orphan gate) and the assistant parts are dropped
— presenting as "the request never reached the LLM".

## Fix

In `session-composer-controls.ts`, extract a `bootstrapProject(target, worktree)` helper (mirrors
`home-controller.ts:add`) and call it from every branch of `selectProject` before navigating /
updating the draft. It:
1. Lists files in the folder (`.file.list({ path:".", location })`)
2. If empty → `project.initGit({ directory })` (else `project.current`)
3. Seeds the child store with `sync.child(directory, { bootstrap:false })[1]("project", project.id)`
4. Falls back to `target.projects.open(worktree)` on the existing list so already-known projects
   still work (bootstrap is fire-and-forget, non-blocking).

## Verification

- Typecheck of the app package is clean (see command log).
- Existing `session-composer-controls` behavior unchanged for already-registered projects
  (`projects.open/touch` still called).
- **Build+deploy verified (wrap-up):** the fix is in the **live binary** — pid 1586634 on :4447
  serves build `0.0.0-mark-dev-202609140028` (built 08:29, after the 08:06 source edit); the
  binary contains the bootstrap path strings `project.initGit` / `project.list`. No rebuild needed.
- Live on-device retest pending on the fork build (FU-046 tracker) — user action only.

## Links

- `pages/session/composer/session-composer-controls.ts` (fixed)
- `pages/home/home-controller.ts:89-109` (reference pattern)
- `10-status/open-followups.md` FU-046
