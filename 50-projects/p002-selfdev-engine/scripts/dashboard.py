"""Self* engine dashboard - zero-dependency live view of engine runs (stdlib only).

Serves a small web UI over ``ENGINE_STATE/runs/<run-id>/`` so you can watch a
night-cycle run (or re-read a finished one) from any browser on the LAN. No
deps, no build: ``python3 scripts/dashboard.py`` then open the printed URL.

Endpoints
---------
GET  /                    the dashboard HTML page.
GET  /api/runs            JSON list of runs (id + meta + status summary).
GET  /api/runs/<id>       JSON snapshot of one run (meta, per-cycle phases,
                          workers, plan, trail, state, reports, agent-log tails).

The HTML page auto-refreshes ``/api/runs/<id>`` on a timer, so a live run
updates in place without reload. All reads are defensive: files that do not
exist yet (a run is written incrementally) are simply absent from the payload.
"""

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_RUNS_DIR = PROJECT / "ENGINE_STATE" / "runs"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8899


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def read_meta(rd):
    try:
        return json.loads((rd / "meta.json").read_text())
    except Exception:
        return {}


def read_lines(path):
    """Read a file defensively, returning a list of lines (empty on error)."""
    try:
        return path.read_text(errors="replace").splitlines()
    except Exception:
        return []


def read_text(path):
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


def parse_jsonl(path):
    """Parse a .jsonl file into a list of dicts, skipping malformed lines."""
    out = []
    for ln in read_lines(path):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def tail_text(path, n=60):
    lines = read_lines(path)
    return "\n".join(lines[-n:])


def discover_runs(runs_dir):
    """All run ids (newest first) plus a per-run meta + status summary."""
    runs = []
    for rd in sorted(runs_dir.iterdir(), key=lambda p: p.name):
        if not rd.is_dir() or not (rd / "meta.json").exists():
            continue
        m = read_meta(rd)
        runs.append({
            "id": rd.name,
            "repo": m.get("repo"),
            "feature": m.get("feature"),
            "cycle": m.get("cycle"),
            "round": m.get("round"),
            "max_round": m.get("max_round"),
            "status": m.get("status"),
            "good": m.get("good"),
            "created": m.get("created"),
            "issue": m.get("issue"),
        })
    # newest first by dir name (run ids are UTC timestamps)
    runs.sort(key=lambda r: r["id"], reverse=True)
    return runs


def is_agent_log(name):
    return name.startswith("agent-") and name.endswith(".log")


def _cycle_sort_key(c):
    parts = str(c).split(".")
    return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)


def build_run(runs_dir, rid):
    """Snapshot one run as a JSON-serialisable dict (defensive)."""
    rd = runs_dir / rid
    if not rd.is_dir():
        return None
    meta = read_meta(rd)
    out = {"id": rid, "meta": meta}

    out["plan"] = read_text(rd / "plan.md")
    out["trail"] = read_text(rd / "trail.md")
    out["handoff"] = read_text(rd / "handoff.md")
    out["interview"] = read_text(rd / "interview.md")

    # reports + next-cycle docs
    out["reports"] = {}
    out["next_cycles"] = {}
    for p in sorted(rd.iterdir()):
        if p.is_file():
            m = re.match(r"report-(\d.*)\.md$", p.name)
            if m:
                out["reports"][m.group(1)] = read_text(p)
                continue
            m = re.match(r"next-cycle-(\d.*)\.md$", p.name)
            if m:
                out["next_cycles"][m.group(1)] = read_text(p)

    # phases + workers + state per cycle (cycle = "1", "2", "2.1", ...)
    phases = {}
    workers = {}
    states = {}
    for p in sorted(rd.iterdir()):
        if not p.is_file():
            continue
        m = re.match(r"phases-(.+)\.jsonl$", p.name)
        if m:
            phases[m.group(1)] = parse_jsonl(p)
            continue
        m = re.match(r"workers-(.+)\.jsonl$", p.name)
        if m:
            workers[m.group(1)] = parse_jsonl(p)
            continue
        m = re.match(r"state-(.+)\.json$", p.name)
        if m:
            states[m.group(1)] = json.loads(
                p.read_text(errors="replace") or "{}"
            )
    # merge all phase records into one chronological list
    all_phases = []
    for cyc, recs in phases.items():
        for r in recs:
            r = dict(r)
            r["_cycle"] = cyc
            all_phases.append(r)
    all_phases.sort(key=lambda r: (_cycle_sort_key(r.get("_cycle", "")),
                                   str(r.get("start", ""))))
    out["phases"] = all_phases

    # merge all worker records into one list (each row is one *record*; the UI
    # collapses by branch, keeping the latest status per task)
    all_workers = []
    for cyc, recs in workers.items():
        for r in recs:
            r = dict(r)
            r["_cycle"] = cyc
            all_workers.append(r)
    all_workers.sort(key=lambda r: (_cycle_sort_key(r.get("_cycle", "")),
                                    r.get("worker") or 0,
                                    str(r.get("start", ""))))
    out["workers"] = all_workers
    out["states"] = states

    # agent logs (tail) + phase/worker files present, for live-run visibility
    out["agent_logs"] = {}
    for p in sorted(rd.iterdir()):
        if p.is_file() and is_agent_log(p.name):
            out["agent_logs"][p.name] = tail_text(p, 80)

    out["_files"] = sorted(p.name for p in rd.iterdir() if p.is_file())
    return out


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
ROUTES = "/api/runs", "/api/runs/<id>"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        runs_dir = DEFAULT_RUNS_DIR
        if path == "/" or path == "/index.html":
            html = (Path(__file__).resolve().parent / "dashboard.html")
            if not html.exists():
                self._send(500, "dashboard.html missing next to dashboard.py")
                return
            self._send(200, html.read_text(), "text/html; charset=utf-8")
            return
        if path == "/api/runs":
            self._send(200, json.dumps({"runs": discover_runs(runs_dir)}))
            return
        m = re.match(r"^/api/runs/(.+)$", path)
        if m:
            rid = m.group(1)
            data = build_run(runs_dir, rid)
            if data is None:
                self._send(404, json.dumps({"error": "unknown run"}))
                return
            self._send(200, json.dumps(data))
            return
        self._send(404, json.dumps({"error": "not found"}))


def main(argv=None):
    argv = list(sys.argv) if argv is None else list(argv)
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--host") and i + 1 < len(argv):
            host = argv[i + 1]
            i += 2
        elif a in ("-p", "--port") and i + 1 < len(argv):
            port = int(argv[i + 1])
            i += 2
        else:
            i += 1
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"engine dashboard: http://{host}:{port}/")
    print(f"  runs dir:       {DEFAULT_RUNS_DIR}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
