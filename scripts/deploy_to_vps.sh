#!/usr/bin/env bash
set -euo pipefail

# Run locally: sync code to VPS and restart service.
# Example:
# ./scripts/deploy_to_vps.sh ubuntu@1.2.3.4 /opt/meditation-bot/app
# ./scripts/deploy_to_vps.sh ubuntu@1.2.3.4 /opt/meditation-bot/app --sync-only

REMOTE_HOST="${1:-}"
REMOTE_APP_DIR="${2:-/opt/meditation-bot/app}"
MODE="${3:-deploy}"

if [[ -z "$REMOTE_HOST" ]]; then
  echo "Usage: $0 <user@host> [remote_app_dir] [--sync-only]"
  exit 1
fi

if [[ "$MODE" != "deploy" && "$MODE" != "--sync-only" ]]; then
  echo "Unknown mode: $MODE"
  echo "Allowed: deploy (default), --sync-only"
  exit 1
fi

rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.venv311' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'data/' \
  ./ "$REMOTE_HOST:$REMOTE_APP_DIR/"

if [[ "$MODE" == "--sync-only" ]]; then
  echo "Sync-only mode complete."
  exit 0
fi

ssh "$REMOTE_HOST" "cd '$REMOTE_APP_DIR' && bash deploy/vps/update_app.sh && if systemctl list-unit-files | grep -q '^meditation-bot.service'; then sudo systemctl restart meditation-bot && sudo systemctl status meditation-bot --no-pager; else echo 'Service meditation-bot is not installed yet. Run deploy/vps/install_systemd_service.sh on server.'; fi"

echo "Deploy completed."
