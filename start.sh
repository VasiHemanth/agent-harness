#!/usr/bin/env bash
# Thin wrapper — all real logic lives in bin/cli.js.
set -euo pipefail
cd "$(dirname "$0")"
exec node bin/cli.js
