#!/usr/bin/env bash
# Agent Observability Harness — one-line installer.
#   curl -fsSL https://raw.githubusercontent.com/hemanthvasi/coding-agent-harness-evaluation/main/install.sh | bash
set -euo pipefail

REPO_URL="https://github.com/hemanthvasi/coding-agent-harness-evaluation.git"
TARGET_DIR="${AGENT_HARNESS_DIR:-agent-harness}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required but not installed."; exit 1; }; }

need git
need node
need npm
command -v python3 >/dev/null 2>&1 || need python

# Clone if we're not already inside the repo
if [ ! -f "./bin/cli.js" ]; then
  if [ -d "$TARGET_DIR" ]; then
    echo "→ using existing clone at $TARGET_DIR"
  else
    echo "→ cloning $REPO_URL → $TARGET_DIR"
    git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
  fi
  cd "$TARGET_DIR"
fi

exec node bin/cli.js
