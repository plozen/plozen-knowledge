#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/mnt/data/workspace/plozen-knowledge"
VENV_BIN="$PROJECT_DIR/.venv/bin"

cd "$PROJECT_DIR"

if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo "Missing $PROJECT_DIR/.env" >&2
  exit 1
fi

if [ ! -x "$VENV_BIN/plozen-knowledge-mcp" ]; then
  echo "Missing MCP executable. Run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
. "$PROJECT_DIR/.env"
set +a

export KNOWLEDGE_API_BASE_URL="${KNOWLEDGE_API_BASE_URL:-http://127.0.0.1:${API_PORT:-3200}}"

exec "$VENV_BIN/plozen-knowledge-mcp"
