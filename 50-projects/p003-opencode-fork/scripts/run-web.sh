#!/usr/bin/env bash
# Start the modified opencode web on the testing folder. Usage: ./run-web.sh [port]
# If OPENCODE_SERVER_PASSWORD is set in the environment, the server requires the
# FE-001 login landing page; otherwise it stays open (plain 200).
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${1:-4447}"
BIN="opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode"
mkdir -p testing
cd testing
setsid nohup "../$BIN" web --port "$PORT" --hostname 0.0.0.0 > "web-$PORT.log" 2>&1 < /dev/null &
disown
sleep 5
echo "PID $!  log: testing/web-$PORT.log  url: http://0.0.0.0:$PORT/ (LAN: http://<this-host-ip>:$PORT/)"
if [ -n "${OPENCODE_SERVER_PASSWORD:-}" ]; then
  echo "  login page active: any URL redirects to /login until you sign in."
else
  echo "  no password configured -> open, no login page."
fi
