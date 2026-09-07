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
        "roles": ["assembler", "engineer", "qa", "reviewer", "researcher", "retro"],
        "engineer": {"max_parallel": 2},
        "researcher": {"on": True},
        "gates": {"plan": "auto", "review": "auto_merge", "qa_iterations": 3, "review_rounds": 2},
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


def git(args, cwd=None, dry=False, token=None, retries=3, timeout=200):
    env = os.environ.copy()
    if token:
        b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraHeader"
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
    meta = {
        "run_id": rid, "repo": a.repo or cfg["target_repo"], "feature": a.feature,
        "work": a.work, "issue": None, "cycle": 0, "good": False,
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
    meta["cycle"] = a.cycle
    meta["status"] = f"cycle{a.cycle}-start"
    write_meta(cfg, rid, meta)

    if dry:
        print(f"DRY  clone {repo} -> {co}; branch {branch}")
        print(f"DRY  phases: think→complete→test→review→ship (base {base})")
        return

    # 1. clone/refresh
    if not dry:
        try:
            gh.delete_branch(repo, branch)      # drop stale engine/<rid> so re-push stays fast-forward
        except RuntimeError:
            pass
    if not (co / ".git").exists():
        git(["clone", f"https://github.com/{repo}.git", str(co)], token=token)
    else:
        git(["fetch", "origin"], cwd=str(co))
    git(["checkout", "-B", branch, "origin/" + base], cwd=str(co))
    materialize_agents(cfg, co)
    git(["add", "-A"], cwd=str(co))
    git(["-c", "user.name=engine", "-c", "user.email=engine@localhost", "commit", "-m", f"engine {rid}: bootstrap agents + plan"], cwd=str(co))
    git(["push", "-u", "origin", branch], cwd=str(co), token=token)
    board(cfg, meta, f"**engine {rid}** cycle {a.cycle} kickoff — branch `{branch}` created; plan + role agents in place.", dry=False, token=token)

    # 2. think — if the Assembler doesn't produce a plan, abort loudly (no silent empty cycle)
    if not run_agent(cfg, "assembler",
                     f"Read the context. Produce ENGINE_PLAN/{rid}/PRD.md, design.md and tasks.md "
                     f"for the target feature '{meta['feature']}' in this repo. Minimum: PRD.md with acceptance "
                     f"criteria and tasks.md with 1-5 ordered tasks, one per line starting with '- '.",
                     co, logfile=rd / f"agent-assembler-{a.cycle}.log", timeout=1500):
        log_run(cfg, rid, f"cycle{a.cycle}-assembler", "FAILED")
        board(cfg, meta, f"**engine {rid}** ✗ Assembler failed — cycle {a.cycle} aborted (no plan produced).", dry=False, token=token)
        meta["status"] = f"cycle{a.cycle}-abort-assembler"
        write_meta(cfg, rid, meta)
        sys.exit(f"assembler agent failed for run {rid}")
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
    max_par = max(1, cfg.get("engineer", {}).get("max_parallel", 2))
    ok_wts = []
    research_proc = None
    res_dir = Path(cfg["workdir"]) / f"res-{rid}"
    for i, task in enumerate(task_lines, 1):
        tb = f"engine/{rid}-t{i}"                       # flat name: `engine/<rid>/t<n>` clashes with the git ref namespace of `engine/<rid>`
        wt = Path(cfg["workdir"]) / f"wt-{rid}-t{i}"
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
        git(["worktree", "add", "-b", tb, str(wt), branch], cwd=str(co))
    wts = [(i, t, Path(cfg["workdir"]) / f"wt-{rid}-t{i}", f"engine/{rid}-t{i}") for i, t in enumerate(task_lines, 1)]
    if cfg.get("researcher", {}).get("on", True):
        res_dir.mkdir(parents=True, exist_ok=True)
        (res_dir / "CONTEXT.md").write_text(
            f"# Task context\n\n- feature: {meta['feature']}\n- work: {meta['work']}\n"
            f"- run: {rid} on repo {meta['repo']}\n\nProduce ENGINE_RESEARCH.md as in your brief.\n")
        research_proc = spawn_agent(cfg, "researcher",
                                    f"Research the domain of '{meta['feature']}'. Write ENGINE_RESEARCH.md in this dir (real URLs).",
                                    res_dir, logfile=rd / f"agent-researcher-{a.cycle}.log")
    idx = 0
    while idx < len(wts):
        batch = wts[idx:idx + max_par]
        idx += len(batch)
        procs = []
        for i, task, wt, tb in batch:
            procs.append((spawn_agent(cfg, "engineer",
                                      f"Implement this ONE task from the plan and commit it as feat(<slug>): {task}",
                                      wt, logfile=rd / f"agent-engineer-t{i}.log"), i, task, wt, tb))
        for p, i, task, wt, tb in procs:
            try:
                rc = p.wait(timeout=3600)
            except subprocess.TimeoutExpired:
                p.kill()
                rc = -1
            if p._engine_log:
                p._engine_log.close()
                p._engine_log = None
            if rc != 0:
                log_run(cfg, rid, f"cycle{a.cycle}-engineer-t{i}", f"agent exit {rc}")
                board(cfg, meta, f"**engine {rid}** ✗ Engineer task {i} failed (exit {rc}) — task skipped: {task[:60]}", dry=False, token=token)
                continue
            _commit_if_dirty(wt, f"engine {rid} t{i}")
            if not _has_commit(wt, tb, base):
                log_run(cfg, rid, f"cycle{a.cycle}-engineer-t{i}", "no commits produced")
                board(cfg, meta, f"**engine {rid}** ⚠ Engineer task {i} exited 0 but made no commits — skipped: {task[:60]}", dry=False, token=token)
                continue
            git(["push", "-u", "origin", tb], cwd=str(wt), token=token)
            ok_wts.append((i, task, wt, tb))
            board(cfg, meta, f"**engine {rid}** Engineer done task {i}: {task[:70]}", dry=False, token=token)
    for i, task, wt, tb in ok_wts:
        git(["merge", "--no-ff", "-m", f"engine {rid}: merge task {i}", tb], cwd=str(co))
        git(["worktree", "remove", "--force", str(wt)], cwd=str(co))
    if ok_wts:
        git(["push", "origin", branch], cwd=str(co), token=token)
    if research_proc is not None:
        try:
            research_proc.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            research_proc.kill()
        if research_proc._engine_log:
            research_proc._engine_log.close()
            research_proc._engine_log = None
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

    # 4. test (QA) — a failing QA gate blocks the auto-merge
    qa_ok = run_agent(cfg, "qa",
                      "Build/fix tests for the implemented feature so the project's test suite passes. "
                      "Run it. If the suite cannot run, say so in a TESTING.md and state the blocker.",
                      co, logfile=rd / f"agent-qa-{a.cycle}.log", timeout=2400)
    log_run(cfg, rid, f"cycle{a.cycle}-qa", "ok" if qa_ok else "FAILED")
    _git_commit_if_dirty(co, f"engine {rid}: tests")
    if qa_ok:
        board(cfg, meta, f"**engine {rid}** QA suite passed for this cycle.", dry=False, token=token)
    else:
        board(cfg, meta, f"**engine {rid}** ✗ QA failed — PR will NOT auto-merge this cycle.", dry=False, token=token)

    # 5. review — verdict must be present and APPROVE for auto-merge
    run_agent(cfg, "reviewer",
              "Review the diff vs base for the target feature; write a verdict file ENGINE_STATE/review.md "
              "containing a line `verdict: APPROVE` or `verdict: REQUEST_CHANGES`, then your findings.",
              co, logfile=rd / f"agent-reviewer-{a.cycle}.log", timeout=2400)
    log_run(cfg, rid, f"cycle{a.cycle}-review", "done")
    git(["add", "-A"], cwd=str(co))
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(co), capture_output=True, text=True).stdout
    if status.strip():
        git(["-c", "user.name=engine", "-c", "user.email=engine@localhost", "commit", "-m", f"engine {rid}: review artifact"], cwd=str(co))
    git(["push", "origin", branch], cwd=str(co), token=token)
    verdict = "missing"
    for rp in (co / "ENGINE_STATE" / "review.md", co / "review.md", co / "REVIEW.md"):
        if rp.exists():
            txt = rp.read_text()
            verdict = "changes" if "REQUEST_CHANGES" in txt.upper() else ("approve" if "APPROVE" in txt.upper() else "unclear")
            break

    # 6. ship — merge only when: gate auto AND QA ok AND reviewer explicitly approved
    pr = gh.create_pr(repo, f"[engine/{rid}] {meta['feature']} (cycle {a.cycle})",
                      f"head={meta['repo'].split('/')[-1]}:{branch}", base,
                      f"Automatic run of engine {rid} on cycle {a.cycle}.\n\nplan: ENGINE_PLAN/{rid}/\nQA: {'passed' if qa_ok else 'failed'}\nreviewer verdict: {verdict}")
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
    meta["status"] = f"cycle{a.cycle}-merged" if merged else f"cycle{a.cycle}-pr-open"
    write_meta(cfg, rid, meta)
    print(f"cycle {a.cycle} complete: PR #{pr['number']} -> {pr['html_url']} (merged={merged})")


def cmd_report(a, cfg, dry, token):
    rid = a.run
    meta = read_meta(cfg, rid)
    rd = run_dir(cfg, rid)
    trail = (rd / "trail.md").read_text() if (rd / "trail.md").exists() else "(no trail)"
    plan = (rd / "plan.md").read_text() if (rd / "plan.md").exists() else "(no plan)"
    text = (
        f"# Morning report {rid} · cycle {meta.get('cycle')}\n\n- repo: {meta['repo']}\n- feature: {meta['feature']}\n"
        f"- status: {meta.get('status')}\n- good: {meta.get('good')}\n\n## Plan\n{plan}\n\n## Trail\n{trail}\n\n"
        f"## Next (ask the user)\n- Does the outcome match the requirement? keep → cycle {meta.get('cycle', 0) + 1}; done → close epic.\n"
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
        git(["clone", "--depth", "1", f"https://github.com/{repo}.git", str(tmp / "c")], dry=dry)
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

    h = sub.add_parser("handoff", parents=[common]); h.add_argument("--work", required=True); h.add_argument("--feature", required=True); h.add_argument("--run")
    c = sub.add_parser("clarify", parents=[common]); c.add_argument("--run", required=True); c.add_argument("--answer", default=""); c.add_argument("--good", action="store_true")
    r = sub.add_parser("run", parents=[common]); r.add_argument("--run", required=True); r.add_argument("--cycle", type=int, default=1)
    m = sub.add_parser("report", parents=[common]); m.add_argument("--run", required=True); m.add_argument("--cycle", type=int, default=1)
    q = sub.add_parser("probe", parents=[common])
    y = sub.add_parser("cycle", parents=[common]); y.add_argument("--work", required=True); y.add_argument("--feature", required=True); y.add_argument("--run")
    return p


def main():
    args = build_parser().parse_args()
    cfg = load_config()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if args.cmd in ("handoff", "clarify", "run", "report", "cycle") and not args.dry_run and not token:
        sys.exit("GITHUB_TOKEN not set in environment (required for network ops; set it, don't store it).")
    handlers = {"handoff": cmd_handoff, "clarify": cmd_clarify, "run": cmd_run, "report": cmd_report, "cycle": cmd_cycle, "probe": cmd_probe}
    handlers[args.cmd](args, cfg, args.dry_run, token)


if __name__ == "__main__":
    main()
