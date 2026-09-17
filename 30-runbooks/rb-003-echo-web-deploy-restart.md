# RB-003: Deploy & restart the opencode-fork web UI

**Risk level:** destructive (replace-a-running-service)
**Applies to:** dev-station
**Prerequisites:** fork repo clean/committed on `dev` (`50-projects/p003-opencode-fork/opencode`); bun 1.3.14 available (script pins it)

## When to use

Every time you change the fork and want the new binary serving on **:4447** (the web UI). Also the one place to learn the *correct* way to invoke deploy/restart.

## Procedure

1. Commit + push your fork changes on the `dev` branch first:
   ```bash
   git -C 50-projects/p003-opencode-fork/opencode add -A
   git -C 50-projects/p003-opencode-fork/opencode commit -m "…"
   git -C 50-projects/p003-opencode-fork/opencode push origin dev
   ```
2. Run the deploy script **from the fork root, NOT from inside `scripts/`**:
   ```bash
   cd 50-projects/p003-opencode-fork && bash scripts/deploy-web-4447.sh --detach
   ```
   - `--detach` re-execs itself in the background and writes progress to `testing/deploy-4447.log`. Use it when you're invoking from inside the :4447 opencode instance itself (so the script survives killing that listener).
   - **Why fork root?** The script resolves its `ROOT` from `$0`'s parent dir. Running `./deploy-web-4447.sh` from inside `scripts/` used to break because it `cd`'d to the fork root *before* `readlink` of a relative `$0` → wrong path (missing `scripts/`). The script is now path-generalized (resolves `SELF` before any `cd`) so it works from **any** cwd; the fork-root form remains the documented norm.
3. Tail the deploy log to watch build + start:
   ```bash
   tail -f 50-projects/p003-opencode-fork/testing/deploy-4447.log
   ```
   Build prints a Vite production bundle, then starts the binary.

## Verify success

```bash
ss -ltnp 2>/dev/null | grep ':4447'          # an `opencode` pid LISTENING on 0.0.0.0:4447
cat 50-projects/p003-opencode-fork/testing/.web-4447.pid
curl -sf http://127.0.0.1:4447/api/health    # {"healthy":true,...}
```
New pid != old pid; login page (FE-001) active on `/` (401 → `/login`).

## Rollback

Redeploy a previous good binary: rebuild from the last-good fork commit, or re-run step 2 to restart the same build. Kill a stuck instance:
```bash
kill -9 "$(cat 50-projects/p003-opencode-fork/testing/.web-4447.pid)"
```

## Log

Append every step's result to `20-logs/command-log.md`; update `10-status/current-state.md` (new build version + pid).
