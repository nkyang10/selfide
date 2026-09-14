#!/usr/bin/env python3
"""Ready-to-use Serper (Google) search fallback for the web-research skill.

SearXNG is the primary backend (see SKILL.md). When it is unavailable, run this
script to query Serper directly and get clean, fetchable results.

Usage:
    python serper.py "your query"
    python serper.py "your query" --gl us --hl en --num 10
    python serper.py "your query" --fresh day        # qdr:d | week | month | year
    python serper.py "your query" --json             # raw JSON (pipe to jq)

Environment:
    SERPER_API_KEY  required; the Serper API key (never hardcode it here).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error


ENDPOINT = "https://google.serper.dev/search"


def _load_key_from_bashrc():
    """Best-effort fallback: pull SERPER_API_KEY out of ~/.bashrc when the
    agent's non-interactive shell didn't inherit it. Only runs when the env
    var is absent, so a real env var always wins."""
    home = os.path.expanduser("~")
    for rc in (os.path.join(home, ".bashrc"), os.path.join(home, ".profile")):
        try:
            with open(rc, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            continue
        m = re.search(r'^\s*(?:export\s+)?SERPER_API_KEY=["\']?([A-Za-z0-9_\-]+)', content, re.M)
        if m:
            return m.group(1)
    return None


def _get_key():
    key = os.environ.get("SERPER_API_KEY")
    if key:
        return key
    key = _load_key_from_bashrc()
    if key:
        os.environ["SERPER_API_KEY"] = key
    return key


SERPER_API_KEY = _get_key()


def search(query, gl="us", hl="en", num=10, fresh=None):
    key = _get_key()
    if not key:
        sys.stderr.write(
            "Error: SERPER_API_KEY is not set and could not be found in ~/.bashrc.\n"
            "Add: export SERPER_API_KEY=\"<key>\"  to ~/.bashrc\n"
        )
        sys.exit(3)
    payload = {"q": query, "gl": gl, "hl": hl, "num": num}
    if fresh:
        payload["tbs"] = f"qdr:{fresh[0]}"  # d/w/m/y

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "X-API-KEY": key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"Serper HTTP {e.code}: {e.read().decode('utf-8', 'replace')}\n")
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write(f"Serper unreachable: {e.reason}\n")
        sys.exit(2)


def render(data):
    out = []
    if data.get("answerBox"):
        ab = data["answerBox"]
        title = ab.get("title") or ab.get("answer") or ""
        if title:
            out.append(f"ANSWER: {title}")
        snippet = ab.get("snippet") or ab.get("answer")
        if snippet and snippet != title:
            out.append(f"  {snippet}")
    if data.get("knowledgeGraph"):
        kg = data["knowledgeGraph"]
        out.append(f"KG: {kg.get('title', '')} — {kg.get('description', '')}")
    for i, r in enumerate(data.get("organic", []), 1):
        out.append(f"{i}. {r.get('title', '')}")
        out.append(f"   {r.get('link', '')}")
        if r.get("snippet"):
            out.append(f"   {r['snippet']}")
    related = data.get("relatedSearches")
    if related:
        out.append("RELATED: " + ", ".join(s.get("query", "") for s in related))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Serper Google search fallback")
    ap.add_argument("query", help="search query")
    ap.add_argument("--gl", default="us", help="geo country (default us)")
    ap.add_argument("--hl", default="en", help="language (default en)")
    ap.add_argument("--num", type=int, default=10, help="result count")
    ap.add_argument("--fresh", choices=["day", "week", "month", "year"], help="time range")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    data = search(args.query, args.gl, args.hl, args.num, args.fresh)
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else render(data))


if __name__ == "__main__":
    main()
