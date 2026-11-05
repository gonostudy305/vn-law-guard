# Haravan / Sapo

> Module này chưa được kiểm chứng trên dự án thật. Tên menu trong admin có thể khác theo phiên bản: xác nhận lại trên tài khoản của khách trước khi ghi vào báo cáo.

## 1. Tracking

- Cả hai nền tảng cho phép dán mã GA4/GTM/Pixel trong phần cấu hình chung của admin hoặc trực tiếp trong theme (theme dùng cú pháp giống Liquid). Mã dán theo cách này nạp ngay khi tải trang.
- Chưa xác minh được nền tảng có banner đồng ý cookie dựng sẵn hay không. Nếu không có: tự thêm banner trong theme + cổng Consent Mode (`templates/remediation/generic-consent-mode.html`), và chuyển toàn bộ mã tracking từ ô cấu hình chung vào cổng đó.
- App/plugin từ kho ứng dụng có thể chèn script riêng: đối chiếu `third_party_hosts` trong `scan.json`.

## 2. Form và thông tin bắt buộc

- Form liên hệ, đăng ký nhận tin, đặt hàng nằm trong file template của theme: thêm câu nêu mục đích, link chính sách, ô đồng ý không tích sẵn (`templates/remediation/form-consent.html`).
- Trang chính sách, đổi trả, vận chuyển, thanh toán, khiếu nại; thông tin doanh nghiệp và link Bộ Công Thương ở footer (02-B, 02-C).

## 3. Dữ liệu lưu ở đâu (01-D)

Hỏi khách hoặc xem hợp đồng/điều khoản của nền tảng để biết dữ liệu đơn hàng lưu trong hay ngoài Việt Nam. Không suy đoán. Chưa rõ thì ghi "chưa xác định vị trí lưu trữ" và xếp 🟡.

## 4. Kiểm tra

Như mọi nền tảng: `dynamic_scan.py` trước và sau khi sửa, so bảng 3 phiên.
