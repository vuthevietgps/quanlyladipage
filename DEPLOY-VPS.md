# 🚀 HƯỚNG DẪN DEPLOY LÊN VPS UBUNTU

## 📋 Chuẩn Bị

### VPS Requirements:
- **OS**: Ubuntu 20.04+ hoặc 22.04 LTS
- **RAM**: Tối thiểu 1GB (khuyến nghị 2GB+)
- **Storage**: 20GB+ free space
- **Network**: Public IP với port 80, 443 mở

### Domain Setup:
1. **Mua domain** (ví dụ: `mydomain.com`)
2. **Cấu hình DNS** tại nhà cung cấp domain:
   ```
   Type    Name     Value           TTL
   A       @        YOUR_VPS_IP     300
   A       *        YOUR_VPS_IP     300
   A       admin    YOUR_VPS_IP     300
   ```

## 🛠️ Deploy Bước 1: Tải Code và Deploy Tự Động

### SSH vào VPS:
```bash
ssh root@YOUR_VPS_IP
```

### Download và deploy:
```bash
# Tải code từ GitHub
git clone https://github.com/vuthevietgps/quanlyladipage.git
cd quanlyladipage

# Chạy script deploy tự động
sudo bash deploy.sh
```

### Khi script chạy:
1. Nhập domain chính của bạn (ví dụ: `mydomain.com`)
2. Chờ script cài đặt (5-10 phút)
3. Script sẽ tự động:
   - Cài Python, Nginx, SQLite
   - Tạo virtual environment
   - Cài dependencies
   - Tạo systemd service
   - Cấu hình Nginx wildcard
   - Setup backup tự động

## 🔧 Bước 2: Cấu Hình Environment

### Chỉnh sửa file .env:
```bash
cd /var/www/quanlyladipage
sudo nano .env

# Thay đổi các thông số sau:
SECRET_KEY=your-super-secret-production-key-change-this
ADMIN_DOMAIN=admin.mydomain.com
WILDCARD_DOMAIN=mydomain.com
```

### Restart services:
```bash
sudo systemctl restart quanlyladipage
sudo systemctl reload nginx
```

## 🔒 Bước 3: Cài SSL Certificate (Khuyến Nghị)

```bash
# Cài Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Tạo certificate cho wildcard domain
sudo certbot --nginx -d admin.mydomain.com -d "*.mydomain.com"

# Chọn: Redirect HTTP to HTTPS (option 2)
```

## ✅ Bước 4: Kiểm Tra Hoạt Động

### 1. Kiểm tra services:
```bash
sudo systemctl status quanlyladipage    # Flask app
sudo systemctl status nginx             # Web server
```

### 2. Truy cập admin panel:
- **URL**: `https://admin.mydomain.com`
- Nếu thấy giao diện quản lý → **Thành công!** ✅

### 3. Test tạo landing page:
1. Vào admin panel
2. Click "Thêm Landing Page"
3. Điền thông tin:
   ```
   Subdomain: test123
   Agent: [chọn hoặc tạo agent]
   File HTML: Upload file HTML
   ```
4. Save và truy cập: `https://test123.mydomain.com`
5. Nếu hiển thị landing page → **Hoàn thành!** 🎉

## 🖼️ Bước 5: Upload Images cho Landing Pages

### Sử dụng script có sẵn:
```bash
# Upload ảnh từ local lên server
scp *.jpg *.png user@YOUR_VPS_IP:/tmp/

# SSH vào server và di chuyển ảnh
ssh user@YOUR_VPS_IP
sudo bash /var/www/quanlyladipage/images.sh upload test123 /tmp/
```

### Hoặc upload qua FTP/SFTP:
```bash
# Upload vào thư mục tương ứng
/var/www/landingpages/subdomain/images/
```

## 🔍 Troubleshooting

### Landing page không load:
```bash
# Kiểm tra DNS
nslookup test123.mydomain.com

# Kiểm tra Nginx config
sudo nginx -t
sudo systemctl status nginx

# Kiểm tra file tồn tại
ls -la /var/www/landingpages/test123/
```

### Flask app không chạy:
```bash
# Xem logs
sudo journalctl -u quanlyladipage -f

# Restart service
sudo systemctl restart quanlyladipage

# Test thủ công
cd /var/www/quanlyladipage
source venv/bin/activate
python main.py
```

### Images không hiển thị:
```bash
# Kiểm tra quyền thư mục
ls -la /var/www/landingpages/subdomain/images/

# Fix quyền nếu cần
sudo chown -R www-data:www-data /var/www/landingpages/
sudo chmod -R 755 /var/www/landingpages/
```

## 📊 Monitoring

### Kiểm tra logs:
```bash
# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Flask app logs  
sudo journalctl -u quanlyladipage -f

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Health check:
```bash
curl -I https://admin.mydomain.com          # Admin panel
curl -I https://test123.mydomain.com        # Landing page
```

## 🆘 Support

Nếu gặp vấn đề:

1. **Kiểm tra logs** theo hướng dẫn trên
2. **Tạo issue** tại: https://github.com/vuthevietgps/quanlyladipage/issues
3. **Cung cấp thông tin**:
   - OS version: `lsb_release -a`
   - Error logs
   - Steps đã làm

## 🎉 Hoàn Thành!

Bạn đã có hệ thống quản lý landing page hoàn chỉnh:

- ✅ **Admin Panel**: `https://admin.mydomain.com`
- ✅ **Wildcard Subdomain**: `https://anything.mydomain.com`
- ✅ **Tracking Integration**: Google Analytics, Phone, Zalo
- ✅ **Image Management**: Upload và optimize tự động
- ✅ **Auto Backup**: Database và files
- ✅ **SSL Certificate**: HTTPS secure

**Chúc mừng bạn đã deploy thành công!** 🚀

## 🔄 (Mới) Làm sạch sâu và triển khai lại từ GitHub

Nếu VPS của bạn đã có ứng dụng cũ, hãy dùng các bước sau để dọn dẹp sâu và triển khai lại từ repo GitHub mới `quanlyladipage1`:

### 1) Làm sạch sâu VPS

Chạy script dọn sâu (sẽ hỏi có giữ dữ liệu landingpages/uploads hay không, và có backup rồi xoá SSL hay không):

```bash
wget -O /root/cleanup-vps.sh https://raw.githubusercontent.com/vuthevietgps/quanlyladipage/main/cleanup-vps.sh
sudo bash /root/cleanup-vps.sh
```

### 2) Triển khai lại từ GitHub mới

Script triển khai 1 bước: cài gói cần thiết, clone repo `quanlyladipage1`, tạo venv, cài requirements, khởi tạo DB, tạo service systemd, cấu hình Nginx admin + wildcard, mở firewall và khởi động.

Chạy tương tác (sẽ hỏi DOMAIN và có giữ landingpages hay không):

```bash
wget -O /root/redeploy-vps.sh https://raw.githubusercontent.com/vuthevietgps/quanlyladipage/main/redeploy-vps.sh
sudo bash /root/redeploy-vps.sh
```

Hoặc chạy không cần hỏi (ví dụ):

```bash
DOMAIN=example.com \
BRANCH=main \
REPO_URL=https://github.com/vuthevietgps/quanlyladipage1.git \
PRESERVE_LANDINGPAGES=true \
sudo -E bash /root/redeploy-vps.sh
```

Sau khi hoàn tất:

- Trỏ DNS: `@`, `*`, `admin` → IP VPS
- Mở admin: `http://admin.example.com`
- Cài SSL (khuyến nghị):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d admin.example.com -d "*.example.com"
```

Ghi chú: `redeploy-vps.sh` cho phép ghi đè bằng biến môi trường: `APP_NAME`, `APP_DIR`, `PUBLISHED_DIR`, `UPLOADS_DIR`, `SERVICE_NAME`, `PY_BIN`… để tùy biến đường dẫn và tên dịch vụ.