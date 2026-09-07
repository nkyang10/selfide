---
name: web-research
description: Use ONLY when the user needs to search the web or research a topic using websearch/webfetch. Front-load keywords like "research", "search", "find out", "look up", "what is", "latest", "compare".
---

# Web Research

Use this skill whenever the user asks to investigate, find, or learn about a
topic that may require up-to-date or external information.

## Workflow

1. **Clarify scope** if the request is vague — what exactly does the user want
   to know, and at what depth?
2. **Search** with `websearch` using specific, keyword-rich queries. Run 2–4
   queries from different angles to avoid bias.
3. **Fetch** the most relevant and authoritative URLs with `webfetch` to pull
   concrete details, numbers, and quotes.
4. **Synthesize** into a concise answer. Lead with the direct answer, then
   supporting evidence.
5. **Cite** sources as markdown links so the user can verify.
6. **Flag uncertainty** — note conflicting sources, gaps, or stale data
   explicitly rather than blending them.

## Quality rules

- Prefer primary sources (docs, papers, official sites) over aggregators.
- Separate what you verified from what you inferred.
- If search returns nothing useful, broaden or rephrase before giving up.
- Keep the final answer tight; move detail into structured sections only when
  the topic is complex.

## Self-hosted search backend: SearXNG on Docker Desktop

When the user wants a private, keyed search backend, deploy
SearXNG in a container. This is the recommended path (the old
`searxng/searxng-docker` repo is archived; use the official compose template).

### 1. Prerequisites (Docker Desktop)

- Install [Docker Desktop](https://docs.docker.com/get-docker/) and start it.
- On Linux, add your user to the docker group: `sudo usermod -aG docker $USER`
  then re-login. On Windows/macOS Docker Desktop handles this.

### 2. Deploy with compose (core + valkey stack)

```bash
mkdir -p ./searxng/core-config/ && cd ./searxng
curl -fsSL \
  -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml \
  -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example
cp -i .env.example .env          # edit .env (ports, host) as needed
docker compose up -d            # starts searxng-core + searxng-valkey
docker compose ps               # confirm ports, e.g. 0.0.0.0:8080->8080/tcp
```

The compose stack runs the web core alongside a Valkey
cache (for rate limiting / bot protection). Access the UI at
`http://localhost:8080`.

### 3. Set the secret key (required)

SearXNG refuses to start the API without a `secret_key`. Generate one and put
it in `core-config/settings.yml`:

```bash
openssl rand -hex 16           # e.g. 1a2b3c...  -> use as secret_key
```

`core-config/settings.yml`:

```yaml
server:
  secret_key: "PASTE_THE_HEX_VALUE_HERE"   # required, from openssl above
search:
  formats:
    - json                             # enable the JSON API (else 403)
    - csv
    - rss
  safe_search: 1
```

Restart: `docker compose down && docker compose up -d`.

### 4. Query with the key

The JSON endpoint is `/search?q=...&format=json`:

```bash
curl 'http://localhost:8080/search?q=searxng&format=json'
```

Notes:
- `categories` param picks engines (e.g. `general`, `science`, `it`).
- `time_range` = `day|month|year` for freshness.
- If exposing remotely, protect with a reverse proxy and enable the
  `api:` key check so only keyed clients can hit the JSON endpoint.
- Use the JSON results to feed further `webfetch` of the top `url` hits.

### 5. Troubleshooting

- Logs: `docker compose logs -f core`
- Shell: `docker compose exec -it --user root core /bin/sh -l`
- Update: `docker compose down && docker compose pull && docker compose up -d`
- Docs: https://docs.searxng.org/admin/installation-docker.html

## Fallback search backend: Serper (Google API)

If SearXNG is unavailable (Docker not running, no key allowed, slow or
unreachable), fall back to Serper's Google Search API. The key is **not**
stored in this repo — it lives in the `SERPER_API_KEY` environment variable
(Windows user env var, set once via `setx SERPER_API_KEY "<key>"`; restart
shells/opencode afterwards so it is inherited).

On this Linux machine (`dgx` workstation) the key is already configured in
`~/.bashrc` (one-time: `echo 'export SERPER_API_KEY="<key>"' >> ~/.bashrc`,
then `source ~/.bashrc` or open a new shell). If the var is missing in a new
shell/session, `source ~/.bashrc` or export it inline before calling the script.

### Query

Use the prebuilt script (no code generation needed — it is ready to run):

```bash
python .opencode/skills/web-research/storage/serper.py "your query"
python .opencode/skills/web-research/storage/serper.py "your query" --fresh week --num 10
python .opencode/skills/web-research/storage/serper.py "your query" --json | jq
```

Or raw `curl`:

```bash
curl -s -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"q": "searxng docker example", "gl": "us", "hl": "en", "num": 10}'
```

Notes:
- `gl` / `hl` control country and language (`us` / `en` by default).
- `num` caps result count (default 10).
- `tbs` adds freshness (e.g. `qdr:d` = past day, `qdr:w` = past week).
- Response fields: `organic` (title/link/snippet), `answerBox`, `knowledgeGraph`,
  `news`, `topStories`, `relatedSearches`. Feed the top `organic[].link` hits
  into `webfetch`.
- The key is charged per query; use Serper only when SearXNG is unavailable.
- The script fails fast with exit code 3 if `SERPER_API_KEY` is unset.
