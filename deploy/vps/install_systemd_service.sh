#!/usr/bin/env bash
set -euo pipefail

# Run as root after code upload.
APP_USER="${APP_USER:-ubuntu}"
APP_BASE_DIR="${APP_BASE_DIR:-/opt/meditation-bot}"
APP_DIR="${APP_DIR:-$APP_BASE_DIR/app}"
SHARED_DIR="${SHARED_DIR:-$APP_BASE_DIR/shared}"
ENV_FILE="${ENV_FILE:-$SHARED_DIR/.env}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must be run as root."
  exit 1
fi

SRC_TEMPLATE="$APP_DIR/deploy/systemd/meditation-bot.service"
DST_SERVICE="/etc/systemd/system/meditation-bot.service"

if [[ ! -f "$SRC_TEMPLATE" ]]; then
  echo "Template not found: $SRC_TEMPLATE"
  exit 1
fi

sed \
  -e "s|__APP_USER__|$APP_USER|g" \
  -e "s|__APP_DIR__|$APP_DIR|g" \
  -e "s|__ENV_FILE__|$ENV_FILE|g" \
  -e "s|__SHARED_DIR__|$SHARED_DIR|g" \
  "$SRC_TEMPLATE" > "$DST_SERVICE"

systemctl daemon-reload
systemctl enable meditation-bot
systemctl restart meditation-bot
systemctl status meditation-bot --no-pager
