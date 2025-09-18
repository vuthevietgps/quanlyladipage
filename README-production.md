# 🚀 QUAN LY LANDING PAGE - PRODUCTION DEPLOYMENT

Hệ thống quản lý và phục vụ landing pages với wildcard subdomain, tracking injection và quản lý Agent.

## 📋 TÓM TẮT CHỨC NĂNG

### ✅ Đã Hoàn Thành & Test Thành Công
- **Agent Management**: CRUD hoàn chỉnh với API endpoints
- **Landing Page Management**: Upload, edit, delete, pause/resume
- **Tracking Code Injection**: Google Analytics, Phone, Zalo, Form tracking
- **File Publishing**: Tự động publish HTML + assets vào thư mục public
- **Wildcard Subdomain**: Phục vụ `*.yourdomain.com` từ static files
- **Bootstrap UI**: Responsive 2-pane layout với modal interactions
- **Error Handling**: Validation và error messages chuẩn HTTP

### 🔧 Production Features
- **Environment Configuration**: `.env` support
- **Database Backup**: Automated daily backups
- **Image Management**: Upload, optimize, backup ảnh
- **Security**: File upload validation, CORS headers
- **Monitoring**: Systemd service với auto-restart
- **Performance**: Nginx static file serving với caching

## 🏗️ KIẾN TRÚC PRODUCTION

```
VPS Ubuntu Server
├── Nginx (Reverse Proxy + Static Serving)
│   ├── admin.yourdomain.com → Flask App (Port 5000)  
│   └── *.yourdomain.com → Static Files (/var/www/landingpages/)
├── Flask App (Port 5000)
│   ├── Admin Interface
│   ├── API Endpoints  
│   └── File Processing
├── SQLite Database
│   ├── landing_pages table
│   └── agents table
└── File Storage
    ├── /var/www/landingpages/ (Published sites)
    ├── /var/www/uploads/ (Temporary uploads)
    └── /var/backups/ (Automated backups)
```

## 🚀 DEPLOY LÊN VPS UBUNTU

### Bước 1: Chuẩn Bị VPS
```bash
# SSH vào VPS
ssh root@your-server-ip

# Download code (hoặc upload qua SCP/FTP)
git clone https://github.com/your-repo/quanlyladipage.git
cd quanlyladipage

# Chạy script deploy tự động
sudo bash deploy.sh
```

### Bước 2: Cấu Hình Domain & DNS
Tại nhà cung cấp domain (Cloudflare, GoDaddy, etc.), tạo DNS records:

```
Type    Name     Value               TTL
A       @        YOUR_VPS_IP         300
A       *        YOUR_VPS_IP         300  
A       admin    YOUR_VPS_IP         300
```

### Bước 3: Cấu Hình Environment
```bash
cd /var/www/quanlyladipage
sudo nano .env

# Chỉnh sửa các thông số:
SECRET_KEY=your-super-secret-production-key
ADMIN_DOMAIN=admin.yourdomain.com
WILDCARD_DOMAIN=yourdomain.com
```

### Bước 4: Cài SSL Certificate (Khuyến Nghị)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d admin.yourdomain.com -d "*.yourdomain.com"
```

### Bước 5: Kiểm Tra Hoạt Động
- Admin Panel: `https://admin.yourdomain.com`
- Test Landing: Tạo landing page với subdomain `test123`
- Truy cập: `https://test123.yourdomain.com`

## 📁 QUY TẮC PHÁT TRIỂN LANDING PAGE

### Cấu Trúc File HTML Chuẩn
```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Landing Page Title</title>
    
    <!-- CSS nội bộ hoặc CDN -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Hệ thống tự động inject Google Analytics/Facebook Pixel vào đây -->
</head>
<body>
    <!-- Sử dụng biến tracking trong JavaScript -->
    <script>
        // Truy cập số tracking đã inject
        console.log('Phone:', window.PHONE_TRACKING);
        console.log('Zalo:', window.ZALO_TRACKING); 
        console.log('Form:', window.FORM_TRACKING);
        
        // Tự động cập nhật số điện thoại
        document.addEventListener('DOMContentLoaded', function() {
            if (window.PHONE_TRACKING) {
                document.querySelectorAll('.phone-number').forEach(el => {
                    el.textContent = window.PHONE_TRACKING;
                    el.href = 'tel:' + window.PHONE_TRACKING;
                });
            }
        });
    </script>
    
    <!-- Hệ thống tự động inject tracking codes trước </body> -->
</body>
</html>
```

### Quy Tắc Đường Dẫn Ảnh
```html
<!-- ✅ ĐÚNG: Đường dẫn từ root subdomain -->
<img src="images/logo.png" alt="Logo">
<img src="images/products/item1.jpg" alt="Product">

<!-- ❌ SAI: Đường dẫn tuyệt đối -->
<img src="/var/www/landingpages/subdomain/images/logo.png">
<img src="https://external-site.com/logo.png">
```

## 🖼️ QUẢN LÝ IMAGES

### Upload Ảnh Qua Script
```bash
# Upload tất cả ảnh từ thư mục local
sudo bash images.sh upload my-landing ./local-images/

# Liệt kê ảnh đã upload
bash images.sh list my-landing

# Tối ưu kích thước ảnh
sudo bash images.sh optimize my-landing

# Backup ảnh
sudo bash images.sh backup my-landing
```

### Cấu Trúc Thư Mục Images
```
/var/www/landingpages/my-landing/
├── index.html
└── images/
    ├── logo.png
    ├── banner.jpg
    ├── products/
    │   ├── item1.jpg
    │   └── item2.jpg
    └── icons/
        ├── phone.svg
        └── zalo.png
```

## 🔧 QUẢN TRỊ HỆ THỐNG

### Kiểm Tra Status
```bash
# Flask app
sudo systemctl status quanlyladipage

# Nginx
sudo systemctl status nginx

# Xem logs
sudo journalctl -u quanlyladipage -f
sudo tail -f /var/log/nginx/error.log
```

### Backup & Restore
```bash
# Backup thủ công
sudo cp /var/www/quanlyladipage/database.db /var/backups/backup-$(date +%Y%m%d).db
sudo tar -czf /var/backups/landingpages-$(date +%Y%m%d).tar.gz /var/www/landingpages/

# Restore database
sudo cp /var/backups/backup-20250918.db /var/www/quanlyladipage/database.db
sudo chown www-data:www-data /var/www/quanlyladipage/database.db
```

### Update Code
```bash
cd /var/www/quanlyladipage

# Backup trước khi update
sudo systemctl stop quanlyladipage

# Pull code mới
git pull origin main

# Restart service
sudo systemctl start quanlyladipage
```

## 📊 MONITORING & PERFORMANCE

### Nginx Access Logs Analysis
```bash
# Top 10 subdomain nhiều traffic nhất
sudo awk '{print $1}' /var/log/nginx/access.log | grep -E '\.yourdomain\.com' | sort | uniq -c | sort -nr | head -10

# Response time analysis
sudo awk '{print $NF}' /var/log/nginx/access.log | grep -v '-' | sort -n
```

### Database Statistics
```bash
# Số lượng landing pages
sqlite3 /var/www/quanlyladipage/database.db "SELECT COUNT(*) as total_pages FROM landing_pages;"

# Landing pages theo agent
sqlite3 /var/www/quanlyladipage/database.db "SELECT agent, COUNT(*) as pages FROM landing_pages GROUP BY agent;"

# Top subdomains
sqlite3 /var/www/quanlyladipage/database.db "SELECT subdomain, created_at FROM landing_pages ORDER BY created_at DESC LIMIT 10;"
```

## 🔐 SECURITY CHECKLIST

- [ ] **Firewall**: Chỉ mở port 22, 80, 443
- [ ] **SSL Certificate**: HTTPS cho tất cả domains  
- [ ] **Database Security**: File permissions 664
- [ ] **File Upload**: Validation file types
- [ ] **Rate Limiting**: Nginx rate limit cho API
- [ ] **Admin Access**: Strong password/2FA
- [ ] **Backup Encryption**: Encrypt sensitive backups
- [ ] **Log Rotation**: Setup logrotate
- [ ] **OS Updates**: Regular security updates
- [ ] **Monitoring**: Setup alerts cho downtime

## 🆘 TROUBLESHOOTING

### Landing Page Không Load
1. Kiểm tra DNS: `nslookup test.yourdomain.com`
2. Kiểm tra file: `ls -la /var/www/landingpages/test/`
3. Kiểm tra Nginx: `sudo nginx -t`
4. Xem logs: `sudo tail -f /var/log/nginx/error.log`

### Ảnh Không Hiển Thị  
1. Kiểm tra đường dẫn HTML: `images/logo.png` (không `/images/`)
2. Kiểm tra quyền: `ls -la /var/www/landingpages/subdomain/images/`
3. Test direct access: `curl -I http://subdomain.yourdomain.com/images/logo.png`

### Flask App Không Chạy
1. Kiểm tra service: `sudo systemctl status quanlyladipage`
2. Kiểm tra Python: `cd /var/www/quanlyladipage && source venv/bin/activate && python main.py`
3. Kiểm tra permissions: `sudo chown -R www-data:www-data /var/www/quanlyladipage`

## 📞 SUPPORT

Xem chi tiết tại file `quytac.md` để có hướng dẫn đầy đủ về:
- Cấu hình Nginx chi tiết
- Quy tắc phát triển landing page
- Script quản lý images
- Best practices cho production

---

**Phát triển bởi**: Hệ thống Quan Ly Landing Page  
**Version**: 1.0  
**Update**: September 2025