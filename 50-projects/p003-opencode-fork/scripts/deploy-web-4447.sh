#!/usr/bin/env bash
# One-shot: rebuild the modified opencode fork and (re)deploy the web server on :4447.
# Usage: ./deploy-web-4447.sh
#   - kills whatever currently listens on :4447 (the old deployed instance),
#   - compiles the fork (build-linux.sh, pins bun 1.3.14),
#   - starts the fresh binary on 0.0.0.0:4447 from testing/ (run-web.sh).
# Safe to re-run: it tears down the old instance first. Write-to-self of already-serving
# PIDs is handled via a pidfile under testing/.
set -euo pipefail
PORT="${PORT:-4447}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SELF="$(readlink -f "$0" 2>/dev/null || echo "$0")"
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
STOPPED=0
if [ -f "$PIDFILE" ]; then
  OLD_PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "   killing old server pid=$OLD_PID (from pidfile)"
    kill "$OLD_PID" 2>/dev/null || true
    sleep 2
    if kill -0 "$OLD_PID" 2>/dev/null; then echo "   still alive, force-killing"; kill -9 "$OLD_PID" 2>/dev/null || true; fi
    STOPPED=1
  fi
  rm -f "$PIDFILE"
fi

# Fallback: find port listener via ss if the pidfile was missing/stale.
LISTENER_PID="$(ss -ltnp 2>/dev/null | awk -v p=":$PORT$" '$4 ~ p {x=$6; sub(/.*pid=/,"",x); sub(/,.*/,"",x); print x}' | tr -d '\n')"
if [ -n "$LISTENER_PID" ] && kill -0 "$LISTENER_PID" 2>/dev/null; then
  echo "   killing port-$PORT listener pid=$LISTENER_PID"
  kill "$LISTENER_PID" 2>/dev/null || true
  sleep 2
  if kill -0 "$LISTENER_PID" 2>/dev/null; then echo "   still alive, force-killing"; kill -9 "$LISTENER_PID" 2>/dev/null || true; fi
  STOPPED=1
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
