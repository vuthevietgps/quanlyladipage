# Hướng dẫn Deploy lên VPS

## Yêu cầu hệ thống VPS
- Ubuntu 20.04/22.04 LTS
- Python 3.8+
- Nginx
- Supervisor hoặc systemd

## Bước 1: Chuẩn bị VPS

### Cập nhật hệ thống
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git
```

### Tạo user cho ứng dụng
```bash
sudo adduser appuser
sudo usermod -aG sudo appuser
su - appuser
```

## Bước 2: Clone code từ Git

```bash
cd /home/appuser
git clone https://github.com/vuthevietgps/quanlyladipage.git
cd quanlyladipage
```

## Bước 3: Cài đặt Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Bước 4: Khởi tạo database và tạo admin user

```bash
python init_db.py
python create_admin.py
```

## Bước 5: Tạo thư mục cho published files

```bash
mkdir -p published
chmod 755 published
```

## Bước 6: Cấu hình Supervisor

Tạo file `/etc/supervisor/conf.d/quanlyladipage.conf`:

```ini
[program:quanlyladipage]
command=/home/appuser/quanlyladipage/.venv/bin/python main.py
directory=/home/appuser/quanlyladipage
user=appuser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/quanlyladipage.log
environment=FLASK_ENV=production
```

## Bước 7: Cấu hình Nginx

Tạo file `/etc/nginx/sites-available/quanlyladipage`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Thay bằng domain của bạn

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve published files directly through Nginx
    location /landing/ {
        alias /home/appuser/quanlyladipage/published/;
        try_files $uri $uri/ @flask;
    }

    location @flask {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 50M;
}
```

## Bước 8: Kích hoạt và khởi động services

```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/quanlyladipage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start quanlyladipage
sudo supervisorctl status
```

## Bước 9: Kiểm tra

```bash
# Xem log
sudo supervisorctl tail -f quanlyladipage

# Restart ứng dụng
sudo supervisorctl restart quanlyladipage
```

## Cập nhật code

```bash
cd /home/appuser/quanlyladipage
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart quanlyladipage
```

## Lưu ý bảo mật
- Đổi mật khẩu admin mặc định
- Cấu hình firewall (ufw)
- Cài đặt SSL certificate (Let's Encrypt)
- Backup database định kỳ