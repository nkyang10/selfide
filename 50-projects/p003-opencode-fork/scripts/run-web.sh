#!/usr/bin/env bash
# Start local opencode web on the testing folder. Usage: ./run-web.sh [port]
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${1:-4447}"
BIN="opencode/packages/opencode/dist/opencode-linux-arm64/bin/opencode"
mkdir -p testing
cd testing
if [ -n "${OPENCODE_SERVER_PASSWORD:-}" ]; then
  echo "WARNING: OPENCODE_SERVER_PASSWORD is set in the environment; unsetting for local run." >&2
fi
env -u OPENCODE_SERVER_PASSWORD setsid nohup "../$BIN" web --port "$PORT" --hostname 0.0.0.0 > "web-$PORT.log" 2>&1 < /dev/null &
disown
sleep 4
echo "PID $!  log: testing/web-$PORT.log  url: http://0.0.0.0:$PORT/ (LAN: http://<this-host-ip>:$PORT/)"
