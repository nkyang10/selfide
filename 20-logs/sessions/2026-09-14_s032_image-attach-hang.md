# Session s032 — Investigate: chatbox photo/attachment upload hangs then nothing

- **Date:** 2026-09-14 (UTC)
- **Branch:** `dev` (p003-opencode-fork)
- **Goal (user):** "when i upload a photo through the chatbox attachment of image, nothing done
  after a seconds of hang."

## Symptom

Selecting an image via the chatbox attachment (image) control: ~1s hang, then nothing appears in
the prompt (no thumbnail, no toast). No error shown.

## Code path (image attach)

1. `prompt-input.tsx` `pick()` → `pickAttachmentFiles({ onFile: addAttachment, ... })`, or the
   hidden file-input `change` → `addAttachments([...files])`.
2. `attachments.ts` `add(file)` (attachments.ts:46):
   - `attachmentMime(file)` (files.ts:85): for `image/*` returns immediately at line 87 (no file read).
   - `blob: await input.draftStore.putBlob(file)` (attachments.ts:60) — **the hang point**.
   - `target.prompt.set([...current, attachment])` (attachments.ts:62).
3. `platform.draftStore` is always `createBrowserDraftStore()` (entry.tsx:122) → IndexedDB
   `opencode-drafts` (draft-store.ts:97).
4. `putBlob` → `write("blobs", id, blob)` (draft-store.ts:38) → `await db` (IDB open, draft-store.ts:134).

## Key observations

- `draft-store.ts`, `attachments.ts`, `files.ts` are **unmodified upstream** (all at fork commit
  `ecbc6cc`); only package.json/bun.lock/`directory-tree-zag.tsx` are local changes, and the Zag
  picker (s029) is NOT deployed. So this is upstream acting, not a fork regression.
- `putBlob` path: on many mobile Safari / strict key-value IDB setups, the initial cleanup
  `readwrite` transaction in `createBrowserDraftStore` (draft-store.ts:106-123) only resolves `db`
  on `complete`/`abort`; the `put` can also reject without a catch when quota/IDB is unavailable.

## Evidence

- Running binary `0.0.0-mark-dev-202609130834` (pid 1102064, :4447). Files unmodified from fork base.

## Root cause (CONFIRMED)

`crypto.subtle.digest` in `blobID` (draft-store.ts:25) only exists in **secure contexts**
(HTTPS or `localhost`). The fork web server is plain HTTP on LAN IPs
(`http://192.168.100.11:4447` etc., per run-web.sh). On a non-localhost HTTP page the browser
marks it an insecure context → `crypto.subtle` is `undefined`.

Flow: attach image → v2 `add()` (session-ui .../attachments.ts:106 `await input.store(file)`)
= `draftStore.putBlob(file)` (draft-store.ts:38) → `blobID` (draft-store.ts:25) reads the full
file into memory (`await blob.arrayBuffer()` — the "second of hang" for a photo), then throws
`TypeError: Cannot read properties of undefined (reading 'digest')`. `putBlob` rejects → `add`
rejects → `addAttachments` has no try/catch → **unhandled rejection, no thumbnail, no toast** =
"nothing done".

Active input is **v2** (`newLayoutDesigns` default true → `PromptInputV2Composer`,
session.tsx:2184). v1 and v2 both route through `draftStore.putBlob`.

Matches upstream issue
[anomalyco/opencode#11452](https://github.com/anomalyco/opencode/issues/11452) "Web interface:
Attaching files is broken in insecure contexts" (referenced crypto.randomUUID / insecure context).

A sibling fallback already exists in `packages/app/src/utils/uuid.ts` (guards
`globalThis.crypto`, `isSecureContext`, try/catch) — use the same idiom.

## Fix (implemented + deployed)

1. `packages/app/src/utils/draft-store.ts` — `blobID()` now checks
   `globalThis.crypto?.subtle` + `isSecureContext` (same idiom as `utils/uuid.ts`); on
   secure contexts it keeps SHA-256; on insecure contexts (LAN HTTP) it falls back to an
   in-repo **FNV-1a** hash (`fallbackBlobID`, constant `0x811c9dc5`).
2. `packages/session-ui/src/v2/components/prompt-input/attachments.ts` — same guard applied to
   the `blobReference()` fallback path (used only if `draftStore` is undefined).

### Verification

- `packages/app` `tsgo -b` typecheck: **clean**.
- app `bun test attachments.test.ts`: **10 pass / 0 fail** (v1 flow unaffected).
- session-ui `bun test src/v2/components/prompt-input`: **16 pass / 0 fail** (v2 flow).
- craft test forcing insecure context → `createBlobReference` returns non-empty id + `blob:`
  URL without throwing: **1 pass**.

### Build & deploy

- `scripts/build-linux.sh` (pinned bun 1.3.14) → `dist/opencode-linux-arm64/bin/opencode`
  version **0.0.0-mark-dev-202609140028** (184 MB), smoke `--version` OK (built 08:29 +0800,
  newer than every source mtime → includes s033 `session-composer-controls.ts` edit).
- Replace running server: killed pid **1557456** (s029 Zag build `...140012`), started
  `OPENCODE_SERVER_PASSWORD=<inherited env>` → **pid 1586634** on :4447. `/` 401, `/login`
  200 (FE-001 login page preserved). `/proc/1586634/exe` → my new binary.

## Coordination note

Working tree contained **s033's uncommitted Zag/session-composer work** (pre-existing, untouched
by this session). My rebuild from the working tree preserved it; deployed binary is newer than all
source mtimes. **Resolved in wrap-up (s029-continued):** confirmed the s033 new-folder bootstrap IS
in the live build — binary `...140028` (pid 1586634) carries `project.initGit` (the bootstrap path).
No separate s033 deploy needed; only on-device retest remains (FU-046, shared with FU-047/FU-048).
