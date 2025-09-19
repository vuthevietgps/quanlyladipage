# Quy tắc tạo file index.html cho Landing Page (Tracking-ready)

Mục tiêu: Khi upload index.html, hệ thống sẽ tự động chèn (inject) các mã tracking (Google Ads/Analytics, Facebook Pixel, Phone/Zalo/Form tracking) mà KHÔNG cần sửa tay trong HTML.

## 1) Sử dụng placeholder (khuyến nghị)
Chèn các placeholder sau vào HTML để kiểm soát chính xác vị trí mã tracking được chèn:

- Ở trong <head>:
  <!-- TRACKING_HEAD -->

- Ở gần cuối <body> (trước </body>):
  <!-- TRACKING_BODY -->

Hệ thống sẽ thay thế placeholder bằng nội dung tracking tương ứng.

Ví dụ khung cơ bản:

<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tiêu đề Landing</title>
  <!-- TRACKING_HEAD -->
</head>
<body>
  <!-- Nội dung landing của bạn -->

  <!-- TRACKING_BODY -->
</body>
</html>

Lưu ý: Placeholder không phân biệt hoa thường, có thể viết <!--   tracking_body   -->.

## 2) Không có placeholder? Hệ thống vẫn hoạt động
- Nếu KHÔNG có <!-- TRACKING_HEAD -->: hệ thống sẽ chèn tracking head trước thẻ </head>. Nếu không có </head> thì sẽ chèn lên đầu file.
- Nếu KHÔNG có <!-- TRACKING_BODY -->: hệ thống sẽ chèn tracking body trước thẻ </body>. Nếu không có </body> thì chèn vào cuối file.

## 3) Tính idempotent (không bị chèn lặp)
Khi bạn cập nhật Landing (PUT), hệ thống sẽ tự gỡ các block tracking đã từng chèn trước đó (theo comment markers) rồi chèn lại. Do đó, bạn có thể update nhiều lần mà không bị nhân đôi mã.

Các khối được nhận diện bằng comment:
- Head block:
  <!-- Global Site Tag -->
  ... (nội dung do hệ thống chèn)
  <!-- /Global Site Tag -->

- Body block:
  <!-- Tracking Codes -->
  ... (nội dung do hệ thống chèn)
  <!-- /Tracking Codes -->

## 4) Bạn cần chuẩn bị gì trong admin khi tạo Landing
- Global Site Tag: dán script Google Ads/Analytics hoặc Facebook Pixel (hệ thống sẽ đưa vào phần head).
- Phone/Form/Zalo Tracking: điền giá trị mã theo dõi phù hợp (hệ thống sẽ gán vào biến JS ở cuối body):
  - window.PHONE_TRACKING = "...";
  - window.ZALO_TRACKING  = "...";
  - window.FORM_TRACKING  = "...";

Bạn có thể dùng các biến này trong JS của bạn nếu cần ghi log sự kiện.

## 5) Số điện thoại hiển thị
Bạn muốn hiển thị/href số điện thoại cố định theo thiết kế thì đặt trực tiếp trong index.html (ví dụ <a href="tel:0987654321">Gọi ngay</a>). Hệ thống SẼ KHÔNG tự thay số điện thoại trong HTML.

## 6) Quy ước ảnh
- Nếu upload ảnh kèm theo, hãy dùng đường dẫn tương đối trong HTML (ví dụ <img src="./anh1.jpg">).
- Tối đa 7 ảnh; hệ thống sẽ đổi tên lần lượt anh1.jpg, anh2.png, ... theo thứ tự upload.

---
Cần thêm mẫu HTML chuẩn có sẵn placeholder? Hãy tạo từ file mẫu trong repo và giữ nguyên hai placeholder để việc chèn tracking luôn chính xác.
