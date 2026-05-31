#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_FORMULA="${PYTHON_FORMULA:-python@3.13}"
PYTHON_BIN="${PYTHON_BIN:-}"
WITH_SERVICES=0
START_APP=0
PORT="${ODYSSEUS_PORT:-7001}"

usage() {
  cat <<'EOF'
Usage: scripts/setup-macos.sh [--with-services] [--start]

Sets up Odysseus on macOS without installing Python packages globally:
  - installs/updates Homebrew python@3.13 and tmux
  - creates .venv in this repo
  - installs Python requirements into .venv
  - runs npm ci from package-lock.json
  - runs setup.py to create local data/log folders and auth

Options:
  --with-services  Start ChromaDB, SearXNG, and ntfy with docker compose.
  --start          Start the app on http://127.0.0.1:${ODYSSEUS_PORT:-7001} after setup.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --with-services) WITH_SERVICES=1 ;;
    --start) START_APP=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
  shift
done

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This installer is for macOS. Use the README manual or Docker path on other OSes."
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh/ and rerun this script."
  exit 1
fi

echo "==> Installing Homebrew runtime dependencies"
brew list "$PYTHON_FORMULA" >/dev/null 2>&1 || brew install "$PYTHON_FORMULA"
brew list tmux >/dev/null 2>&1 || brew install tmux

if [ -z "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(brew --prefix "$PYTHON_FORMULA")/bin/python3.13"
fi

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python binary not found at $PYTHON_BIN"
  exit 1
fi

cd "$ROOT_DIR"

echo "==> Creating isolated Python environment"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  echo "==> Installing Node dependencies from package-lock.json"
  npm ci
else
  echo "==> npm not found; skipping Node test dependencies"
fi

echo "==> Running first-time Odysseus setup"
ODYSSEUS_SKIP_ADMIN_CREATE=1 .venv/bin/python setup.py

if [ "$WITH_SERVICES" -eq 1 ]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found; install Docker Desktop to use --with-services."
    exit 1
  fi
  echo "==> Starting bundled services"
  docker compose up -d chromadb searxng ntfy
fi

if [ "$START_APP" -eq 1 ]; then
  SETUP_TOKEN=""
  if ! .venv/bin/python - <<'PY'
import json
from pathlib import Path
try:
    data = json.loads(Path("data/auth.json").read_text())
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if data.get("users") else 1)
PY
  then
    SETUP_TOKEN="$(".venv/bin/python" - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)"
    echo "==> First-run setup URL: http://127.0.0.1:${PORT}/login?setup_token=${SETUP_TOKEN}"
  fi
  echo "==> Starting Odysseus on http://127.0.0.1:${PORT}"
  export ODYSSEUS_PORT="$PORT"
  export ODYSSEUS_INTERNAL_BASE_URL="http://127.0.0.1:${PORT}"
  if [ -n "$SETUP_TOKEN" ]; then
    export ODYSSEUS_SETUP_TOKEN="$SETUP_TOKEN"
  fi
  exec .venv/bin/uvicorn app:app --host 127.0.0.1 --port "$PORT"
fi

echo "==> Done"
echo "Start Odysseus with:"
echo "  source .venv/bin/activate"
echo "  ODYSSEUS_PORT=${PORT} uvicorn app:app --host 127.0.0.1 --port ${PORT}"
echo "The server will print a first-run setup URL if no admin exists yet."
