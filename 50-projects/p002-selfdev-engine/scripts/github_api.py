"""Thin GitHub REST client (python stdlib only).

Auth: read at call-time from $GITHUB_TOKEN (or $GH_TOKEN). Never hardcode keys.
"""
import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"


def _headers():
    h = {"X-GitHub-Api-Version": "2022-11-28", "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def request(method, path, data=None):
    url = path if path.startswith("http") else API + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        snippet = e.read().decode(errors="replace")[:400]
        raise RuntimeError(f"github {method} {path} -> {e.code}: {snippet}")


def default_branch(repo):
    return request("GET", f"/repos/{repo}")[1].get("default_branch", "main")


def create_issue(repo, title, body, labels=None):
    d = {"title": title, "body": body, "labels": labels or []}
    return request("POST", f"/repos/{repo}/issues", d)[1]


def add_issue_comment(repo, issue_no, body):
    return request("POST", f"/repos/{repo}/issues/{issue_no}/comments", {"body": body})[1]


def get_issue_comments(repo, issue_no):
    return request("GET", f"/repos/{repo}/issues/{issue_no}/comments")[1]


def list_issues(repo, state="open", labels=None, limit=30):
    q = f"state={state}&per_page=100"
    if labels:
        q += "&labels=" + ",".join(labels)
    return request("GET", f"/repos/{repo}/issues?{q}")[1][:limit]


def list_branches(repo):
    return [b["name"] for b in request("GET", f"/repos/{repo}/branches?per_page=100")[1]]


def create_pr(repo, title, head, base, body):
    d = {"title": title, "head": head, "base": base, "body": body}
    return request("POST", f"/repos/{repo}/pulls", d)[1]


def close_pr(repo, pr_no):
    return request("PATCH", f"/repos/{repo}/pulls/{pr_no}", {"state": "closed"})[1]


def close_issue(repo, issue_no):
    return request("PATCH", f"/repos/{repo}/issues/{issue_no}", {"state": "closed"})[1]


def delete_branch(repo, branch):
    return request("DELETE", f"/repos/{repo}/git/refs/heads/{branch}")[0]


def get_pulls(repo, state="open", head=None):
    url = f"/repos/{repo}/pulls?state={state}&per_page=100"
    if head:
        url += f"&head={head.replace('/', '%2F')}"
    return request("GET", url)[1]


def merge_pr(repo, pr_no, method="merge"):
    return request("PUT", f"/repos/{repo}/pulls/{pr_no}/merge", {"merge_method": method})[1]


def get_checks_for_head(repo, sha):
    try:
        d = request("GET", f"/repos/{repo}/commits/{sha}/check-runs")[1]
        return [c["status"] + "/" + c["conclusion"] for c in d.get("check_runs", [])]
    except RuntimeError:
        return []
