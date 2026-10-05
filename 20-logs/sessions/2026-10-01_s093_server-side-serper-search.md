# s093 — Server-side Serper: the search key lives on the server, not on every machine

Session opened 2026-10-01 11:24 UTC
Preceded by s092 (special lines / panel controls). Triggered by a question, not a
bug: *"is there a previous task support serper (search)?"* — yes, s031/s032, but it
ran `storage/serper.py` on the **user's** machine and needed a key there.

## The request

> shall we do it as a server side function which we set key in server opencode.json.
> and then when any user take the skill, it will able to do

The shape is right and the fork already has the seam for it: `websearch` is a
server-side tool with pluggable providers (`packages/opencode/src/tool/websearch.ts:37`),
exposed for `opencode` / `opencode-go` models (`registry.ts:58`) — which is the
model family this session runs on. So Serper becomes a **provider**, the key is
read from config **on the server**, and any client of the deployed server can
search without possessing anything.

Decisions taken (asked, not assumed):

| Question | Answer |
|---|---|
| Provider of `websearch` vs a new tool id | **Provider of `websearch`** — the model already calls it, so no skill is required for search to work at all |
| Where the key lives | **Literal key in `~/.config/opencode/opencode.jsonc`** — the user's explicit choice over `{env:SERPER_API_KEY}` |

## Status

(record filled in as the work lands — see the sections below)