#!/bin/bash

# Deploy script cho VPS Ubuntu
# Sử dụng: bash deploy.sh

set -e

echo "🚀 Bắt đầu deploy Quan Ly Landing Page..."

# Biến cấu hình
APP_NAME="quanlyladipage"
APP_DIR="/var/www/$APP_NAME"
PUBLISHED_DIR="/var/www/landingpages"
BACKUP_DIR="/var/backups"
PYTHON_VERSION="3.9"

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Kiểm tra quyền root
if [[ $EUID -ne 0 ]]; then
   print_error "Script này cần chạy với quyền root (sudo)"
   exit 1
fi

print_status "1. Cập nhật hệ thống..."
apt update && apt upgrade -y

print_status "2. Cài đặt các package cần thiết..."
apt install -y python3 python3-pip python3-venv nginx git sqlite3 htop curl

print_status "3. Tạo user www-data nếu chưa có..."
id -u www-data &>/dev/null || useradd -r -s /bin/false www-data

print_status "4. Tạo thư mục ứng dụng..."
mkdir -p $APP_DIR
mkdir -p $PUBLISHED_DIR
mkdir -p $BACKUP_DIR
mkdir -p /var/www/uploads

print_status "5. Sao chép source code..."
if [ -d ".git" ]; then
    print_status "Đang clone từ git repository..."
    git clone . $APP_DIR || cp -r . $APP_DIR
else
    print_status "Đang copy source code..."
    cp -r . $APP_DIR
fi

print_status "6. Tạo Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

print_status "7. Cài đặt Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

print_status "8. Tạo file cấu hình môi trường..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_warning "Hãy chỉnh sửa file .env với thông tin thực tế:"
    print_warning "- SECRET_KEY: Thay đổi secret key"
    print_warning "- ADMIN_DOMAIN: Domain admin của bạn"  
    print_warning "- WILDCARD_DOMAIN: Domain chính của bạn"
fi

print_status "9. Khởi tạo database..."
python -c "from app.db import init_db; from app import create_app; init_db(create_app())"

print_status "10. Cấp quyền thư mục..."
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data $PUBLISHED_DIR
chown -R www-data:www-data /var/www/uploads
chmod -R 755 $PUBLISHED_DIR
chmod -R 755 /var/www/uploads
chmod 664 $APP_DIR/database.db

print_status "11. Tạo systemd service..."
cat > /etc/systemd/system/$APP_NAME.service << EOF
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
systemctl enable $APP_NAME

print_status "12. Cấu hình Nginx..."
read -p "Nhập domain chính của bạn (vd: example.com): " DOMAIN

cat > /etc/nginx/sites-available/$APP_NAME << EOF
# Quản trị app (Flask admin)
server {
    listen 80;
    server_name admin.$DOMAIN;

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

# Wildcard subdomain cho landing pages  
server {
    listen 80;
    server_name *.$DOMAIN;
    root $PUBLISHED_DIR;
    index index.html;

    location / {
        set \$subdomain "";
        if (\$host ~* "^([^.]+)\.$DOMAIN\$") {
            set \$subdomain \$1;
        }
        
        try_files /\$subdomain/index.html /\$subdomain/index.html @fallback;
    }

    location ~* ^/([^/]+)/images/(.+\.(jpg|jpeg|png|gif|svg|webp|ico))\$ {
        alias $PUBLISHED_DIR/\$1/images/\$2;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
    }

    location @fallback {
        return 404 "Landing page không tồn tại";
    }

    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

# Kích hoạt site
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

print_status "13. Khởi động các service..."
systemctl start $APP_NAME
systemctl reload nginx

print_status "14. Thiết lập backup tự động..."
cat > /etc/cron.d/$APP_NAME-backup << EOF
# Backup database mỗi ngày lúc 2:00 AM
0 2 * * * root cp $APP_DIR/database.db $BACKUP_DIR/${APP_NAME}-\$(date +\\%Y\\%m\\%d).db

# Backup landing pages mỗi tuần lúc 3:00 AM chủ nhật
0 3 * * 0 root tar -czf $BACKUP_DIR/landingpages-\$(date +\\%Y\\%m\\%d).tar.gz $PUBLISHED_DIR/

# Xóa backup cũ hơn 30 ngày
0 4 * * * root find $BACKUP_DIR -name "${APP_NAME}-*.db" -mtime +30 -delete
0 4 * * * root find $BACKUP_DIR -name "landingpages-*.tar.gz" -mtime +30 -delete
EOF

print_status "15. Cấu hình firewall..."
ufw allow 22/tcp
ufw allow 80/tcp  
ufw allow 443/tcp
ufw --force enable

print_status "✅ Deploy hoàn thành!"
echo ""
echo "🔧 Các bước tiếp theo:"
echo "1. Chỉnh sửa file .env tại: $APP_DIR/.env"
echo "2. Cấu hình DNS wildcard trỏ về IP server này:"
echo "   - A record: @ -> $(curl -s ifconfig.me)"
echo "   - A record: * -> $(curl -s ifconfig.me)"
echo "   - A record: admin -> $(curl -s ifconfig.me)"
echo "3. Truy cập admin panel: http://admin.$DOMAIN"
echo "4. Cài SSL certificate: sudo certbot --nginx"
echo ""
echo "📊 Kiểm tra status:"
echo "- Flask app: sudo systemctl status $APP_NAME"
echo "- Nginx: sudo systemctl status nginx"
echo "- Logs: sudo journalctl -u $APP_NAME -f"
echo ""
echo "🎉 Chúc mừng! Hệ thống đã sẵn sàng!"