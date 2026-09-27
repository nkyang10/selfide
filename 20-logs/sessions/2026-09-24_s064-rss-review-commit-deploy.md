# Session s064 — RSS (FE-019) review → fix → commit → deploy

- **Date (UTC):** 2026-09-24
- **Companion session:** s062 (RSS planning, 2026-09-21)
- **Scope:** detailed review of the uncommitted RSS working tree in the fork, fix 3 typecheck errors, commit, push, deploy to :4447.

## Context

The RSS feature planned in s062 was found fully coded but **uncommitted** in
`50-projects/p003-opencode-fork/opencode` (packages/opencode/src/rss + packages/opencode/src/server/rss,
plus wiring in httpapi/server.ts, settings-general.tsx, and all 60+ locale files).
User asked for a detailed review and then to commit / push / deploy.

## Review findings (s064)

Uncommitted RSS working tree reviewed end-to-end against event schemas, auth
middleware, mount pattern, TextField API, i18n. Three typecheck errors found and fixed:

1. **`packages/opencode/src/rss/rss.ts` append — real runtime bug.** `await loadFeed(token)` inside
   an async callback awaited an Effect (not thenable), so `existing` was `Effect | RssItem[]`;
   the on-disk feed was never actually loaded. Rewrote as `Effect.gen` + `yield*`.
2. **`rss.ts` — `Global.Service` dependency not in `Rss.node` deps** ("Missing dependencies"
   type error). Switched to `Global.Path.state` static (matches push.ts pattern) instead of
   `yield* Global.Service`, removing the requirement.
3. **`httpapi/server.ts` — `rssUrlRoute` leaked a `Config` requirement** into the merged
   RouteRequirements (which disallows `Config`). Root cause: direct `yield* ServerAuth.Config`
   in the router constructor. Fixed by adding `Layer.provide(ServerAuth.Config.layer)` — the same
   pattern `uiRoute` already uses.

Verified correct: all four event payloads carry `sessionID` (incl. optional one on
`session.error`); `/rss/:token` is public-by-token, `/api/rss/url` auth-gated; XML escaping
applied; TextField `readOnly`+`copyable` supported; 60+ locales updated.

## First-run commit (RSS, separate from titlebar)

```
feat(rss): FE-019 per-user RSS notification feed
```

## Execution log

| UTC time | Session | Target | Command | Exit | Result / note |
|---|---|---|---|---|---|
