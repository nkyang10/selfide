#!/usr/bin/env bash
# Start/build the modified opencode single-file binary for the testing folder.
# Pins the same bun toolchain the opencode release build uses (root
# packageManager: bun@1.3.14). NEVER build with bun 1.4.x: its compiler embeds a
# broken effect/schema graph that crashes v2 endpoints (e.g. /api/reference)
# with `TypeError: undefined is not an object (evaluating ... .name)`
# (see 40-knowledge/decisions-log.md DEC-015).
set -euo pipefail
cd "$(dirname "$0")/.."

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
case "$OS" in
  linux) OS=linux ;;
  darwin) OS=darwin ;;
  *) echo "unsupported OS: $OS" >&2; exit 1 ;;
esac
ARCH=$(uname -m)
case "$ARCH" in
  x86_64|amd64) ARCH=x64 ;;
  aarch64|arm64) ARCH=aarch64 ;;
  *) echo "unsupported arch: $ARCH" >&2; exit 1 ;;
esac

BUN_VERSION=1.3.14
BUN_DIR="$HOME/.cache/opencode-build/bun-$BUN_VERSION"
BUN="$BUN_DIR/bun-$OS-$ARCH/bun"
if ! "$BUN" --version 2>/dev/null | grep -qx "$BUN_VERSION"; then
  mkdir -p "$BUN_DIR"
  echo "downloading bun $BUN_VERSION ($OS-$ARCH)"
  curl -fsSL "https://github.com/oven-sh/bun/releases/download/bun-v$BUN_VERSION/bun-$OS-$ARCH.zip" -o "$BUN_DIR/bun.zip"
  unzip -q -o "$BUN_DIR/bun.zip" -d "$BUN_DIR"
fi

export PATH="$BUN_DIR/bun-$OS-$ARCH:$PATH"
cd opencode
"$BUN" install
"$BUN" ./packages/opencode/script/build.ts --single
echo "built:"
ls -la packages/opencode/dist/*/bin/opencode
