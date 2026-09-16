# Session s046 — Fix: foreground choice dialog wiped by unscoped syncQuestions

**Date:** 2026-09-16 UTC
**Session:** s046
**Trigger:** Continuation of s045 — user tested the instrumented build on the phone ("u can check log"); the fresh debug log revealed the dialog was never missing, `syncQuestions` was destroying it.

## Evidence (testing/web-4447.log, phone test)
```
composer:questionRequest shown id=que_0aac23c2d001T9uQLBjnTwEsG0 q=What's your main goal?   (dock mounted)
lyt:visibilitychange state=hidden
lyt:foreground begin id=ses_f57fe8472ffePzvzTaWJiQ5eFS
dir:syncQuestions sessionID=ses_… protocol=v1 all=0 pending=0 firstOwn=- otherSessions=
lyt:state questionStore=0 entries first=-
```
The question dock **mounted while the phone was still alive** (SSE delivered `question.asked` → store populated). On return to foreground, `syncQuestions` ran, got `all=0`, and `reconcile([])` **wiped** the store entry → `questionStore=0` → `composer:questionRequest hidden` → dialog gone.

## Root cause chain
1. `serverSync.protocol` = **v1** (fork serves `/global/health` with `healthy:true`; `server-protocol.ts` returns v1 on the legacy probe).
2. v1 branch of `syncQuestions` called `serverSDK.client.question.list()` with **no directory/location**.
3. `serverSDK.client` is the v2 SDK → `GET /question` → `WorkspaceRoutingMiddleware` routes on `directory`/`location` query. No scope → default workspace = the server's own cwd (`testing/`), not the project dir → returns `[]`.
4. `set("question", id, reconcile([], {key:"id"}))` overwrote the populated store → dock died.

Chat history survived this because `session.sync()` v1 uses a *directory-scoped* client wrapper (`sdkFor(directory)` / `x-opencode-directory`), so only the question path was unscoped.

## Fix (scope + don't-destroy)
`packages/app/src/context/directory-sync.ts` → `syncQuestions`:
- v1 branch now passes the directory: `serverSDK.client.question.list({ directory })` (v2 SDK accepts `{directory}` which the routing middleware consumes). Matches v2 branch's `{ location: { directory } }`.
- Introduced `fetched` flag; when the fetch **throws**, skip the `set`/`reconcile` entirely (`pending` stays `undefined`) so a failed fetch can never delete a live dialog.
- Debug line now includes `fetched=`.

## Deploy + verify
- `bun run typecheck` clean; `bash scripts/deploy-web-4447.sh --detach` → **0.0.0-mark-dev-202609161521**, PID 3468506 on :4447.
- Live bundle `index-BPKpEQSx.js` contains `question.list({directory:e})` and the fetched gate (`h!==void 0&&o("question",…)`); `/__debug` probe 204.

## Follow-up
- FU-050 retest on phone: lock >20 s while agent asks a question → unlock → dialog must stay visible; `dir:syncQuestions fetched=true … pending=1`.
- **RESULT: USER-VERIFIED ✅ "it works now" (s046).** FU-050 closed.
