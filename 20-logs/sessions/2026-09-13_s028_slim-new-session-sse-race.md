# s028 — Slim new-session: SSE response race (no live reply, appears after reload)

**Date:** 2026-09-13 (UTC)
**Project:** p003-opencode-fork (web/app)
**Scope:** `packages/app` (client). Follow-on to s027/FU-037.

## Symptom (reported by user, on phone via LAN)
The slim button (compact → create a new session seeded with the summary) works: new tab opens,
summary appears. But **no live assistant response** — neither for the seeded handoff nor for a fresh
message typed afterward. The assistant **does** reply after a **page reload** shows it.

## Diagnosis
- Server-side is fine: DB + opencode.log show the new session (`Test (2)`, ses_f666...) created the
  assistant reply for every turn. `stream providerID=dgx modelID=general ... agent=build mode=primary`
  ran to completion. So the response is generated and persisted.
- Reload renders it → the client simply never received/surfaced the **SSE stream** for the
  brand-new session: a **subscription race**. The slim flow does `session.create` → `navigate(...)`
  → immediately `sendFollowupDraft(...)` in the same tick. The client's event stream for the new
  session (`directory`/`sessionID`) is not yet subscribed, so the live response is missed.

## Root cause section
The server produces the assistant reply fine (DB + `opencode.log` show `stream ... agent=build mode=primary`
→ `step-finish`). Reload renders it → the client lost the **live** reply only.

The slim flow's `session.create`:
- **omitted `location: { directory }`** (normal new-session path passes it, submit.ts:407), and
- **never registered the new session client-side** (normal path calls `seed()` =
  `serverSync().session.remember(info)` + directory child `setStore("session", …)`; slim did neither).

The timeline renders from the round global store (`directory-sync.ts:35` routes message/part reads to
`server-session.data`, populated by `session.apply`/`applyV2` for every SSE event). Streaming parts for a
session whose parent message isn't in `data.message[<newId>]` yet — and with no message load/registration
for that session — are gated/dropped (`server-session.ts:1094-1107`), so they don't render until a reload
re-fetches the session history.

## Fix
In `slimSession` (message-timeline.tsx), mirror the normal new-session path immediately after create:
1. `session.create({ ..., location: { directory: sdk().directory } })` — anchors the new session to the
   active project directory.
2. `serverSync().session.remember(created)` + child `setStore("session", …)` insert — register the session
   client-side exactly like `seed()` in `prompt-input/submit.ts`.

## Verification
- `tsgo -b` (app, pinned bun 1.3.14): clean.
- Full single-file build `0.0.0-dev-202609130745`; deployed to :4447 (pid 1086348). Login 302, authed / 200.
- **On-device phone check pending** (FU-041): confirm live reply now appears without reload for (1) the
  seeded compact summary and (2) a fresh message in the slim-created session.
