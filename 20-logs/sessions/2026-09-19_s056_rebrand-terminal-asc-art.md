# s056 — Rebrand terminal ASCII art: "opencode" → "MarkCode"

**Date:** 2026-09-19 (UTC) **UTC timestamp:** 2026-09-19 09:49
**Trigger:** user asked to change the "opencode" ASCII art that the web-daemon command prints (its terminal
prompt/banner) to "MarkCode". Followed up with "search online".
**Result:** ✅ DONE — 3 files changed; verified (renders as "MarkCode", typecheck 2/2). **Not committed/pushed**
(user has not asked yet).

## Background / research (searched online, per user)

- The terminal banner is `UI.println(UI.logo("  "))` in `packages/opencode/src/cli/cmd/web.ts` (line 47),
  also used by the `upgrade` + `uninstall` commands.
- `UI.logo()` (packages/opencode/src/cli/ui.ts) renders two ways:
  - **non-TTY:** the plain `wordmark` array (4 lines).
  - **TTY:** `glyphs.left` + `glyphs.right` from `@opencode-ai/tui/logo`, drawn two-tone
    **left = dim gray, right = white**, with `_`/`^`/`~` as shading marks.
- `packages/tui/src/logo.ts` is ALSO consumed by the main TUI app's `Logo` component
  (`packages/tui/src/component/logo.tsx`) and by `packages/tui/src/util/presentation.ts`
  (session-transcript epilogue header). So the shared logo change rebrands the terminal art consistently.
- **Search online:** confirmed there is no pre-existing "MarkCode" ASCII art (it's the fork's own brand) and
  surveyed figlet/ASCII generators. No local `figlet`; online generators are client-side JS (not fetchable).
  Decision: author compact block art in the **same 4-line block-font style** as the current opencode wordmark
  (the consistent rebrand), then verify by simulating the exact `draw()` logic.

## The change (3 files, +8/−8)

- **`packages/tui/src/logo.ts`** — `logo.left` = `Mark`, `logo.right` = `Code` (replaces `open`/`code`).
- **`packages/tui/src/util/presentation.ts`** — second copy of the same `logo` object rebranded.
- **`packages/opencode/src/cli/ui.ts`** — `wordmark` array rebranded to plain "MarkCode".
- New art reads **MarkCode** (M a r k / C o d e), left two-tone gray, right white; verified by rendering with
  a copy of the `draw()` logic (output confirmed readable).

New art (combined, plain):
```
█  █           █    ▄▄▄          ▄
█▄▄█ █▀▀█ █▄▄  █ ▄  █    █▀▀█ █▀▀█ █▀▀█
█  █ █  █ █    █▄   █    █  █ █  █ █▀▀▀
▀  ▀ ▀▀▀▀ ▀    █ ▄  ▀▀▀  ▀▀▀▀ ▀▀▀▀ ▀▀▀▀
```

## Verification

- `grep` : no old art pattern (`█▀▀█ █▀▀█ █▀▀█ █▀▀▄` / `█▀▀▀ █▀▀█ █▀▀█ █▀▀█`) left anywhere; new art in all 3 files.
- Render simulation (replicating `draw()`): output reads "MarkCode".
- Typecheck forced for `@opencode-ai/tui` (incl. presentation.ts) + `opencode`: **2/2 pass**.
- `git diff`: only the 8 logo/wordmark lines changed (3 files, +8/−8).

## Follow-up

- **Not committed/pushed.** 3 modified files in fork working tree. Suggested msg: `chore(ui): rebrand CLI/TUI terminal art opencode → MarkCode`.
- Note: `packages/script/release.ts` remains untracked from s054 (not part of this change; left alone).
