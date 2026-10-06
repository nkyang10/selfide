# Session s101 — folder picker: create a new folder inside the selected one

User's spec, in their words: *"markcode webui open project folder selection 喺最低取消，選擇資料夾隔離，加多粒掣，
係喺現在選擇咗嘅資料夾入面開一個新folder，咁嗰粒掣撳落去嘅時候會彈出一個視窗俾我打新資料夾嘅名稱，
確定之後就會直接喺入面開一個新資料夾，然後就直接當選擇咗個資料夾完成呢個步驟"*

Mapped: in the Open-project folder-selection dialog, the footer (`Cancel` / `Select folder`) gets **one more
button**; it opens a **name dialog**; confirming **creates the folder inside the currently selected folder** and
then **treats it as the selection and finishes the step**.

**One question asked and answered** (the only ambiguity): after the folder exists, should the picker
auto-confirm? — user chose **直接開啟佢**: create → select → the picker returns that folder and closes
(no second click). So `resolve()` runs on the new folder's path.

## Decisions taken before code

- **Where the button lives:** `dialog-select-directory-v2.tsx` (`DialogSelectDirectoryV2`) footer, left of
  `Cancel`. It is the live picker: `newLayoutDesignsDefault = true` (`settings.tsx:62`), and the fork's own
  `AGENTS.md` records that the v1 surfaces are dead code ("do not fix that by editing `settings-general.tsx`").
  The **desktop** path is untouched — `directory-picker.tsx:26` hands `platform.openDirectoryPickerDialog` to
  the OS, and no button can be added to an OS dialog.
- **"the currently selected folder"** = `selected()` when the reader has highlighted one, otherwise `root()`,
  the folder the tree is currently showing. Both are already absolute (`policy.result` / `nativePickerPath`).
- **The write endpoint is a raw route, not a new HttpApi endpoint — and the reason is the client, not taste.**
  `packages/app/package.json:57` pins `@opencode-ai/client` to a **vendored tarball**
  (`file:vendor/opencode-ai-client-1.17.13-v2.tgz`), *not* the workspace `packages/client`. So adding
  `fs.mkdir` to `packages/protocol/src/groups/fs.ts` and running `bun run generate` (verified: it runs clean,
  zero diff) would produce a typed method **the app cannot call** — the picker would still need a hand-rolled
  fetch. `packages/app/src/utils/server.ts` already carries three hand-rolled fetches for exactly this reason
  (`fetchProjectDirectories`, `fetchWebuiStatus`, the FE-028 commentary routes), with the precedent documented
  in-file. So: one raw auth-gated route, one fetch helper beside its siblings.
- **Security shape of the route:** authenticated (same `authorizationRouterMiddleware` layer as
  `/api/rss/url`), and the **name** is validated server-side as a single path segment (no `/`, `\`, `.`,
  `..`, no control characters, non-empty, ≤255 chars). The server has no user model — any authenticated
  browser is already "admin" and the picker already browses the whole filesystem — so the honest boundary is
  the auth gate plus a name that cannot escape its parent, not a per-path ACL.

## Status

See the sections below, filled in as the work lands.