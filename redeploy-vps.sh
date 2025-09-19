#!/bin/bash

# One-shot cleanup + redeploy script for Ubuntu VPS with Nginx
# - Safely stop/remove old app service and code
# - Install/update required packages
# - Clone from GitHub and set up Python venv
# - Initialize DB, set permissions
# - Configure systemd service and Nginx (admin + wildcard)
# - Start services
#
# Usage:
#   sudo bash redeploy-vps.sh
#
# Non-interactive (env overrides):
#   DOMAIN=mydomain.com BRANCH=main REPO_URL=https://github.com/vuthevietgps/quanlyladipage.git PRESERVE_LANDINGPAGES=true sudo -E bash redeploy-vps.sh

set -Eeuo pipefail

# ---------- Pretty printing ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
header()  { echo -e "${BLUE}\n==== $* ====${NC}"; }

# ---------- Config (overridable via env) ----------
APP_NAME="${APP_NAME:-quanlyladipage}"
REPO_URL="${REPO_URL:-https://github.com/vuthevietgps/quanlyladipage.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="${APP_DIR:-/var/www/$APP_NAME}"
PUBLISHED_DIR="${PUBLISHED_DIR:-/var/www/landingpages}"
UPLOADS_DIR="${UPLOADS_DIR:-/var/www/uploads}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups}"
SERVICE_NAME="${SERVICE_NAME:-$APP_NAME}"
PY_BIN="${PY_BIN:-python3}"
PRESERVE_LANDINGPAGES="${PRESERVE_LANDINGPAGES:-ask}"

# ---------- Root check ----------
if [[ $EUID -ne 0 ]]; then
  error "Please run as root: sudo bash $0"
  exit 1
fi

# ---------- Domain input ----------
DOMAIN="${DOMAIN:-}"
if [[ -z "$DOMAIN" ]]; then
  read -rp "Enter your main domain (e.g. example.com): " DOMAIN
fi
if [[ -z "$DOMAIN" ]]; then
  error "DOMAIN is required. Abort."
  exit 1
fi
ADMIN_DOMAIN="${ADMIN_DOMAIN:-admin.$DOMAIN}"

# ---------- Preserve landing pages? ----------
case "$PRESERVE_LANDINGPAGES" in
  true|false) ;;
  ask)
    read -rp "Preserve existing landing pages dir '$PUBLISHED_DIR'? (Y/n): " yn
    yn=${yn:-Y}
    if [[ "$yn" =~ ^[Yy]$ ]]; then PRESERVE_LANDINGPAGES=true; else PRESERVE_LANDINGPAGES=false; fi
    ;;
  *) warn "PRESERVE_LANDINGPAGES must be true|false|ask. Defaulting to true."; PRESERVE_LANDINGPAGES=true;;
esac

header "1) Update system and install packages"
export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
apt install -y nginx git sqlite3 "$PY_BIN" python3-venv python3-pip ufw curl

header "2) Stop and remove old services (if any)"
if systemctl list-unit-files | grep -q "^$SERVICE_NAME.service"; then
  info "Stopping service $SERVICE_NAME"
  systemctl stop "$SERVICE_NAME" || true
  systemctl disable "$SERVICE_NAME" || true
  rm -f "/etc/systemd/system/$SERVICE_NAME.service"
fi
systemctl daemon-reload

header "3) Backup and clean old code"
timestamp=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

if [[ -d "$APP_DIR" ]]; then
  info "Backing up old app to $BACKUP_DIR/${APP_NAME}-code-$timestamp.tar.gz"
  tar -czf "$BACKUP_DIR/${APP_NAME}-code-$timestamp.tar.gz" -C "$(dirname "$APP_DIR")" "$(basename "$APP_DIR")" || true
  
  # Backup DB before removing app dir
  if [[ -f "$APP_DIR/database.db" ]]; then
    info "Backing up DB to $BACKUP_DIR/${APP_NAME}-$timestamp.db"
    cp -f "$APP_DIR/database.db" "$BACKUP_DIR/${APP_NAME}-$timestamp.db" || true
  fi
  
  info "Removing old app dir $APP_DIR"
  rm -rf "$APP_DIR"
fi

if [[ -d "$PUBLISHED_DIR" ]]; then
  if [[ "$PRESERVE_LANDINGPAGES" == "true" ]]; then
    info "Preserving existing landing pages at $PUBLISHED_DIR"
  else
    info "Backing up and cleaning landing pages at $PUBLISHED_DIR"
    tar -czf "$BACKUP_DIR/landingpages-$timestamp.tar.gz" -C "$(dirname "$PUBLISHED_DIR")" "$(basename "$PUBLISHED_DIR")" || true
    rm -rf "$PUBLISHED_DIR"
  fi
fi

header "4) Prepare directories"
mkdir -p "$APP_DIR" "$PUBLISHED_DIR" "$UPLOADS_DIR"
chown -R www-data:www-data "$PUBLISHED_DIR" "$UPLOADS_DIR"
chmod -R 755 "$PUBLISHED_DIR" "$UPLOADS_DIR"

header "5) Clone repository $REPO_URL (branch: $BRANCH)"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$APP_DIR.tmp"
mv "$APP_DIR.tmp" "$APP_DIR"

header "6) Create Python virtual environment and install deps"
cd "$APP_DIR"
"$PY_BIN" -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
if [[ -f requirements.txt ]]; then
  pip install -r requirements.txt
else
  warn "requirements.txt not found. Installing common deps just in case."
  pip install Flask Flask-Login Flask-WTF python-dotenv WTForms
fi

header "7) Create .env if missing"
if [[ ! -f .env ]]; then
  cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 16)
ADMIN_DOMAIN=$ADMIN_DOMAIN
WILDCARD_DOMAIN=$DOMAIN
EOF
  info "Generated .env with defaults. Please review at $APP_DIR/.env"
fi

header "8) Initialize database"
set +e
python - << 'PY'
import sys
try:
    from app.db import init_db
    from app import create_app
    app = create_app()
    init_db(app)
    print('DB initialization: OK')
except Exception as e:
    print('DB initialization failed:', e)
    sys.exit(1)
PY
rc=$?
set -e
if [[ $rc -ne 0 ]]; then
  error "Database initialization failed. Check your app and .env"
  exit 1
fi

header "9) Permissions"
chown -R www-data:www-data "$APP_DIR"
chmod 664 "$APP_DIR/database.db" || true

header "10) Systemd service"
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Quan Ly Landing Page Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="FLASK_APP=main.py"
Environment="FLASK_ENV=production"
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

header "11) Nginx configuration"
cat > "/etc/nginx/sites-available/$APP_NAME" << EOF
# Admin panel (proxied to Flask)
server {
    listen 80;
    server_name $ADMIN_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# Wildcard subdomains for landing pages
server {
    listen 80;
    server_name *.$DOMAIN;
    root $PUBLISHED_DIR;
    index index.html;

    location / {
        set \$subdomain "";
        if (\$host ~* "^([^.]+)\\.$DOMAIN\$") { set \$subdomain \$1; }
        try_files /\$subdomain/index.html /\$subdomain/index.html @fallback;
    }

    location ~* ^/([^/]+)/images/(.+\.(jpg|jpeg|png|gif|svg|webp|ico))$ {
        alias $PUBLISHED_DIR/\$1/images/\$2;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
    }

    location @fallback { return 404 "Landing page không tồn tại"; }

    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/$APP_NAME"
rm -f /etc/nginx/sites-enabled/default || true

nginx -t

header "12) Firewall (UFW)"
ufw allow 22/tcp || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable || true

header "13) Start services"
systemctl restart "$SERVICE_NAME"
systemctl reload nginx

sleep 1
systemctl --no-pager -l status "$SERVICE_NAME" || true

header "✅ Done"
ip=$(curl -s ifconfig.me || echo "<YOUR_IP>")
echo "\nNext steps:"
echo "- Admin:    http://$ADMIN_DOMAIN" 
echo "- Wildcard: http://anything.$DOMAIN"
echo "- DNS: Ensure A records @, *, admin -> $ip"
echo "- SSL (optional): sudo apt install -y certbot python3-certbot-nginx; sudo certbot --nginx -d $ADMIN_DOMAIN -d '*.$DOMAIN'"
