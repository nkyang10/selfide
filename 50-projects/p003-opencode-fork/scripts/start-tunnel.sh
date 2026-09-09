#!/usr/bin/env bash
# Start a cloudflared quick tunnel to the local opencode web UI on :4447.
# Usage: ./start-tunnel.sh
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
TARGET="${1:-http://localhost:4447}"
LOG=/tmp/opencode/cloudflared.log
mkdir -p /tmp/opencode
: > "$LOG"
setsid nohup cloudflared tunnel --url "$TARGET" --no-autoupdate > "$LOG" 2>&1 < /dev/null &
disown
sleep 6
echo "cloudflared launched (pid $!). log: $LOG"
