# s011 — FE-004 folder-picker tweaks (2026-09-09 15:28 UTC)

## Scope
Two tweaks to the mobile folder picker (`dialog-select-directory-v2.tsx`).

## Changes
1. **Removed "tap highlighted folder again → unhighlight"** — removed `tappedRowPath()` helper
   and the `onContainerClick` capture-phase listener. Plain tap now only navigates into a folder.
2. **Picker opens at filesystem root** — the mount `createEffect` now navigates to
   `pickerRoot(start())` (i.e. `/` or `X:`) instead of drilling straight into the last-opened
   folder, so the user lists from the top and drills down themselves. `start()` (last-opened) is
   still the default selection for the confirm action.
3. **Reveal-from-root on typed path (fix user found)** — typing a path (e.g. `~/Desktop/ide/...`)
   and pressing Enter previously `navigate()`d into that folder (kept the folder pinned as the
   view). Added `reveal()`: resolves the input to absolute (`pickerAbsoluteInput`), ensures the
   tree is rooted at the filesystem root, then walks each ancestor segment (`load` that level +
   `getItem` a trailing-slash dir lookup + `child.expand()`) and finally `select()`s the target.
   Enter's no-suggestion fallback now calls `reveal(input())` instead of `navigate(input())`, so
   the tree still lists from `/` with the target revealed+highlighted. Folders, listings, and
   home-expansion (`~/`) all handled; `pickerRelativePath` imported.

## Verification
- `bun x tsgo -b` → clean (no output).
- `bun test .../directory-picker.test.ts .../directory-picker-domain.test.ts .../pierre-tree.test.ts`
  → 25 pass, 0 fail.

## Status
Code committed? NO (local uncommitted changes). 
- 00:39 UTC Sep 11 (session continues): rebuilt + deployed `0.0.0-dev-202609101639` (bun 1.3.14)
  to :4447 pid 3453286. The prior deployed instance (2790696) had CRASHED — log ended with
  `MaxListenersExceededWarning: Possible EventTarget memory leak detected. 11 event listeners...`
  after ~6h, killing the tunnel origin (tunnel itself never expired; cloudflared stayed up,
  returned 502 until server restarted). Rebuild+restart fixed it. Verified localhost/LAN/tunnel
  all 200 with `opencode:hahahaha`; tunnel URL unchanged (orlando-expansion-thu-toxic).
  TODO: root-cause the MaxListeners leak (suspected SSE/EventTarget accumulation).
