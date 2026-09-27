# s071 — DEV dropdown: mirror the project-page utility items (Log out / Settings / Help)

- **Date:** 2026-09-27 (UTC)
- **Owner:** agent (user: mark)
- **Trigger:** user — "opencode fork 4447 enhancement … in the top left DEV button … dropdownmenu add more option …
  add the 3 items that originally in project selection page, setting, logout"
- **Baseline:** fork `dev` = `c1f1b58` (FE-020, pushed, clean tree). Live :4447 = build `1.1.20260926102413`,
  pid **2999326** (s068 settings-v2 build; **FE-020 is not in it**).
- **⚠ Concurrency:** a **parallel workspace process** is running as **s070** ("thinking dual elapsed timers") in
  the same fork checkout. It claimed the s070 number first, so this session file was renamed to `s071`. Its
  uncommitted WIP is described under "Cross-contamination" below and is **also inside the deployed binary**.
- **Outcome:** ✅ implemented, typechecked, deployed to :4447, **verified live with Playwright**, then
  **committed `96f8e79` + pushed to `origin/dev`** at the user's request (pre-push typecheck 30/30).

## What the user asked for

The top-left **DEV** button (`ChannelIndicator` in `packages/app/src/components/titlebar.tsx:649`, dev-channel +
`debugTools` only) had 4 items: Home page, Refresh, Clear cache, Debug tools. The user wants the 3 utility items
that live at the bottom of the **project selection page** (Home ▸ Projects) available there too.

Those 3 items are `HomeUtilityNav` (`packages/app/src/pages/home/home-projects-view.tsx:158-196`), in this order:

| item | handler in `HomeUtilityNav` | origin |
|---|---|---|
| Log out | `window.confirm(sidebar.logoutConfirm)` → `window.location.href = "/logout"` | inline (view) |
| Settings | `projects.utility.settings` = `useSettingsCommand()` → `useSettingsDialog()` | `home-projects-controller.tsx:24,122` |
| Help | `projects.utility.help` = `platform.openExternal("https://opencode.ai/desktop-feedback")` | `home-projects-controller.tsx:123` |

## What changed

One file, `packages/app/src/components/titlebar.tsx`, +22 lines:

- `ChannelIndicator` now also calls `useLanguage()`, `usePlatform()` and **`useSettingsDialog()`** (all three hooks
  are above the existing `if (channel === "dev" && props.debugTools)` early return, so hook order is stable for
  the non-dev branch too).
- After the 4 dev items: a `DropdownMenu.Separator`, then **Log out**, **Settings**, **Help** — the same order as
  the project page, with the same handlers.
- Copy comes from the **existing** i18n keys `sidebar.logout`, `sidebar.logoutConfirm`, `sidebar.settings`,
  `sidebar.help` (already present and translated in all 62 locale files) → **no new keys, no parity-test churn**,
  and the DEV menu matches the rest of the UI in the active locale.
- `useSettingsDialog()` and **not** `useSettingsCommand()`: the `settings.open` command is already registered by
  the home + session controllers, so registering it a third time from the titlebar would duplicate it in the
  command palette. The returned `show` is exactly what the project page's Settings button calls.

Verified on the live server (build `1.1.20260927065342`, pid **3613950**), Playwright chromium-1217:

| check | result |
|---|---|
| DEV menu contents | `["Home page","Refresh","Clear cache","Debug tools","Log out","設定","說明"]` (zh browser locale) |
| separator | 1, 1px tall, `margin: 4px -4px` (styled by `packages/ui/src/components/dropdown-menu.css:93`) |
| row geometry | all 7 rows 27px, no overlap |
| **Settings** | opens the v2 dialog — `[data-slot="dialog-content"]` visible, `.settings-v2` present, `data-orientation=vertical` @1280px |
| **Log out** | native confirm "Are you sure you want to log out?" → accept → lands on `/login` (title "Sign in · opencode") |
| **Help** | not clicked (opens an external URL); the call is character-identical to the project page's |
| console / page errors | none |

Gates run **before** the parallel process's WIP landed: `bun typecheck` (packages/app) clean · app unit
755 pass / 1 fail (the pre-existing FU-076 i18n parity) · oxlint on the file 13 warnings / **0 errors**, all
pre-existing lines (221…685), none in the added block.

## Commit + push (07:45–07:49)

`git add` staged exactly the 3 files of this change (`titlebar.tsx`, `AGENTS.md`, `README.md`, +37/−2,
`git diff --cached --check` clean) and left every parallel-process file unstaged. Between that `add` and the
`commit`, the **parallel process committed its own work as `5d6b47a`** (65 files, +802/−13) — so this session's
commit `96f8e79` sits on top of it and the two stay cleanly separated. Push needed `PATH+=~/.bun/bin` for the
husky pre-push `bun turbo typecheck` (**30/30 successful**); pushed `5d6b47a..96f8e79 dev->dev`, and after a
`git fetch` local `dev` == `origin/dev` == **96f8e79**. The 8 still-dirty files belong to the parallel process
(it has moved on to engine-side project work), none to s071.

## Cross-contamination (read this before deploying again)

The build compiles the whole checkout, so the deployed binary `1.1.20260927065342` contains **two** changes:

1. this session's DEV-menu items, and
2. the parallel s070 process's **uncommitted, currently typecheck-broken** WIP —
   `packages/app/src/pages/session/timeline/turn-activity.ts` (new, **2 TS errors** at `:23`/`:27`,
   `number | undefined` not assignable to `string | number`), `turn-activity.test.ts` (new),
   `message-timeline.tsx` and a new `session.thinking.elapsed` key in `i18n/en.ts` (en-only → it became the
   i18n-parity failure, replacing the RSS keys that process had already fixed).

Nothing of the parallel work was touched or reverted here (not ours to kill), and `titlebar.tsx` is the only
*code* file this session modified (plus the fork's `AGENTS.md` / `README.md` deploy notes). The live UI loads
clean (Home renders, DEV menu opens, 0 console errors).

**Update 07:33 — the parallel process kept working and repaired its own breakage:** `bun typecheck` (packages/app)
is **clean again**, and `session.thinking.elapsed` has since been added to all 62 locale files, so the i18n-parity
debt it caused is paid. What remains true: that work is still **uncommitted**, and it **is** inside the deployed
binary `1.1.20260927065342`, so :4447 currently serves it. FU-082 tracks landing-or-reverting it.

## Housekeeping

`20-logs/command-log.md` had reached 543 lines, so the oldest 268 rows were rotated into
`90-archive/command-log-2026-09.md` (dated marker + header pointer updated; first kept row = 2026-09-17 01:32).
No folder map or runbook index change was needed (no new files or folders). The fork clone is a git-ignored
nested repo, so nothing in it is committed to the ide repo.

## Follow-ups raised

- **FU-081** — commit + push the DEV-menu change (single file, `packages/app/src/components/titlebar.tsx`);
  awaiting the user's go-ahead, and it must be staged alone (the tree also holds the s070 WIP).
- **FU-082** — parallel s070 WIP is in the deployed binary and is still uncommitted; its owner must land or
  revert it before the next commit. (Its 2 TS errors were self-fixed at 07:33; `bun typecheck` is clean again.)
- **FU-083** — the DEV menu's 4 dev-only items are still hardcoded English ("Home page", "Refresh", "Clear
  cache", "Debug tools") while the 3 new ones are localized, so a zh user sees a mixed menu. Fix = new i18n keys
  in `en.ts` + all 62 locales (same English source copy), i.e. the FU-026 pattern.
- **FU-084** — `sidebar.logout` / `sidebar.logoutConfirm` are still the English placeholder in `zh.ts` (and most
  other locales) since s012/s013, so the new Log out item (and its confirm) reads English inside a Chinese UI.

