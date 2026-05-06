#!/usr/bin/env bash
# TokenTelemetry - configurable start script
set -euo pipefail
cd "$(dirname "$0")"

# Allow overriding ports from CLI: ./start.sh 3010 8010
FRONTEND_PORT=${1:-${FRONTEND_PORT:-3000}}
BACKEND_PORT=${2:-${BACKEND_PORT:-8000}}

export FRONTEND_PORT
export BACKEND_PORT

echo "Starting TokenTelemetry with FRONTEND_PORT=$FRONTEND_PORT and BACKEND_PORT=$BACKEND_PORT..."
exec node bin/cli.js
