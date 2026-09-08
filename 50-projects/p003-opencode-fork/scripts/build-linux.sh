#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../opencode"
export PATH="$HOME/.bun/bin:$PATH"
bun install
bun ./packages/opencode/script/build.ts --single
echo "built:"
ls -la packages/opencode/dist/*/bin/opencode
