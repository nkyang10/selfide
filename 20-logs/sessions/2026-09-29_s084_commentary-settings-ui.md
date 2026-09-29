# s084 — Commentary settings in the Settings v2 General tab

> **Started:** 2026-09-29 (UTC)
> **Feature id:** FE-029 (FE-028 is the panel; s083 holds FU-111 mobile). Decision record: **DEC-058**.
> **Fork:** `50-projects/p003-opencode-fork/opencode` @ `dev` (`4218986` + s083's uncommitted WIP).

## Request (user, verbatim)

> *"opencode webui setting v2 — do we have a onoff switch for the commentary function? i want to add a
> section of setup in general part. on/off switch. a textarea to add text for manual prompt injection to
> the call that generating commentary. it is used for user to add preference like tone, tech level,
> role, etc."*

## Findings (read-only, before any code)

1. **A config key `commentary.enabled` already exists** and is enforced server-side
   (`packages/opencode/src/session/commentary.ts:362`, `if (!config.enabled) return undefined`), with
   `enabled: commentary?.enabled ?? true` in `settings()` (`:71`). It is **hand-edit only** —
   `~/.config/opencode/opencode.jsonc` — so today the only way to stop the narration is to edit a file.
2. **No prompt-injection key exists.** The narration prompt is hardcoded in two places:
   `packages/opencode/src/agent/prompt/commentary.txt` (the hidden `commentary` agent's system prompt)
   and `INSTRUCTIONS` (`commentary.ts:227`), which is the tail of the per-tick user message built by
   `prompt()` (`:238`).
3. The General tab is `packages/app/src/components/settings-v2/general.tsx`; the **Admin** tab
   (`settings-v2/admin.tsx`, FE-023) is the precedent for config-file rows, but it is server-global.
4. The narration is gated **server-side on a lease** — `watch`/`unwatch` with a 45 s TTL, refreshed by a
   15 s client heartbeat. A client that never takes the lease gets no narration for that session.
5. `packages/app/src/pages/session/commentary-watch.ts` is **s083's uncommitted WIP** and is the lease
   owner. It must be extended, not replaced.
6. `packages/ui/src/v2/components/textarea-v2.tsx` exists (`TextareaV2`), used by
   `dialog-edit-project-v2.tsx` and `dialog-rss-v2.tsx`.

## Decisions taken (asked, not assumed)

| # | Question | User's answer |
|---|---|---|
| D1 | Server-global config file vs per-browser? | **Per-browser local setting** |
| D2 | Textarea save: on blur / debounced / explicit Save? | **Explicit Save button** |
| D3 | The prompt is assembled server-side, so the text must reach the server. Config key, or ride the watch lease? | **Send it with the watch lease** |

**Consequence of D1 that had to be checked before answering:** a per-browser switch is still a *real*
off, not just a hidden button — because the server narrates only while a client holds the lease, so
"never take the lease" means "no LLM calls from this device". This is what made the local choice
coherent; the option I offered first was pessimistic about it.

**Known wart of D3, accepted:** the lease is one value per session (`Map<SessionID, …>`), so if two
devices watch the *same* session, whichever heartbeated last supplies the wording. They already share
one narration stream, so this only shows across two screens open on one session. The alternative
(counting leases) is forbidden by the existing design note in `commentary.ts:350`.

## Work

(filled in as it lands)

## Result

(pending)
