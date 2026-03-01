#!/usr/bin/env bash
set -euo pipefail

# Run as root on Ubuntu/Debian VPS.
APP_USER="${APP_USER:-ubuntu}"
APP_BASE_DIR="${APP_BASE_DIR:-/opt/meditation-bot}"
APP_DIR="${APP_DIR:-$APP_BASE_DIR/app}"
SHARED_DIR="${SHARED_DIR:-$APP_BASE_DIR/shared}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must be run as root."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip rsync curl ca-certificates

if ! id -u "$APP_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /bin/bash "$APP_USER"
fi

mkdir -p "$APP_DIR" "$SHARED_DIR" "$SHARED_DIR/data" "$SHARED_DIR/backups"
chown -R "$APP_USER":"$APP_USER" "$APP_BASE_DIR"

cat <<INFO
Bootstrap completed.
- app user: $APP_USER
- app dir:  $APP_DIR
- shared:   $SHARED_DIR

Next:
1) Upload project files to $APP_DIR
2) Put production env to $SHARED_DIR/.env
3) Run deploy/vps/update_app.sh as $APP_USER
4) Run deploy/vps/install_systemd_service.sh as root
INFO
