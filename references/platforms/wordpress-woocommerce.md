# WordPress / WooCommerce

## 1. Tìm chỗ nạp tracking

Tracking trên WordPress thường đến từ nhiều chỗ cùng lúc, nên đo bằng `dynamic_scan.py` trước rồi mới lần nguồn:

- Plugin: Site Kit by Google, GTM4WP, MonsterInsights, PixelYourSite, Facebook for WooCommerce...
- Plugin chèn mã đầu trang (Insert Headers and Footers, WPCode...): mã dán tay ở đây chạy trước khi đồng ý.
- Theme: `header.php`, `functions.php` (`wp_head`), tùy chọn "Mã theo dõi" trong theme options.

```bash
grep -rnE "gtag\(|googletagmanager|fbq\(|analytics\.tiktok|clarity\.ms" wp-content/themes wp-content/mu-plugins
```

## 2. Banner đồng ý

- Dùng plugin quản lý đồng ý có hỗ trợ Google Consent Mode v2 và chặn script trước khi đồng ý (ví dụ Complianz, CookieYes, Cookiebot). `dynamic_scan` nhận ra các banner này.
- Cấu hình phải có nút Từ chối ngang hàng nút Chấp nhận. Nhiều plugin mặc định chỉ có "Chấp nhận" + "Cài đặt": đó là 01-B.
- Chọn cấu hình cho vùng Việt Nam theo chế độ "opt-in" (mặc định từ chối). Một số plugin mặc định áp opt-out ngoài EU: kiểm tra bằng phiên `none` của scanner.
- Plugin cache (WP Rocket, LiteSpeed Cache...) có thể cache trang kèm trạng thái đồng ý của người khác hoặc gộp/hoãn script làm vỡ cổng chặn: chạy scanner sau khi xóa cache.
- Tracking cấu hình trong plugin quản lý đồng ý hoặc qua GTM có Consent Mode, không dán tay trong header.

## 3. Form

- Contact Form 7: thêm thẻ `[acceptance ...]` (mặc định không tích) kèm câu nêu mục đích và link chính sách.
- WPForms, Gravity Forms, Fluent Forms: có trường "đồng ý / GDPR agreement" hoặc checkbox; không đặt giá trị mặc định là đã chọn.
- Form gửi qua dịch vụ ngoài (Mailchimp, HubSpot...) thì ghi bên nhận và vị trí lưu trữ trong chính sách (01-A, 01-D).

## 4. WooCommerce

- WooCommerce → Cài đặt → Tài khoản & Quyền riêng tư: chọn trang chính sách bảo mật, sửa câu thông báo ở trang đăng ký và trang thanh toán cho phù hợp.
- Trang thanh toán: ô đồng ý điều khoản không tích sẵn; ô nhận tin khuyến mại tách riêng.
- Công bố thông tin bắt buộc (02-C): đổi trả, vận chuyển, thanh toán, khiếu nại, thông tin doanh nghiệp, link Bộ Công Thương ở footer.
- Giá, phí vận chuyển, thuế hiện trước khi đặt hàng, không có phí ẩn ở bước cuối (04).

## 5. Quyền của chủ thể dữ liệu

WordPress có công cụ lõi Công cụ → Xuất dữ liệu cá nhân / Xóa dữ liệu cá nhân. Dùng nó để đáp ứng yêu cầu xem/xóa trong thời hạn ở 01-A, và ghi kênh nhận yêu cầu trong chính sách.

## 6. Kiểm tra sau khi sửa

Xóa cache → `dynamic_scan.py` → phiên `none` và `decline` 0 cookie theo dõi, phiên `accept` có cookie. Kiểm tra cả trang sản phẩm và trang thanh toán (scanner chỉ mở trang chủ và một trang nội bộ; mở thêm bằng tay nếu cần).
