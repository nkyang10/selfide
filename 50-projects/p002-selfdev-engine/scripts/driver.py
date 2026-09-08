#!/usr/bin/env python3
"""p002 self* development engine — driver CLI (stdlib only).

Subcommands (see features/FE-002-operating-cycle/spec.md):
  handoff   file the epic + start the clarifying interview
  clarify   answer a round; engine folds answers in, asks next questions / plans
  run       execute the FE-001 pipeline on a clone (think→complete→test→review→ship)
  report    write + post the morning report
  cycle     handoff + clarify + run + report in one shot

Auth: GitHub token read at run time from $GITHUB_TOKEN (never stored to disk).
Dry-run: `--dry-run` prints the shell it would execute and performs no network/git.
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh  # noqa: E402


def utc(tag=""):
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M") + tag


def deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config():
    defaults = {
        "target_repo": "nkyang10/cloud-pos-system",
        "opencode_bin": os.path.expanduser("~/.opencode/bin/opencode"),
        "workdir": "/tmp/opencode/engine-work",
        "state_dir": "ENGINE_STATE",
        "model": "",
        "roles": ["assembler", "engineer", "qa", "reviewer", "researcher", "designer", "retro"],
        "engineer": {"max_parallel": 2},
        "researcher": {"on": True},
        "gates": {"plan": "auto", "review": "auto_merge", "ship": "pr", "qa_iterations": 3, "review_rounds": 2},
        "require_mgmt": {"interview": True, "max_question_rounds": 2},
    }
    cfg = PROJECT / "config" / "engine.json"
    if cfg.exists():
        return deep_merge(defaults, json.loads(cfg.read_text()))
    return defaults


def run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def run_dir(cfg, rid):
    return PROJECT / cfg["state_dir"] / "runs" / rid


def read_meta(cfg, rid):
    p = run_dir(cfg, rid) / "meta.json"
    if not p.exists():
        sys.exit(f"run {rid} not found at {p}")
    return json.loads(p.read_text())


def write_meta(cfg, rid, meta):
    p = run_dir(cfg, rid)
    p.mkdir(parents=True, exist_ok=True)
    (p / "meta.json").write_text(json.dumps(meta, indent=2))


def checkout_path(cfg, repo):
    name = repo.split("/")[-1]
    return Path(cfg["workdir"]) / name

def _git_url(repo):
    """Repo clone/push URL for git operations — GitHub by default, or a local Gitea root via env."""
    root = os.environ.get("ENGINE_GIT_ROOT")
    return f"{root}/{repo}.git" if root else f"https://github.com/{repo}.git"


def proxy_note():
    if os.environ.get("ENGINE_GITEA") == "1":
        print("· repo layer: GITEA", flush=True)


def git(args, cwd=None, dry=False, token=None, retries=3, timeout=200):
    env = os.environ.copy()
    if token:
        b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        base = (os.environ.get("ENGINE_GIT_ROOT") or "https://github.com").rstrip("/")
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = f"http.{base}/.extraHeader"
        env["GIT_CONFIG_VALUE_0"] = f"Authorization: Basic {b64}"
    cmd = ["git", *args]
    if dry:
        print("DRY  $ git " + " ".join(args) + f"  (cwd={cwd})")
        return
    for attempt in range(retries):
        try:
            subprocess.run(cmd, cwd=cwd, check=True, env=env, timeout=timeout)
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if attempt == retries - 1:
                raise
            print(f"· git {args[:2]} failed (network?) — retry {attempt + 1}/{retries} …", flush=True)
            time.sleep(3 * (attempt + 1))


def _clean_task_slot(co, tb, wt):
    """Reclaim a task worktree slot left over from a crashed/previous run: drop the worktree first
    (else its branch stays checked out and -D refuses), then delete the stale branch ref, then the dir."""
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=str(co), capture_output=True)
    subprocess.run(["git", "branch", "-D", tb], cwd=str(co), capture_output=True)
    if Path(wt).exists():
        shutil.rmtree(wt, ignore_errors=True)


def agent_cmd(cfg, agent, message, cwd):
    """Build the opencode argv. IMPORTANT: `--dir` MUST be absolute — a relative one makes opencode
    fail to load the role agent when the child is exec'd without a shell (Unexpected server error)."""
    cmd = [cfg["opencode_bin"], "run", message, "--agent", agent, "--dir", str(Path(cwd).resolve()), "--auto", "--format", "json"]
    if cfg.get("model"):
        cmd += ["-m", cfg["model"]]
    return cmd


def run_agent(cfg, agent, message, cwd, dry=False, timeout=900, logfile=None, attempts=2):
    """Run one role agent to completion. Returns True only if it exits 0 (after one retry)."""
    if dry:
        print(f"DRY  run agent [{agent}] <task> …")
        return True
    for i in range(attempts):
        out = None
        want = None
        try:
            if logfile is not None:
                Path(logfile).parent.mkdir(parents=True, exist_ok=True)
                out = open(logfile, "ab")
            p = subprocess.Popen(agent_cmd(cfg, agent, message, cwd),
                                 stdout=out or subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=str(cwd))
            want = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                p.kill()
            except Exception:
                pass
            print(f"✗ agent [{agent}] TIMEOUT > {timeout}s — aborting this phase", flush=True)
            return False
        finally:
            if out:
                out.close()
        if want == 0:
            return True
        print(f"✗ agent [{agent}] exit code {want} (attempt {i + 1}/{attempts})", flush=True)
    return False


def spawn_agent(cfg, agent, message, cwd, logfile=None):
    """Non-blocking spawn for parallel agents (engineers, researcher)."""
    out = None
    if logfile is not None:
        Path(logfile).parent.mkdir(parents=True, exist_ok=True)
        out = open(logfile, "ab")
    p = subprocess.Popen(agent_cmd(cfg, agent, message, cwd),
                         stdout=out or subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=str(cwd))
    p._engine_log = out   # caller closes after wait
    return p


def _commit_if_dirty(wt, msg):
    st = subprocess.run(["git", "status", "--porcelain"], cwd=str(wt), capture_output=True, text=True).stdout.strip()
    if st:
        subprocess.run(["git", "add", "-A"], cwd=str(wt), check=True)
        subprocess.run(["git", "-c", "user.name=engine", "-c", "user.email=engine@localhost", "commit", "-m", msg],
                       cwd=str(wt), check=True)


def _has_commit(wt, branch, base):
    """True if the branch has ≥1 commit beyond the remote base (proves the engineer actually delivered)."""
    st = subprocess.run(["git", "rev-list", "--count", f"origin/{base}..{branch}"], cwd=str(wt),
                        capture_output=True, text=True)
    return st.returncode == 0 and st.stdout.strip().isdigit() and int(st.stdout) > 0


def _git_commit_if_dirty(co, msg):
    st = subprocess.run(["git", "status", "--porcelain"], cwd=str(co), capture_output=True, text=True).stdout.strip()
    if st:
        git(["add", "-A"], cwd=str(co))
        git(["-c", "user.name=engine", "-c", "user.email=engine@localhost", "commit", "-m", msg], cwd=str(co))


def board(cfg, meta, text, dry=False, token=None):
    """Post a note to the epic issue (the shared board)."""
    if dry:
        print(f"DRY  board comment on {meta['repo']}#{meta['issue']}: {text[:80]}…")
        return
    gh.add_issue_comment(meta["repo"], meta["issue"], text)


PERMS_FULL = "  read: allow\n  glob: allow\n  grep: allow\n  write: allow\n  edit: allow\n  bash: allow"
PERMS_GIT = "  read: allow\n  glob: allow\n  grep: allow\n  write: allow\n  bash: allow"
AGENT_FRONTMATTER = {
    "assembler": "mode: all\npermission:\n" + PERMS_GIT,
    "engineer": "mode: all\npermission:\n" + PERMS_FULL,
    "qa": "mode: all\npermission:\n" + PERMS_FULL,
    "reviewer": "mode: all\npermission:\n" + PERMS_GIT,
    "researcher": "mode: all\npermission:\n" + PERMS_FULL,
    "designer": "mode: all\npermission:\n" + PERMS_GIT,
    "retro": "mode: all\npermission:\n  read: allow\n  glob: allow\n  grep: allow\n  write: allow\n  edit: allow",
}


def materialize_agents(cfg, cwd, dry=False):
    """Generate .opencode/agent/<role>.md in the worktree from prompts/<role>.md (canonical briefs)."""
    prompts = PROJECT / "prompts"
    dst = cwd / ".opencode" / "agent"
    if dry:
        print(f"DRY  generate {dst}/ from {prompts}/*.md")
        return
    dst.mkdir(parents=True, exist_ok=True)
    for role in cfg["roles"]:
        brief = prompts / f"{role}.md"
        if not brief.exists():
            continue
        fm = AGENT_FRONTMATTER.get(role, "mode: all")
        (dst / f"{role}.md").write_text(f"---\nname: {role}\ndescription: p002 role agent: {role}\n{fm}\n---\n\n" + brief.read_text())


def heuristic_questions(feature, work):
    return [
        f"Target: '{feature}'. What is the single MUST-HAVE outcome for the first usable version (happy path only)?",
        f"Stack/language for the project? (if unset, we default to Python 3 + no external deps unless you say otherwise.)",
        f"Is there an existing design, schema, or API shape to follow, or should the Assembler invent a reasonable one?",
        f"Where should the result be deployed/served, if at all, in this cycle? (default: local CLI/library, no infra.)",
    ]


def log_run(cfg, rid, phase, note):
    p = run_dir(cfg, rid) / "trail.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(f"- [{utc()}] {phase}: {note}\n")


# ----------------------------- subcommands -----------------------------

def cmd_handoff(a, cfg, dry, token):
    rid = a.run or run_id()
    rd = run_dir(cfg, rid)
    rd.mkdir(parents=True, exist_ok=True)
    targets = [t.strip() for t in (getattr(a, "targets", "") or "").split("|") if t.strip()]
    meta = {
        "run_id": rid, "repo": a.repo or cfg["target_repo"], "feature": a.feature,
        "work": a.work, "issue": None, "cycle": 0, "good": False, "targets": targets,
        "round": 0, "max_round": cfg["require_mgmt"]["max_question_rounds"],
        "created": utc(),
    }
    (rd / "handoff.md").write_text(
        f"# Hand-off {rid}\n\n- work: {a.work}\n- target feature/workflow: {a.feature}\n- repo: {meta['repo']}\n"
    )
    if a.repo and meta["repo"] != a.repo:
        meta["repo"] = a.repo
    log_run(cfg, rid, "handoff", f"epic '{a.feature}' on {meta['repo']}")

    if dry:
        print("DRY  create epic issue: [epic] " + a.feature)
        questions = heuristic_questions(a.feature, a.work)
        print("DRY  interview: " + "; ".join(questions))
        (rd / "interview.md").write_text(
            f"# Interview {rid}\n\n## Round 1 — engine questions\n\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
            + "\n\n_Status: awaiting user answers (DRY)._\n"
        )
        write_meta(cfg, rid, meta)
        return

    issue = gh.create_issue(meta["repo"], f"[epic] {a.feature}",
                            f"**{a.work}**\n\nTarget feature/workflow: {a.feature}\n\n_(engine {rid})_")
    meta["issue"] = issue["number"]
    questions = heuristic_questions(a.feature, a.work)
    (rd / "interview.md").write_text(
        f"# Interview {rid}\n\n## Round 1 — engine questions\n\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
        + "\n\n_Status: awaiting user answers._\n"
    )
    board(cfg, meta, f"**engine {rid}** hand-off received. Asking {len(questions)} clarifying question(s). "
                     "Answer inline and I'll fold them in before kickoff.", dry=False, token=token)
    write_meta(cfg, rid, meta)
    print(f"epic #{meta['issue']} created on {meta['repo']}; interview started (round 1 of {meta['max_round']}).")
    print("→ continue: python3 scripts/driver.py clarify --run " + rid + " --answer \"...\"")


def cmd_clarify(a, cfg, dry, token):
    rid = a.run
    meta = read_meta(cfg, rid)
    rd = run_dir(cfg, rid)
    meta["round"] += 1
    log_run(cfg, rid, "clarify", f"round {meta['round']} answer: {a.answer[:60]!r}")

    good = meta["round"] >= meta["max_round"] or a.good
    if good:
        (rd / "plan.md").write_text(
            f"# Plan {rid} (round {meta['round']}, marked good)\n\n- feature: {meta['feature']}\n- work: {meta['work']}\n"
            f"- last user answer: {a.answer}\n\n## Tasks (provisional)\n1. scaffold project skeleton\n2. core feature\n3. tests\n"
        )
        meta["good"] = True
        (rd / "interview.md").write_text(
            (rd / "interview.md").read_text() + f"\n## Round {meta['round']} — user: {a.answer}\n\n_Status: GOOD (ready to kickoff) — plan drafted._\n"
        )
        board(cfg, meta, f"**engine {rid}** round {meta['round']} recorded. Plan marked GOOD — ready for `run` (cycle kickoff).", dry=dry, token=token)
    else:
        questions = heuristic_questions(meta["feature"], meta["work"])
        nxt = questions[meta["round"] % len(questions)]
        (rd / "interview.md").write_text(
            (rd / "interview.md").read_text() + f"\n## Round {meta['round']} — user: {a.answer}\n\n_engine next question: {nxt}_\n"
        )
        board(cfg, meta, f"**engine {rid}** round {meta['round']} recorded. One more question: {nxt}", dry=dry, token=token)
    write_meta(cfg, rid, meta)
    if good:
        print(f"plan marked GOOD. → start: python3 scripts/driver.py run --run {rid} --cycle 1")
    else:
        print(f"round {meta['round']}/{meta['max_round']} recorded. → answer next: ... clarify --run {rid} --answer \"...\"  (or --good to force plan)")


def cmd_run(a, cfg, dry, token):
    rid = a.run
    meta = read_meta(cfg, rid)
    if not meta.get("good"):
        if dry:
            print("DRY  (run skipped: plan not marked good; use `clarify --good` first)")
        else:
            sys.exit("plan not marked good yet — run `clarify --good` or answer the final round first.")
    repo = meta["repo"]
    base = gh.default_branch(repo) if not dry else "main"
    branch = f"engine/{rid}"
    co = checkout_path(cfg, repo)
    rd = run_dir(cfg, rid)
    phases_fp = rd / f"phases-{a.cycle}.jsonl"
    worker_fp = rd / f"workers-{a.cycle}.jsonl"
    state_fp = rd / f"state-{a.cycle}.json"
    state = {}
    if state_fp.exists():
        try:
            state = json.loads(state_fp.read_text())
        except Exception:
            state = {}
    done = {k for k, v in state.items() if isinstance(v, dict) and v.get("status") == "done"}
    resuming = bool(done)
    if resuming:
        print(f"· RESUME: {len(done)} phase(s) already done {sorted(done)} — continuing from the next incomplete", flush=True)

    def _phase(role):
        """Returns (finish_fn_or_None, skipped). skipped=True when this phase already completed in an
        earlier (crashed) attempt of the same cycle — the event-sourced resume gate."""
        st = state.get(role)
        if st and st.get("status") == "done":
            print(f"· resume-skip phase[{role}]", flush=True)
            return None, True
        rec = {"phase": role, "cycle": a.cycle, "start": utc()}

        def _finish(ok, note=""):
            rec["end"] = utc()
            rec["ok"] = bool(ok)
            rec["note"] = note
            with phases_fp.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"· phase[{role}] {'ok' if ok else 'FAIL'} {note}", flush=True)
            state[role] = {"status": "done" if ok else "failed",
                           "start": rec["start"], "end": rec["end"], "note": note}
            state_fp.write_text(json.dumps(state, indent=2))    # event-sourced: idempotent, survives crashes
            return bool(ok)
        return _finish, False

    meta["cycle"] = a.cycle
    meta["status"] = f"cycle{a.cycle}-start"
    write_meta(cfg, rid, meta)

    if dry:
        print(f"DRY  clone {repo} -> {co}; branch {branch}")
        print(f"DRY  phases: think→complete→test→review→ship (base {base})")
        return

    # 1. clone/refresh — on a DIFFER-AHEAD resume, keep the existing worktree/branches (partial work is usable)
    if not resuming and not dry:
        try:
            gh.delete_branch(repo, branch)      # drop stale engine/<rid> so re-push stays fast-forward
        except RuntimeError:
            pass
    if not (co / ".git").exists():
        git(["clone", _git_url(repo), str(co)], token=token)
    else:
        git(["fetch", "origin"], cwd=str(co))
    git(["remote", "set-url", "origin", _git_url(repo)], cwd=str(co), dry=dry)   # pin the active repo layer (Gitea/GitHub)
    cur = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(co),
                         capture_output=True, text=True).stdout.strip()
    git(["reset", "--hard", "HEAD"], cwd=str(co))        # drop any pending merge-conflict index before branching
    if not resuming or cur != branch:
        git(["checkout", "-B", branch, "origin/" + base], cwd=str(co))
    materialize_agents(cfg, co)
    seed_targets(meta, co)
    _git_commit_if_dirty(co, f"engine {rid}: bootstrap agents + plan")   # cycle 2+ already has these on main
    git(["push", "-f", "-u", "origin", branch], cwd=str(co), token=token)   # engine branch is disposable; force keeps restart/resume simple
    if not resuming:
        board(cfg, meta, f"**engine {rid}** cycle {a.cycle} kickoff — branch `{branch}` created; plan + role agents in place.", dry=False, token=token)

    # 2. think — if the Assembler doesn't produce a plan, abort loudly (no silent empty cycle)
    _fin, _skip = _phase("assembler")
    if not _skip and not run_agent(cfg, "assembler",
                       f"Read the context on this branch: if ENGINE_PLAN/{rid}/NEXT-CYCLE.md exists, treat its "
                       f"proposals as the approved input for THIS cycle. Produce ENGINE_PLAN/{rid}/PRD.md, "
                       f"design.md and tasks.md for the target feature '{meta['feature']}' in this repo. "
                       f"Minimum: PRD.md with acceptance criteria and tasks.md with 1-5 ordered tasks, one "
                       f"per line starting with '- '.",
                       co, logfile=rd / f"agent-assembler-{a.cycle}.log", timeout=1500):
        log_run(cfg, rid, f"cycle{a.cycle}-assembler", "FAILED")
        board(cfg, meta, f"**engine {rid}** ✗ Assembler failed — cycle {a.cycle} aborted (no plan produced).", dry=False, token=token)
        _fin(False, "no plan produced")
        meta["status"] = f"cycle{a.cycle}-abort-assembler"
        write_meta(cfg, rid, meta)
        sys.exit(f"assembler agent failed for run {rid}")
    elif _skip:
        pass
    else:
        _fin(True, "plan produced")
        _git_commit_if_dirty(co, f"engine {rid}: plan")
        git(["push", "origin", branch], cwd=str(co), token=token)
        board(cfg, meta, f"**engine {rid}** Assembler plan committed under `ENGINE_PLAN/{rid}/`.", dry=False, token=token)

    # 3. complete — ENGINEERS IN PARALLEL (one isolated git worktree per task); each exit code and commit is checked
    tasks_md = co / "ENGINE_PLAN" / rid / "tasks.md"
    task_lines = []
    if tasks_md.exists():
        task_lines = [l.strip("- \t") for l in tasks_md.read_text().splitlines() if l.strip().startswith(("-", "1", "2", "3", "4", "5"))]
    task_lines = [t for t in task_lines if t][:5]
    if not task_lines:
        log_run(cfg, rid, f"cycle{a.cycle}-plan", "no tasks parsed from tasks.md")
        board(cfg, meta, f"**engine {rid}** ✗ plan produced no parseable tasks — cycle {a.cycle} aborted.", dry=False, token=token)
        meta["status"] = f"cycle{a.cycle}-abort-tasks"
        write_meta(cfg, rid, meta)
        sys.exit(f"no tasks parsed for run {rid}")
    _fin_eng, _skip_eng = _phase("engineers")
    ok_wts = []
    research_proc = None
    res_dir = Path(cfg["workdir"]) / f"res-{rid}"
    worker_fp = rd / f"workers-{a.cycle}.jsonl"
    worker_rows = []
    if not _skip_eng:
        max_par = max(1, cfg.get("engineer", {}).get("max_parallel", 2))
        ok_wts = []
        research_proc = None
        res_dir = Path(cfg["workdir"]) / f"res-{rid}"
        for i, task in enumerate(task_lines, 1):
            tb = f"engine/{rid}-t{i}-c{a.cycle}"            # per-cycle name: no clash with previous cycles' (deleted) task branches
            wt = Path(cfg["workdir"]) / f"wt-{rid}-t{i}"
            _clean_task_slot(co, tb, wt)
            git(["worktree", "add", "-b", tb, str(wt), branch], cwd=str(co))
        wts = [(i, t, Path(cfg["workdir"]) / f"wt-{rid}-t{i}", f"engine/{rid}-t{i}-c{a.cycle}") for i, t in enumerate(task_lines, 1)]
        if cfg.get("researcher", {}).get("on", True):
            res_dir.mkdir(parents=True, exist_ok=True)
            (res_dir / "CONTEXT.md").write_text(
                f"# Task context\n\n- feature: {meta['feature']}\n- work: {meta['work']}\n"
                f"- run: {rid} on repo {meta['repo']}\n\nProduce ENGINE_RESEARCH.md as in your brief.\n")
            research_proc = spawn_agent(cfg, "researcher",
                                        f"Research the domain of '{meta['feature']}'. Write ENGINE_RESEARCH.md in this dir (real URLs).",
                                        res_dir, logfile=rd / f"agent-researcher-{a.cycle}.log")
        # — WORKER PIPELINE: a ThreadPool runs up to max_parallel engineers concurrently; a slow task no
        #   longer stalls its batch slot; each worker phase is logged (start/end/exit/commits). —
        from concurrent.futures import ThreadPoolExecutor, as_completed
    
        worker_fp = rd / f"workers-{a.cycle}.jsonl"
        worker_rows = []
    
        def _append_worker(rec):
            worker_rows.append(rec)
            with worker_fp.open("a") as f:
                f.write(json.dumps(rec) + "\n")
    
        def _engineer_worker(item):
            i, task, wt, tb = item
            rec = {"worker": i, "role": "engineer", "task": task[:70], "branch": tb,
                   "start": utc(), "end": None, "exit": None, "commits": 0, "status": "failed"}
            _append_worker(rec)
            wlog = rd / f"agent-engineer-t{i}-c{a.cycle}.log"
            p = spawn_agent(cfg, "engineer",
                            f"Implement this ONE task from the plan and commit it as feat(<slug>): {task}",
                            wt, logfile=wlog)
            try:
                rc = p.wait(timeout=3600)
            except subprocess.TimeoutExpired:
                p.kill()
                rc = -1
            if p._engine_log:
                p._engine_log.close()
                p._engine_log = None
            rec["exit"] = rc
            rec["end"] = utc()
            if rc == 0:
                _commit_if_dirty(wt, f"engine {rid} t{i}")
                if _has_commit(wt, tb, base):
                    git(["push", "-u", "origin", tb], cwd=str(wt), token=token)
                    rec["status"] = "done"
                    rec["commits"] = 1
                else:
                    rec["status"] = "no-commits"
            _append_worker(rec)
            return (i, task, wt, tb, rec)
    
        wts = [(i, t, Path(cfg["workdir"]) / f"wt-{rid}-t{i}", f"engine/{rid}-t{i}-c{a.cycle}") for i, t in enumerate(task_lines, 1)]
        ok_wts = []
        with ThreadPoolExecutor(max_workers=max_par) as pool:
            futures = [pool.submit(_engineer_worker, item) for item in wts]
            for fut in as_completed(futures):
                i, task, wt, tb, rec = fut.result()
                if rec["status"] == "done":
                    ok_wts.append((i, task, wt, tb))
                    board(cfg, meta, f"**engine {rid}** Engineer done task {i} ({rec['end']}): {task[:70]}", dry=False, token=token)
                else:
                    board(cfg, meta, f"**engine {rid}** ⚠/✗ Engineer task {i} {rec['status']} (exit {rec['exit']}) — skipped: {task[:60]}", dry=False, token=token)
                    log_run(cfg, rid, f"cycle{a.cycle}-engineer-t{i}", rec["status"])
    ok_wts.sort(key=lambda t: t[0])          # deterministic merge order by task id
    for i, task, wt, tb in ok_wts:
        try:
            git(["merge", "--no-ff", "-m", f"engine {rid}: merge task {i}", tb], cwd=str(co), retries=1)
        except subprocess.CalledProcessError:
            # parallel tasks can touch overlapping files -> retry resolving in the task's favour
            subprocess.run(["git", "merge", "--abort"], cwd=str(co), capture_output=True)
            try:
                git(["merge", "--no-ff", "-X", "theirs", "-m", f"engine {rid}: merge task {i} (theirs)", tb],
                    cwd=str(co), retries=1, timeout=120)
            except subprocess.CalledProcessError:
                subprocess.run(["git", "merge", "--abort"], cwd=str(co), capture_output=True)
                board(cfg, meta, f"**engine {rid}** ⚠ merge conflict on task {i} left out: {task[:60]}", dry=False, token=token)
                continue
        git(["worktree", "remove", "--force", str(wt)], cwd=str(co))
    if ok_wts:
        git(["push", "origin", branch], cwd=str(co), token=token)
        if research_proc is not None:
            _finr, _skipr = _phase("researcher")
            if not _skipr:
                try:
                    research_proc.wait(timeout=3600)
                except subprocess.TimeoutExpired:
                    research_proc.kill()
                if research_proc._engine_log:
                    research_proc._engine_log.close()
                    research_proc._engine_log = None
            findings = res_dir / "ENGINE_RESEARCH.md"
            if not _skipr:
                _finr(findings.exists(), "findings file" if findings.exists() else "no findings")
        if not dry:
            for i, task, wt, tb in wts:
                try:
                    gh.delete_branch(repo, tb)   # housekeeping: merged or failed, the task branches are done
                except RuntimeError:
                    pass
        findings = res_dir / "ENGINE_RESEARCH.md"
        if findings.exists():
            board(cfg, meta, f"**engine {rid}** Researcher findings:\n\n" + findings.read_text()[:2000], dry=dry, token=token)
        elif cfg.get("researcher", {}).get("on", True):
            board(cfg, meta, f"**engine {rid}** Researcher produced no findings this cycle.", dry=dry, token=token)
        if not ok_wts:
            log_run(cfg, rid, f"cycle{a.cycle}-complete", "no tasks completed")
            board(cfg, meta, f"**engine {rid}** ✗ No task completed — cycle {a.cycle} aborted before QA.", dry=False, token=token)
            meta["status"] = f"cycle{a.cycle}-abort-eng"
            write_meta(cfg, rid, meta)
            sys.exit(f"no engineer task succeeded for run {rid}")
        _fin_eng(len(ok_wts) > 0, f"{len(ok_wts)}/{len(task_lines)} tasks merged")
    else:
        pass

    # 4. test (QA) — a failing QA gate blocks the auto-merge
    _fin, _skip = _phase("qa")
    qa_ok = True if _skip else run_agent(cfg, "qa",
                        "Build/fix tests for the implemented feature so the project's test suite passes. "
                        "Run it. If the suite cannot run, say so in a TESTING.md and state the blocker.",
                        co, logfile=rd / f"agent-qa-{a.cycle}.log", timeout=2400)
    if not _skip:
        _fin(qa_ok, "suite green" if qa_ok else "suite failed")
    log_run(cfg, rid, f"cycle{a.cycle}-qa", "ok" if qa_ok else "FAILED")
    _git_commit_if_dirty(co, f"engine {rid}: tests")
    if qa_ok:
        board(cfg, meta, f"**engine {rid}** QA suite passed for this cycle.", dry=False, token=token)
    else:
        board(cfg, meta, f"**engine {rid}** ✗ QA failed — PR will NOT auto-merge this cycle.", dry=False, token=token)

    # 5. review — verdict must be present and APPROVE for auto-merge
    _fin, _skip = _phase("reviewer")
    if not _skip:
        run_agent(cfg, "reviewer",
                  "Review the diff vs base for the target feature; write a verdict file ENGINE_STATE/review.md "
                  "containing a line `verdict: APPROVE` or `verdict: REQUEST_CHANGES`, then your findings.",
                  co, logfile=rd / f"agent-reviewer-{a.cycle}.log", timeout=2400)
        _fin(True, "verdict written")
    log_run(cfg, rid, f"cycle{a.cycle}-review", "done")
    # 5b. design — Research + Design parties propose the NEXT cycle's tasks/refinements (every cycle)
    nxt = co / "ENGINE_PLAN" / rid / "NEXT-CYCLE.md"
    proposals = []
    if cfg.get("designer", {}).get("on", True):
        _fin, _skip = _phase("designer")
        if _skip:
            pass
        else:
            d_ok = run_agent(cfg, "designer",
                             f"Design the next cycle. Read ENGINE_PLAN/{rid}/, the review verdict at ENGINE_STATE/review.md, "
                             f"the researcher findings at {res_dir}/ENGINE_RESEARCH.md (if present), the code shipped this cycle, "
                             f"and the user requirement '{meta['feature']}'. Then write ENGINE_PLAN/{rid}/NEXT-CYCLE.md as in your brief.",
                             co, logfile=rd / f"agent-designer-{a.cycle}.log", timeout=1800)
            _fin(d_ok and nxt.exists(), "NEXT-CYCLE.md" if nxt.exists() else "no proposals")
            if nxt.exists():
                (rd / f"next-cycle-{a.cycle}.md").write_text(nxt.read_text())
                board(cfg, meta, f"**engine {rid}** Workshop proposal → **next cycle**:\n\n" + nxt.read_text()[:1800], dry=False, token=token)
                if not dry:
                    proposals = proposal_issues(meta, co, rd, a.cycle)   # each proposal = its own issue
    seed_repo_meta_files(co)
    git(["add", "-A"], cwd=str(co))
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(co), capture_output=True, text=True).stdout
    if status.strip():
        git(["-c", "user.name=engine", "-c", "user.email=engine@localhost", "commit", "-m", f"engine {rid}: review + next-cycle proposals"], cwd=str(co))
    git(["push", "origin", branch], cwd=str(co), token=token)
    verdict = "missing"
    for rp in (co / "ENGINE_STATE" / "review.md", co / "review.md", co / "REVIEW.md"):
        if rp.exists():
            txt = rp.read_text()
            verdict = "changes" if "REQUEST_CHANGES" in txt.upper() else ("approve" if "APPROVE" in txt.upper() else "unclear")
            break

    # 6. ship — merge only when: gate auto AND QA ok AND reviewer explicitly approved
    proposals_ref = ""
    prq = rd / f"proposals-{a.cycle}.json"
    if prq.exists():
        nums = json.loads(prq.read_text())
        if nums:
            proposals_ref = "\nrelated proposals: " + ", ".join(f"#{n}" for n in nums)
    ship_mode = cfg["gates"].get("ship", "pr")
    _fin, _skip = _phase("ship")
    if _skip:
        merged = True                      # already merged in a prior (crashed) attempt
        pr = {"number": "?"}
    elif ship_mode == "direct_push":
        # bypass the (currently broken) GitHub /pulls REST API: push the engine branch onto main directly.
        # audit trail still lands on the board; PRs can be recreated from the branch later if wanted.
        git(["push", "origin", f"{branch}:{base}", "--force-with-lease"], cwd=str(co), token=token, retries=4)
        merged = True
        pr = {"number": "direct-push"}
        board(cfg, meta, f"**engine {rid}** ⚠ direct-push shipped to `{base}` (PR API unavailable); branch `{branch}` kept for later PR.", dry=False, token=token)
        _fin(merged, "direct-push")
        meta["status"] = f"cycle{a.cycle}-merged"
        write_meta(cfg, rid, meta)
    else:
        time.sleep(4)                                           # let the freshly-pushed ref index before create_pr (avoids GH 500s)
        pr = gh.create_pr(repo, f"[engine/{rid}] {meta['feature']} (cycle {a.cycle})",
                          f"head={meta['repo'].split('/')[-1]}:{branch}", base,
                          f"Automatic run of engine {rid} on cycle {a.cycle} for epic #{meta['issue']}.\n\n"
                          f"plan: ENGINE_PLAN/{rid}/\nQA: {'passed' if qa_ok else 'failed'}\n"
                          f"reviewer verdict: {verdict}{proposals_ref}")
        board(cfg, meta, f"**engine {rid}** cycle {a.cycle} — PR #{pr['number']} opened: {pr['html_url']}", dry=False, token=token)
        gate = cfg["gates"]["review"]
        merged = False
        if gate == "require_human":
            board(cfg, meta, f"**engine {rid}** review gate = human — PR #{pr['number']} left for you to review/merge.", dry=False, token=token)
        elif not qa_ok:
            board(cfg, meta, f"**engine {rid}** QA failed — PR #{pr['number']} left open (no auto-merge).", dry=False, token=token)
        elif verdict != "approve":
            board(cfg, meta, f"**engine {rid}** reviewer: {verdict} — PR #{pr['number']} left open for human review.", dry=False, token=token)
        else:
            gh.merge_pr(repo, pr["number"])
            merged = True
            board(cfg, meta, f"**engine {rid}** merged PR #{pr['number']} into {base}.", dry=False, token=token)
        _fin(merged, f"PR #{pr['number']}")
    meta["status"] = f"cycle{a.cycle}-merged" if merged else f"cycle{a.cycle}-pr-open"
    write_meta(cfg, rid, meta)
    n_done = len([w for w in worker_rows if w.get("status") == "done"])
    print(f"cycle {a.cycle}: {n_done}/{len(worker_rows)} workers done; phases/workers logged -> "
          f"{rd / f'phases-{a.cycle}.jsonl'}, {rd / f'workers-{a.cycle}.jsonl'}", flush=True)


def seed_targets(meta, co):
    """Write ENGINE_STATE/TARGETS.md (unchecked) into the worktree if targets were handed off."""
    if not meta.get("targets"):
        return
    tgt = co / "ENGINE_STATE" / "TARGETS.md"
    if tgt.exists():
        return
    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.write_text("# Engine targets\n\n" + "\n".join(f"- [ ] {t}" for t in meta["targets"]) + "\n")
    print(f"· seeded {len(meta['targets'])} targets -> {tgt.relative_to(co)}", flush=True)


def targets_all_met(co):
    """True when TARGETS.md exists and no line opens with '- [ ]'."""
    tgt = co / "ENGINE_STATE" / "TARGETS.md"
    if not tgt.exists():
        return False
    return not any(l.strip().startswith("- [ ]") or l.strip().startswith("* [ ]") for l in tgt.read_text().splitlines())


def _ship_only_pending(cfg, rid, cyc):
    """True when a failed cycle left all pre-ship phases done — a resume will re-run only the ship step."""
    sf = run_dir(cfg, rid) / f"state-{cyc}.json"
    if not sf.exists():
        return False
    try:
        state = json.loads(sf.read_text())
    except Exception:
        return False
    pre = ["assembler", "engineers", "qa", "reviewer", "designer"]
    return all(state.get(p, {}).get("status") == "done" for p in pre) and state.get("ship", {}).get("status") != "done"


def cmd_marathon(a, cfg, dry, token):
    """Continuous run: repeat cycles until all TARGETS are met or max cycles reached.
    A failed cycle whose ship-step was the only blocker is retried via cheap phase-resume."""
    rid = a.run
    meta = read_meta(cfg, rid)
    repo = meta["repo"]
    co = checkout_path(cfg, repo)
    last = a.start - 1
    consecutive_fail = 0
    for cyc in range(a.start, a.max + 1):
        log_run(cfg, rid, f"marathon-cycle-{cyc}", "begin")
        extra = ["--dry-run"] if dry else []
        rc = subprocess.run([sys.executable, str(Path(__file__)), "run", "--run", rid, "--cycle", str(cyc)] + extra,
                            env=os.environ.copy()).returncode
        if rc == 0:
            consecutive_fail = 0
            last = cyc
            subprocess.run([sys.executable, str(Path(__file__)), "report", "--run", rid, "--cycle", str(cyc)] + extra,
                           env=os.environ.copy())
        else:
            consecutive_fail += 1
            log_run(cfg, rid, f"marathon-cycle-{cyc}", f"FAILED (run rc={rc})")
            if _ship_only_pending(cfg, rid, cyc) and consecutive_fail <= 6:
                print(f"marathon: cycle {cyc} blocked at ship step only — resuming (cheap) …", flush=True)
                time.sleep(90)          # ride out a GitHub /pulls 500-flap window before the next cheap ship retry
                continue          # retry the SAME cycle: resume skips straight to ship
            if consecutive_fail >= 3:
                print(f"marathon abort: {consecutive_fail} consecutive failures", flush=True)
                break
            print(f"marathon: cycle {cyc} failed ({rc}) — small backoff then retry", flush=True)
        if targets_all_met(co):
            print(f"marathon done: all targets met after cycle {last}", flush=True)
            break
        time.sleep(a.min_gap)
    print(f"marathon finished for {rid}: {last} cycles", flush=True)


def proposal_issues(meta, co, rd, cyc):
    """Mirror each next-cycle proposal bullet to its own GitHub issue — visible, queryable, linkable."""
    rid = meta["run_id"]
    nxt = co / "ENGINE_PLAN" / rid / "NEXT-CYCLE.md"
    out = []
    if not nxt.exists():
        return out
    gh.ensure_labels(meta["repo"], ["engine/proposal", "enhancement"])
    for line in nxt.read_text().splitlines():
        l = line.strip()
        if not l.startswith("- "):
            continue
        title = l.lstrip("- ").split("] ")[-1][:70] or l[:70]
        body = (f"Proposal from engine run `{rid}` (cycle {cyc}) → epic #{meta['issue']} "
                f"'{meta['feature']}'.\n\n> {l}\n\nAccepted proposals become the next cycle's tasks "
                f"(see `ENGINE_PLAN/{rid}/NEXT-CYCLE.md`).")
        try:
            iss = gh.create_issue(meta["repo"], f"[proposal] {title}", body, labels=["engine/proposal"])
            out.append(iss["number"])
        except RuntimeError:
            try:
                iss = gh.create_issue(meta["repo"], f"[proposal] {title}", body)
                out.append(iss["number"])
            except RuntimeError:
                pass
    (rd / f"proposals-{cyc}.json").write_text(json.dumps(out))
    return out


def seed_repo_meta_files(co):
    """Give the target repo a proper place to propose features: an issue template."""
    tmpl = co / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml"
    tmpl.parent.mkdir(parents=True, exist_ok=True)
    tmpl.write_text(
        "name: Feature proposal\n"
        "description: Propose a new feature or refinement (engine also files these per cycle)\n"
        "labels: [\"enhancement\"]\n"
        "body:\n"
        "- type: markdown\n"
        "  attributes:\n"
        "    value: |\n"
        "      Please keep the title self-describing (what it is, what it relates to).\n"
        "- type: textarea\n"
        "  attributes:\n"
        "    label: What & why\n"
        "  validations:\n"
        "    required: true\n- type: textarea\n  attributes:\n    label: Acceptance criteria\n"
        "  validations:\n    required: false\n"
    )


def cmd_report(a, cfg, dry, token):
    rid = a.run
    meta = read_meta(cfg, rid)
    rd = run_dir(cfg, rid)
    trail = (rd / "trail.md").read_text() if (rd / "trail.md").exists() else "(no trail)"
    plan = (rd / "plan.md").read_text() if (rd / "plan.md").exists() else "(no plan)"
    next_cycle = (rd / f"next-cycle-{a.cycle}.md").read_text() if (rd / f"next-cycle-{a.cycle}.md").exists() else "(no proposals yet)"
    phases = ""
    pf = rd / f"phases-{a.cycle}.jsonl"
    wf = rd / f"workers-{a.cycle}.jsonl"
    if pf.exists():
        rows = [json.loads(x) for x in pf.read_text().splitlines() if x.strip()]
        phases = "\n".join(f"- {r['phase']}: {'ok' if r.get('ok') else 'FAIL'} ({r['start'][-5:]}→{r['end'][-5:]}) {r.get('note','')}" for r in rows)
    if wf.exists():
        rows = [json.loads(x) for x in wf.read_text().splitlines() if x.strip()]
        done = [r for r in rows if r.get("status") == "done"]
        head = f"- engineers: {len(done)}/{len(rows)} done "
        for r in rows:
            head += f"| t{r['worker']}:{r.get('status')}({r.get('start','')[-5:]}→{r.get('end','')[-5:]})"
        phases += "\n" + head
    text = (
        f"# Morning report {rid} · cycle {a.cycle}\n\n- repo: {meta['repo']}\n- feature: {meta['feature']}\n"
        f"- status: {meta.get('status')}\n\n## Phases (this cycle)\n{phases or '(no phase log yet)'}\n\n"
        f"## Plan\n{plan}\n\n## Research + Design proposals → next cycle\n{next_cycle}\n\n"
        f"## Next (ask the user)\n- Which proposals to accept for cycle {a.cycle + 1}? (reply `clarify --answer ...`) or call it done.\n"
    )
    (rd / f"report-{a.cycle}.md").write_text(text)
    if not dry:
        gh.add_issue_comment(meta["repo"], meta["issue"], text)
    print(text)


def cmd_cycle(a, cfg, dry, token):
    rid = a.run or run_id()
    print("== handoff ==")
    ns = argparse.Namespace(run=rid, work=a.work, feature=a.feature, repo=a.repo)
    cmd_handoff(ns, cfg, dry, token)
    meta = read_meta(cfg, rid)
    if not meta.get("good"):
        print("== clarify (auto-accepting heuristic answers for the demo cycle) ==")
        for _ in range(meta["max_round"]):
            cmd_clarify(argparse.Namespace(run=rid, answer="proceed with sensible defaults", good=True), cfg, dry, token)
    print("== run cycle 1 ==")
    cmd_run(argparse.Namespace(run=rid, cycle=1), cfg, dry, token)
    print("== report ==")
    cmd_report(argparse.Namespace(run=rid, cycle=1), cfg, dry, token)
    print(f"\nDone (dry-run if flagged). run-id: {rid}")


def cmd_probe(a, cfg, dry, token):
    """Live permission probe: exercises every GitHub exchange the role agents make."""
    repo = a.repo or cfg["target_repo"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    tag = f"permprobe/{ts}"
    print(f"probe repo: {repo}")
    ok = lambda cond, what: print(('PASS' if cond else 'FAIL'), '-', what)
    try:
        base = gh.default_branch(repo)
        ok(base in ("main", "master"), f"default_branch -> {base}")
    except RuntimeError as e:
        ok(False, f"default_branch: {e}")
        return
    if dry:
        print("DRY  full probe skipped (net required)")
        return
    try:
        iss = gh.create_issue(repo, f"[engine] perm probe {ts}", "probe artifact, self-closed")
        ok(iss.get("number"), f"create_issue -> #{iss.get('number')}")
        gh.add_issue_comment(repo, iss["number"], "engine probe: comment write OK")
        ok(True, "add_issue_comment OK")
        gh.close_issue(repo, iss["number"])
    except RuntimeError as e:
        ok(False, f"issues/board: {e}")
    try:
        tmp = Path(cfg["workdir"]) / tag.replace("/", "_")
        tmp.mkdir(parents=True, exist_ok=True)
        pb = f"pbase-{ts}"
        git(["clone", "--depth", "1", _git_url(repo), str(tmp / "c")], dry=dry)
        if not dry:
            git(["checkout", "-b", pb, "origin/" + base], cwd=str(tmp / "c"))
            (tmp / "c" / "probe.txt").write_text(f"engine permission probe {ts}\n")
            git(["-c", "user.name=engine", "-c", "user.email=engine@localhost", "add", "-A"], cwd=str(tmp / "c"))
            git(["-c", "user.name=engine", "-c", "user.email=engine@localhost", "commit", "-m", tag], cwd=str(tmp / "c"))
            git(["push", "-u", "origin", pb], cwd=str(tmp / "c"), token=token)
            ok(True, f"git push to {repo} (branch {pb})")
            pr = gh.create_pr(repo, f"[engine] perm probe {ts}", head=f"{repo.split('/')[0]}:{pb}", base=base,
                              body="self-closed by probe")
            ok(pr.get("number"), f"create_pr -> #{pr.get('number')}")
            gh.close_pr(repo, pr["number"])
            gh.delete_branch(repo, pb)
            ok(True, "close_pr + delete_branch OK")
    except RuntimeError as e:
        ok(False, f"pr/push: {e}")
    print("probe complete (issue artifacts: closed)")


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", help="owner/name target repo (overrides config)")
    common.add_argument("--dry-run", action="store_true", help="print the shell, no network/git")
    p = argparse.ArgumentParser(description="p002 self* dev engine driver", parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("handoff", parents=[common]); h.add_argument("--work", required=True); h.add_argument("--feature", required=True); h.add_argument("--run"); h.add_argument("--targets", help="pipe(|)-separated acceptance targets, tracked in ENGINE_STATE/TARGETS.md")
    c = sub.add_parser("clarify", parents=[common]); c.add_argument("--run", required=True); c.add_argument("--answer", default=""); c.add_argument("--good", action="store_true")
    r = sub.add_parser("run", parents=[common]); r.add_argument("--run", required=True); r.add_argument("--cycle", type=int, default=1)
    m = sub.add_parser("report", parents=[common]); m.add_argument("--run", required=True); m.add_argument("--cycle", type=int, default=1)
    q = sub.add_parser("probe", parents=[common])
    mar = sub.add_parser("marathon", parents=[common]); mar.add_argument("--run", required=True); mar.add_argument("--max", type=int, default=30); mar.add_argument("--start", type=int, default=1); mar.add_argument("--min-gap", type=int, default=0, help="(legacy) seconds between cycles; phases already chain with no wait")
    y = sub.add_parser("cycle", parents=[common]); y.add_argument("--work", required=True); y.add_argument("--feature", required=True); y.add_argument("--run")
    return p


def main():
    args = build_parser().parse_args()
    cfg = load_config()
    proxy_note()
    token = os.environ.get("GITEA_TOKEN") if os.environ.get("ENGINE_GITEA") == "1" else (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    if args.cmd in ("handoff", "clarify", "run", "report", "cycle", "marathon") and not args.dry_run and not token:
        sys.exit("GITHUB_TOKEN not set in environment (required for network ops; set it, don't store it).")
    handlers = {"handoff": cmd_handoff, "clarify": cmd_clarify, "run": cmd_run, "report": cmd_report, "cycle": cmd_cycle, "probe": cmd_probe, "marathon": cmd_marathon}
    handlers[args.cmd](args, cfg, args.dry_run, token)


if __name__ == "__main__":
    main()
