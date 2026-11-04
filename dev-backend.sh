#!/usr/bin/env bash
# Inicializa apenas a API local do ControlVision.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "O ambiente Python do backend ainda não existe em backend/.venv." >&2
  echo "Execute uma única vez:" >&2
  echo "  cd backend" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/python -m pip install -r requirements.txt" >&2
  echo "  cd .." >&2
  exit 1
fi

cd "$BACKEND_DIR"
exec "$PYTHON" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
