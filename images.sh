#!/bin/bash

# Image Management Script cho Landing Pages
# Sử dụng: bash images.sh <command> <subdomain> [source_dir]

APP_NAME="quanlyladipage"
PUBLISHED_DIR="/var/www/landingpages"

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }

show_help() {
    echo "🖼️  LANDING PAGE IMAGE MANAGER"
    echo ""
    echo "Cách sử dụng:"
    echo "  bash images.sh <command> <subdomain> [options]"
    echo ""
    echo "Commands:"
    echo "  upload <subdomain> <source_dir>  - Upload ảnh từ thư mục local lên subdomain"
    echo "  download <subdomain> <dest_dir>  - Download ảnh từ subdomain về local"
    echo "  list <subdomain>                 - Liệt kê tất cả ảnh của subdomain"
    echo "  optimize <subdomain>             - Tối ưu kích thước ảnh của subdomain"
    echo "  backup <subdomain>               - Backup ảnh của subdomain"
    echo "  clean <subdomain>                - Xóa ảnh không sử dụng"
    echo "  info <subdomain>                 - Thông tin chi tiết về ảnh"
    echo ""
    echo "Ví dụ:"
    echo "  bash images.sh upload my-product ./local-images/"
    echo "  bash images.sh list my-product"
    echo "  bash images.sh optimize my-product"
}

check_subdomain() {
    local subdomain=$1
    if [ -z "$subdomain" ]; then
        print_error "Vui lòng cung cấp tên subdomain"
        return 1
    fi
    
    if [ ! -d "$PUBLISHED_DIR/$subdomain" ]; then
        print_error "Subdomain '$subdomain' không tồn tại"
        print_info "Có sẵn: $(ls $PUBLISHED_DIR 2>/dev/null | tr '\n' ' ')"
        return 1
    fi
    return 0
}

upload_images() {
    local subdomain=$1
    local source_dir=$2
    
    if [ -z "$source_dir" ]; then
        print_error "Vui lòng cung cấp thư mục nguồn"
        return 1
    fi
    
    if [ ! -d "$source_dir" ]; then
        print_error "Thư mục nguồn '$source_dir' không tồn tại"
        return 1
    fi
    
    check_subdomain $subdomain || return 1
    
    local dest_dir="$PUBLISHED_DIR/$subdomain/images"
    mkdir -p "$dest_dir"
    
    print_status "Đang upload ảnh từ '$source_dir' lên '$subdomain'..."
    
    # Copy tất cả file ảnh
    find "$source_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.svg" -o -iname "*.webp" -o -iname "*.ico" \) -exec cp {} "$dest_dir/" \;
    
    # Cấp quyền
    chown -R www-data:www-data "$dest_dir"
    chmod -R 755 "$dest_dir"
    
    local count=$(find "$dest_dir" -type f | wc -l)
    print_status "✅ Đã upload $count ảnh thành công!"
    
    # Hiển thị thông tin
    print_info "Đường dẫn server: $dest_dir"
    print_info "URL truy cập: http://$subdomain.yourdomain.com/images/"
    
    list_images $subdomain
}

download_images() {
    local subdomain=$1
    local dest_dir=$2
    
    if [ -z "$dest_dir" ]; then
        dest_dir="./images-$subdomain"
    fi
    
    check_subdomain $subdomain || return 1
    
    local source_dir="$PUBLISHED_DIR/$subdomain/images"
    
    if [ ! -d "$source_dir" ]; then
        print_error "Thư mục ảnh của subdomain '$subdomain' không tồn tại"
        return 1
    fi
    
    mkdir -p "$dest_dir"
    
    print_status "Đang download ảnh từ '$subdomain' về '$dest_dir'..."
    
    cp -r "$source_dir"/* "$dest_dir/" 2>/dev/null || true
    
    local count=$(find "$dest_dir" -type f | wc -l)
    print_status "✅ Đã download $count ảnh thành công!"
}

list_images() {
    local subdomain=$1
    check_subdomain $subdomain || return 1
    
    local images_dir="$PUBLISHED_DIR/$subdomain/images"
    
    if [ ! -d "$images_dir" ]; then
        print_warning "Thư mục images chưa tồn tại cho subdomain '$subdomain'"
        return 0
    fi
    
    print_info "📁 Danh sách ảnh của subdomain '$subdomain':"
    echo ""
    
    local count=0
    while IFS= read -r -d '' file; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            local size=$(du -h "$file" | cut -f1)
            local modified=$(stat -c %y "$file" | cut -d' ' -f1)
            printf "  %-20s %8s  %12s\n" "$filename" "$size" "$modified"
            ((count++))
        fi
    done < <(find "$images_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.svg" -o -iname "*.webp" -o -iname "*.ico" \) -print0)
    
    echo ""
    print_status "Tổng cộng: $count ảnh"
    
    if [ $count -gt 0 ]; then
        local total_size=$(du -sh "$images_dir" 2>/dev/null | cut -f1)
        print_info "Tổng dung lượng: $total_size"
        print_info "URL truy cập: http://$subdomain.yourdomain.com/images/"
    fi
}

optimize_images() {
    local subdomain=$1
    check_subdomain $subdomain || return 1
    
    local images_dir="$PUBLISHED_DIR/$subdomain/images"
    
    if [ ! -d "$images_dir" ]; then
        print_warning "Thư mục images chưa tồn tại cho subdomain '$subdomain'"
        return 0
    fi
    
    print_status "Đang tối ưu ảnh cho subdomain '$subdomain'..."
    
    # Cài đặt tools nếu chưa có
    if ! command -v jpegoptim &> /dev/null; then
        print_status "Cài đặt jpegoptim..."
        apt update && apt install -y jpegoptim
    fi
    
    if ! command -v pngquant &> /dev/null; then
        print_status "Cài đặt pngquant..."
        apt update && apt install -y pngquant
    fi
    
    # Backup trước khi optimize
    local backup_dir="/tmp/images-backup-$subdomain-$(date +%Y%m%d-%H%M%S)"
    cp -r "$images_dir" "$backup_dir"
    print_info "Đã backup vào: $backup_dir"
    
    local optimized=0
    
    # Optimize JPEG
    find "$images_dir" -name "*.jpg" -o -name "*.jpeg" | while read -r file; do
        if jpegoptim --max=85 --preserve --quiet "$file"; then
            ((optimized++))
        fi
    done
    
    # Optimize PNG  
    find "$images_dir" -name "*.png" | while read -r file; do
        if pngquant --quality=65-80 --force --ext .png "$file" 2>/dev/null; then
            ((optimized++))
        fi
    done
    
    print_status "✅ Đã tối ưu ảnh xong!"
    print_info "Backup gốc tại: $backup_dir"
    
    # So sánh kích thước
    local old_size=$(du -sh "$backup_dir" | cut -f1)
    local new_size=$(du -sh "$images_dir" | cut -f1)
    print_info "Kích thước trước: $old_size"
    print_info "Kích thước sau: $new_size"
}

backup_images() {
    local subdomain=$1
    check_subdomain $subdomain || return 1
    
    local images_dir="$PUBLISHED_DIR/$subdomain/images"
    local backup_file="/var/backups/images-$subdomain-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    if [ ! -d "$images_dir" ]; then
        print_warning "Thư mục images chưa tồn tại cho subdomain '$subdomain'"
        return 0
    fi
    
    print_status "Đang backup ảnh của subdomain '$subdomain'..."
    
    tar -czf "$backup_file" -C "$images_dir" .
    
    print_status "✅ Backup thành công!"
    print_info "File backup: $backup_file"
    print_info "Kích thước: $(du -h "$backup_file" | cut -f1)"
}

get_image_info() {
    local subdomain=$1
    check_subdomain $subdomain || return 1
    
    local images_dir="$PUBLISHED_DIR/$subdomain/images"
    
    if [ ! -d "$images_dir" ]; then
        print_warning "Thư mục images chưa tồn tại cho subdomain '$subdomain'"
        return 0
    fi
    
    print_info "📊 Thông tin chi tiết ảnh của subdomain '$subdomain':"
    echo ""
    
    # Thống kê theo loại file
    echo "Loại file:"
    find "$images_dir" -type f | grep -o '\.[^.]*$' | sort | uniq -c | sort -nr | while read -r count ext; do
        printf "  %-10s: %d files\n" "$ext" "$count"
    done
    echo ""
    
    # Top 5 file lớn nhất
    echo "Top 5 file lớn nhất:"
    find "$images_dir" -type f -exec du -h {} + | sort -hr | head -5 | while read -r size file; do
        local filename=$(basename "$file")
        printf "  %-6s %s\n" "$size" "$filename"
    done
    echo ""
    
    # Thống kê tổng quan
    local total_files=$(find "$images_dir" -type f | wc -l)
    local total_size=$(du -sh "$images_dir" | cut -f1)
    local avg_size=$(( $(du -sb "$images_dir" | cut -f1) / $total_files / 1024 ))
    
    print_info "Tổng số file: $total_files"
    print_info "Tổng dung lượng: $total_size"
    print_info "Kích thước trung bình: ${avg_size}KB/file"
}

# Main script
case "${1:-help}" in
    "upload")
        upload_images "$2" "$3"
        ;;
    "download")
        download_images "$2" "$3"
        ;;
    "list")
        list_images "$2"
        ;;
    "optimize")
        optimize_images "$2"
        ;;
    "backup")
        backup_images "$2"
        ;;
    "info")
        get_image_info "$2"
        ;;
    "help"|*)
        show_help
        ;;
esac