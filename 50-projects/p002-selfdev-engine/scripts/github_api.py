"""Thin GitHub REST client (python stdlib only).

Auth: read at call-time from $GITHUB_TOKEN (or $GH_TOKEN). Never hardcode keys.
"""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
RETRY_SLEEP = 4


def _is_gitea():
    return os.environ.get("ENGINE_GITEA") == "1"


def _api_base():
    if _is_gitea():
        return os.environ.get("ENGINE_GITEA_BASE", "http://192.168.1.162:3300") + "/api/v1"
    return API


def _headers():
    if _is_gitea():
        tok = os.environ.get("GITEA_TOKEN")
        return {"Authorization": "token " + (tok or ""),
                "Content-Type": "application/json", "Accept": "application/json",
                "X-Gitea-Version": ""}
    h = {"X-GitHub-Api-Version": "2022-11-28",
         "Accept": "application/vnd.github+json",
         "Content-Type": "application/json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def _log(msg):
    print(f"[ghapi] {msg}", flush=True)


def request(method, path, data=None, retries=4):
    url = _api_base() + path if not path.startswith("http") else path
    body = json.dumps(data).encode() if data is not None else None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
                _log(f"{method} {path} OK {r.status} (attempt {attempt + 1})")
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            snippet = e.read().decode(errors="replace")[:400]
            _log(f"{method} {path} HTTP {e.code} attempt {attempt + 1}/{retries + 1} body={snippet.strip()!r}")
            if e.code >= 500 and attempt < retries:      # GitHub flaps: back off exponential to ~2 min total
                wait = RETRY_SLEEP * (2 ** attempt)
                _log(f"{method} {path} retrying in {wait}s")
                time.sleep(wait)
                continue
            if e.code >= 500 and method in ("POST", "PATCH", "PUT"):
                _log(f"{method} {path} trying curl fallback")
                try:
                    r2 = _curl_retry(method, url, data)
                    _log(f"{method} {path} curl fallback OK {r2[0]}")
                    return r2
                except RuntimeError as ce:
                    _log(f"{method} {path} curl fallback FAILED: {ce}")
            raise RuntimeError(f"github {method} {path} -> {e.code}: {snippet}")


def _curl_retry(method, url, data):
    """curl fallback for API endpoints that intermittently 500 depending on the client's request shape."""
    import subprocess
    try:
        if _is_gitea():
            tok = os.environ.get("GITEA_TOKEN") or ""
            cmd = ["curl", "-s", "-X", method, "-H", f"Authorization: token {tok}",
                   "-H", "Accept: application/json", "-H", "Content-Type: application/json"]
        else:
            tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
            cmd = ["curl", "-s", "-X", method, "-H", f"Authorization: Bearer {tok}",
                   "-H", "Accept: application/vnd.github+json", "-H", "Content-Type: application/json",
                   "-H", "X-GitHub-Api-Version: 2022-11-28"]
        if data is not None:
            cmd += ["-d", json.dumps(data)]
        cmd += ["-w", "\n__HTTP__%{http_code}", url]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as e:
        raise RuntimeError(f"curl spawn failed: {e}")
    code = 0
    body = r.stdout
    if "__HTTP__" in r.stdout:
        body, _, code_s = r.stdout.rpartition("__HTTP__")
        code = int(code_s.strip()) if code_s.strip().isdigit() else 0
    _log(f"curl {method} -> rc={r.returncode} http={code} body={body[:80]!r} stderr={r.stderr.strip()[:120]!r}")
    if 200 <= code < 300:
        return code, (json.loads(body) if body.strip() else None)
    raise RuntimeError(f"github {method} {url} -> {code}: {body[:400]}")


def default_branch(repo):
    return request("GET", f"/repos/{repo}")[1].get("default_branch", "main")


def create_issue(repo, title, body, labels=None):
    d = {"title": title, "body": body, "labels": []}
    if labels:
        if _is_gitea():
            d["labels"] = _label_ids(repo, labels)     # Gitea wants [{"id": int}] not names
        else:
            d["labels"] = labels
    return request("POST", f"/repos/{repo}/issues", d)[1]


def _label_ids(repo, names):
    ensure_labels(repo, names)
    try:
        all_l = request("GET", f"/repos/{repo}/labels")[1]
    except RuntimeError:
        return []
    return [l["id"] for l in all_l if l.get("name") in names]


def add_issue_comment(repo, issue_no, body):
    return request("POST", f"/repos/{repo}/issues/{issue_no}/comments", {"body": body})[1]


def get_issue_comments(repo, issue_no, _last=None):
    return request("GET", f"/repos/{repo}/issues/{issue_no}/comments?per_page=100")[1]


def list_issues(repo, state="open", labels=None, limit=30):
    q = f"state={state}&per_page=100"
    if labels:
        q += "&labels=" + ",".join(labels)
    return request("GET", f"/repos/{repo}/issues?{q}")[1][:limit]


def list_branches(repo):
    return [b["name"] for b in request("GET", f"/repos/{repo}/branches?per_page=100")[1]]


def create_pr(repo, title, head, base, body):
    d = {"title": title, "head": head, "base": base, "body": body}
    if _is_gitea():
        d["head"] = head.split(":", 1)[-1]     # Gitea wants the bare branch name; owner prefix 404s
    return request("POST", f"/repos/{repo}/pulls", d)[1]


def close_pr(repo, pr_no):
    return request("PATCH", f"/repos/{repo}/pulls/{pr_no}", {"state": "closed"})[1]


def close_issue(repo, issue_no):
    return request("PATCH", f"/repos/{repo}/issues/{issue_no}", {"state": "closed"})[1]


def delete_branch(repo, branch):
    if _is_gitea():
        return request("DELETE", f"/repos/{repo}/branches/{branch}")[0]
    return request("DELETE", f"/repos/{repo}/git/refs/heads/{branch}")[0]


def ensure_labels(repo, names):
    """Gitea needs labels pre-created (GitHub auto-creates on first use with a label name)."""
    if not _is_gitea():
        return
    try:
        existing = [l["name"] for l in request("GET", f"/repos/{repo}/labels")[1]]
    except RuntimeError:
        return
    for name in names:
        if name in existing:
            continue
        try:
            request("POST", f"/repos/{repo}/labels", {"name": name, "color": "A03623"})
            _log(f"created label {name}")
        except RuntimeError as e:
            _log(f"label {name} create failed: {e}")


def get_pulls(repo, state="open", head=None):
    url = f"/repos/{repo}/pulls?state={state}&per_page=100"
    if head:
        url += f"&head={head.replace('/', '%2F')}"
    return request("GET", url)[1]


def merge_pr(repo, pr_no, method="merge"):
    if _is_gitea():
        return request("POST", f"/repos/{repo}/pulls/{pr_no}/merge", {"Do": method or "merge"})[1]
    return request("PUT", f"/repos/{repo}/pulls/{pr_no}/merge", {"merge_method": method})[1]


def get_checks_for_head(repo, sha):
    try:
        d = request("GET", f"/repos/{repo}/commits/{sha}/check-runs")[1]
        return [c["status"] + "/" + c["conclusion"] for c in d.get("check_runs", [])]
    except RuntimeError:
        return []
