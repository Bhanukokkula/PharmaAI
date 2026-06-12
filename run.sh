#!/usr/bin/env bash
#
# One-command local run: sets up the backend venv, seeds the DB and trains
# the recommender on first run, then starts the API and frontend dev server
# together. Ctrl+C stops both.
#
# Usage: ./run.sh
# Override ports with BACKEND_PORT / FRONTEND_PORT env vars if needed.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo "==> Backend setup ($BACKEND_DIR)"
cd "$BACKEND_DIR"

if [ ! -d .venv ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f pharmaai.db ]; then
  echo "Seeding database (first run — this ingests openFDA data and"
  echo "generates synthetic users/interactions, may take a minute)..."
  python -m ml.seed
fi

if [ ! -f ml/artifacts/meta.json ]; then
  echo "Training recommender (first run)..."
  python -m ml.train
fi

echo "==> Starting backend on :$BACKEND_PORT"
uvicorn app.main:app --port "$BACKEND_PORT" &
BACKEND_PID=$!

cleanup() {
  echo
  echo "Shutting down..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Frontend setup ($FRONTEND_DIR)"
cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo
echo "PharmaAI is running:"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  API:      http://127.0.0.1:$BACKEND_PORT  (interactive docs at /docs)"
echo
echo "Press Ctrl+C to stop both."
echo

VITE_API_BASE="http://127.0.0.1:$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" --strictPort
