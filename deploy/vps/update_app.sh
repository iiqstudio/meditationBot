#!/usr/bin/env bash
set -euo pipefail

# Run as app user after code upload.
APP_BASE_DIR="${APP_BASE_DIR:-/opt/meditation-bot}"
APP_DIR="${APP_DIR:-$APP_BASE_DIR/app}"
SHARED_DIR="${SHARED_DIR:-$APP_BASE_DIR/shared}"

cd "$APP_DIR"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f "$SHARED_DIR/.env" ]]; then
  echo "Missing $SHARED_DIR/.env"
  echo "Create it first (you can copy .env.example)."
  exit 1
fi

ln -snf "$SHARED_DIR/.env" "$APP_DIR/.env"
mkdir -p "$SHARED_DIR/data"

python scripts/init_db.py

echo "App updated successfully in $APP_DIR"
