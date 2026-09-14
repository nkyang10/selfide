---
name: web-research
description: Use PROACTIVELY and by default for ANY question that needs real, current, or external data — the LLM's training is stale and must NOT be trusted for facts. Trigger on ANY of: a version number, a price, a "latest/newest/recent" thing, "who won / who is / what is X now", a date or year in the question, news, weather, stock/sport scores, an install command or CLI flag, an API or library usage, a comparison, "how do I / how to / how does X work", debugging an unfamiliar error, or any factual claim. Also trigger on keywords: search, look up, find out, research, check, verify, confirm, what is, what's the, tell me about, compare, latest, current, today, now, recent, newest, update, release, changelog, docs, example, how to. Do NOT answer from memory when the answer could be outdated — search first, then answer. Only skip if the question is purely about THIS codebase (read the files) or pure math/logic.
---

# Web Research — get REAL data, never stale memory

**First rule: the LLM's training data is stale.** For anything that could have
changed since training — versions, prices, APIs, people, events, "latest",
"best", "how to install", library usage, a date, a score, a news item, a
library's current flags — you **must** search the web and answer from live
results. Do NOT answer from memory. Search first, then synthesize.

This is the default behavior, not an option: when in doubt about whether the
answer is current, **search**. A wrong-but-confident memory answer is worse
than a one-second web check.

## When to trigger (be aggressive)

Trigger on **any** of these — do not wait for the user to say "search":

- A **version number** or "latest / newest / recent / current / 2024 / 2025 / 2026"
- **Who / what / when / where** about the real world (people, companies, events, products)
- **News, scores, weather, prices, stocks, sports, elections**
- **Install commands, CLI flags, config keys, API/library usage** ("how do I install X", "what's the flag for Y")
- **Debugging** an error you are not 100% sure about
- **Comparisons** ("X vs Y", "which is better for Z")
- Any **factual claim** you are not certain is still true

**Do NOT trigger** only when:
- The question is about **this specific codebase** → read the files instead.
- It is **pure math / logic / definitions** with no real-world dependency.

## Workflow

1. **Decide scope.** What exactly does the user want, and at what depth?
   If genuinely ambiguous, ask one clarifying question. Otherwise proceed.
2. **Search with Serper (primary).** Run **2–4** queries from different
   angles to avoid single-source bias. Use the prebuilt script (self-loads
   the API key, no setup needed):

   ```bash
   python ~/.config/opencode/skills/web-research/storage/serper.py "your query"
   python ~/.config/opencode/skills/web-research/storage/serper.py "query" --fresh week --num 10
   python ~/.config/opencode/skills/web-research/storage/serper.py "query" --fresh day --num 5
   ```

   Freshness: `--fresh day|week|month|year` for recency. `--num N` for count.

3. **Fetch the top hits** with `webfetch` to pull concrete details, numbers,
   and exact quotes (the Serper snippets are short — verify against the page).
   Prefer 2–3 authoritative sources.
4. **Synthesize.** Lead with the **direct answer**, then supporting evidence.
   State the **as-of date** explicitly (e.g. "As of Sep 2026, …").
5. **Cite** every load-bearing claim as a markdown link.
6. **Flag uncertainty.** Note conflicting sources, stale data, or gaps rather
   than silently blending them.

## Backends (in priority order)

1. **Serper (Google API)** — primary. `serper.py` resolves the key from
   `SERPER_API_KEY` env, else reads it from `~/.bashrc` automatically. Just
   run the script.
2. **SearXNG (Docker)** — optional private/self-hosted fallback if Serper is
   down or you need no external calls. Deploy guide is in the "SearXNG"
   section below.
3. **Raw `websearch` / `webfetch` tools** — last resort if both are unavailable.

## Serper (primary) — just run it

The script is ready to use. It **self-loads the API key** (env var first,
then `~/.bashrc`), so you do NOT need to export anything first:

```bash
# from ANY working directory — the key is resolved internally
python ~/.config/opencode/skills/web-research/storage/serper.py "opencode install skill"
python ~/.config/opencode/skills/web-research/storage/serper.py "vite 6 release date" --fresh month
python ~/.config/opencode/skills/web-research/storage/serper.py "react server components" --json | jq '.organic[0]'
```

Raw `curl` equivalent (if you need to inline it):

```bash
curl -s -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"q": "your query", "gl": "us", "hl": "en", "num": 10}'
```

Notes:
- `gl` / `hl` control country and language (`us` / `en` by default).
- `num` caps results (default 10).
- `tbs` adds freshness (`qdr:d` = past day, `qdr:w` = past week) — or use `--fresh`.
- Response fields: `organic` (title/link/snippet), `answerBox`, `knowledgeGraph`,
  `news`, `topStories`, `relatedSearches`. Feed top `organic[].link` into `webfetch`.
- The key is **charged per query** — keep queries tight and purposeful.
- Fails with exit code 3 only if the key is in neither env nor `~/.bashrc`.

## SearXNG (optional self-hosted fallback)

Use only if Serper is unavailable and you want a private backend. Deploy
SearXNG in Docker (the old `searxng/searxng-docker` repo is archived; use the
official compose template):

```bash
mkdir -p ./searxng/core-config/ && cd ./searxng
curl -fsSL \
  -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml \
  -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example
cp -i .env.example .env
docker compose up -d
```

Set `server.secret_key` in `core-config/settings.yml` (required for the JSON
API) and enable `formats: [json, csv, rss]`, then:

```bash
curl 'http://localhost:8080/search?q=searxng&format=json'
```

Logs: `docker compose logs -f core`. Update: `docker compose down && docker compose pull && docker compose up -d`.

## Quality rules

- Prefer **primary sources** (official docs, papers, vendor sites) over aggregators.
- **Separate verified from inferred** — say which is which.
- If a search returns nothing useful, **rephrase or broaden** before giving up.
- **Always state the as-of date** for time-sensitive answers.
- Keep the final answer tight; expand into sections only when the topic is complex.
- **Never** present a stale memory as fact when a quick search would settle it.
