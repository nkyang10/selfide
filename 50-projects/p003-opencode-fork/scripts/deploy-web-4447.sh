#!/usr/bin/env bash
# One-shot: rebuild the modified opencode fork and (re)deploy the web server on :4447.
# Usage: ./deploy-web-4447.sh
#   - kills whatever currently listens on :4447 (the old deployed instance),
#   - compiles the fork (build-linux.sh, pins bun 1.3.14),
#   - starts the fresh binary on 0.0.0.0:4447 from testing/ (run-web.sh).
# Safe to re-run: it tears down the old instance first. Write-to-self of already-serving
# PIDs is handled via a pidfile under testing/.
set -euo pipefail

# Resolve our own absolute path FIRST, while cwd is still whatever the caller
# used. Doing readlink after `cd` resolves relative $0 against the new cwd and
# silently produces a wrong path (e.g. ./deploy-web-4447.sh -> fork-root/...).
# This works whether the script is invoked as ./deploy-web-4447.sh (from either
# this scripts/ dir or the fork root) or by an absolute/relative path.
this="$0"
case "$this" in
  /*) SCRIPT_DIR="$(dirname "$this")" ;;
  *)  SCRIPT_DIR="$(cd "$(dirname "$this")" >/dev/null 2>&1 && pwd)" ;;
esac
SELF="$SCRIPT_DIR/$(basename "$this")"
SELF="$(readlink -f "$SELF" 2>/dev/null || echo "$SELF")"

PORT="${PORT:-4447}"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT"
BIN_REL="$(ls opencode/packages/opencode/dist/opencode-linux-*/bin/opencode 2>/dev/null | head -1 || true)"
PIDFILE="$ROOT/testing/.web-$PORT.pid"
DEPLOY_LOG="$ROOT/testing/deploy-$PORT.log"

# --detach: re-exec ourselves fully backgrounded (setsid+nohup) writing to
# $DEPLOY_LOG, then exit. Use this when triggered from inside the :PORT
# opencode instance itself: step 1 below kills that listener, so the script
# must survive the death of its invoker or it dies mid-run (SIGPIPE via pipefail).
if [ "${1:-}" = "--detach" ]; then
  echo "==> deploying in background -> $DEPLOY_LOG"
  setsid nohup bash "$SELF" >"$DEPLOY_LOG" 2>&1 </dev/null &
  disown || true
  exit 0
fi

echo "==> deploy-web :$PORT ($(date -u +%Y-%m-%dT%H:%M:%SZ))"

# --- 1. Stop whatever currently serves :4447 ---------------------------------
# s100: this used to be `kill` + `sleep 2` + `kill -9`, which is a hard kill: whatever the agent was
# doing simply stopped, and the transcript kept a half-written assistant message. Now the server is
# told a drain window is coming (POST /global/lifecycle), so connected browsers can count down, refuse
# new prompts and hold what the reader was trying to send. The server exits when the window elapses
# (see the SIGTERM handler in cli/cmd/web.ts). SIGKILL is only a backstop for a server that ignores it.
STOPPED=0
DRAIN_WINDOW="${DRAIN_WINDOW:-60}"
DRAIN_BACKSTOP="${DRAIN_BACKSTOP:-30}"

# Arm the window first. The server may require auth (FE-001 login gate); a 401 still means it is
# alive and it will arm nothing, so this is best-effort and never fails the deploy.
arm_window() {
  local pid="$1"
  if [ -z "$pid" ]; then return 0; fi
  local port="${2:-$PORT}"
  curl -sf -m 5 -X POST "http://127.0.0.1:$port/global/lifecycle" \
    -H "content-type: application/json" \
    -d "{\"timeoutMs\":$(( DRAIN_WINDOW * 1000 )),\"reason\":\"deploy\"}" >/dev/null 2>&1 \
    && echo "   drain window armed: ${DRAIN_WINDOW}s (pid=$pid)" \
    || echo "   drain window NOT armed (server needs auth, or already gone) — continuing"
}

# SIGTERM, then wait out the window, then SIGKILL as a backstop.
stop_pid() {
  local pid="$1" why="$2"
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then return 1; fi
  arm_window "$pid"
  echo "   SIGTERM to old server pid=$pid ($why)"
  kill "$pid" 2>/dev/null || true
  local waited=0
  while [ "$waited" -lt "$(( DRAIN_WINDOW + DRAIN_BACKSTOP ))" ]; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "   old server exited on its own after ${waited}s"
      return 0
    fi
    sleep 1
    waited=$(( waited + 1 ))
  done
  echo "   still alive after ${waited}s — force-killing (it ignored the drain)"
  kill -9 "$pid" 2>/dev/null || true
  return 0
}

if [ -f "$PIDFILE" ]; then
  OLD_PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    stop_pid "$OLD_PID" "from pidfile" && STOPPED=1
  fi
  rm -f "$PIDFILE"
fi

# Fallback: find port listener via ss if the pidfile was missing/stale.
LISTENER_PID="$(ss -ltnp 2>/dev/null | awk -v p=":$PORT$" '$4 ~ p {x=$6; sub(/.*pid=/,"",x); sub(/,.*/,"",x); print x}' | tr -d '\n')"
if [ -n "$LISTENER_PID" ] && kill -0 "$LISTENER_PID" 2>/dev/null; then
  stop_pid "$LISTENER_PID" "port-$PORT listener" && STOPPED=1
fi

if [ "$STOPPED" -eq 1 ]; then echo "   old instance stopped"; else echo "   nothing was serving :$PORT"; fi

# --- 2. Rebuild the fork -------------------------------------------
echo "==> building fork (build-linux.sh)..."
"$ROOT/scripts/build-linux.sh"
if [ ! -x "$ROOT/$BIN_REL" ]; then echo "ERROR: build did not produce a binary (expected under opencode/packages/opencode/dist/opencode-linux-*/bin/opencode)" >&2; exit 1; fi
echo "   built: $BIN_REL"

# --- 3. (Re)start on :4447 ------------------------------------------
echo "==> starting on :$PORT..."
"$ROOT/scripts/run-web.sh" "$PORT"

# Capture the new PID and write the pidfile for the next deploy cycle.
sleep 2
NEW_PID="$(ss -ltnp 2>/dev/null | awk -v p=":$PORT$" '$4 ~ p {x=$6; sub(/.*pid=/,"",x); sub(/,.*/,"",x); print x}' | tr -d '\n')"
if [ -n "$NEW_PID" ]; then
  echo "$NEW_PID" > "$PIDFILE"
  echo "   new server pid=$NEW_PID  (pidfile: $PIDFILE)"
else
  echo "WARNING: could not detect a listener on :$PORT yet; check testing/web-$PORT.log" >&2
  tail -20 "testing/web-$PORT.log" 2>/dev/null || true
fi

echo "==> deploy complete: http://0.0.0.0:$PORT/"
