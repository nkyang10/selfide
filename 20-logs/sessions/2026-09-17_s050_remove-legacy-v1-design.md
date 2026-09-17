# Session s050 — Remove legacy v1 design entirely

**Date:** 2026-09-17
**Project:** p003-opencode-fork
**Agent:** opencode controller

## Scope
User requested: keep only the latest (v2) design; delete all legacy (v1) code;
commit + push everything; rebuild + deploy to :4447.

Confirmed with user:
- **Delete v1 code entirely**: strip `newLayoutDesigns` flag, delete LegacyHome /
  legacy layout / v1 branches, keep only v2.
- **Rebuild + deploy** to :4447 after commit+push.

## Files touched (tracked below as work progresses)

## Outcome
**ABANDONED — 2026-09-17 15:27 (UTC).** No work was performed. User re-evaluated:
the v1/legacy UI is the *official opencode* first-generation design (upstream's
`newLayoutDesigns` flag + `LegacyHome`), **not related to our fork** and not something
we created. Removing it is out of scope / unnecessary. Session closed, nothing committed
or deployed. v1 code remains in the tree (verified: `app.tsx` + `legacy-home.tsx` still
reference `LegacyHome`, fork HEAD unchanged at `823d96d`).

## Follow-up session notes
- No follow-ups from this session. Note: PID 3850381 (:4447 dev deploy) was killed at
  user request on 2026-09-17 (~15:27 UTC) in a separate thread; redeploy later if needed.
