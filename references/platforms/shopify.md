# Shopify

Kinh nghiệm đúc kết từ triển khai thực tế trên website sản xuất B2B (11/2026). Mã mẫu: `templates/remediation/shopify-*.liquid`.

## 1. Banner cookie của Shopify (Customer Privacy)

- Admin → Cài đặt → Quyền riêng tư của khách hàng → Biểu ngữ cookie.
- **Bẫy lớn nhất:** mặc định Shopify coi Việt Nam là vùng *không* bắt buộc xin đồng ý. Khi đó banner không hiện với khách VN và Customer Privacy API trả "đã cho phép" cho mọi thứ: tracking chạy ngay dù theme có gắn cổng chặn.
  - Kiểm tra: GraphQL Admin `consentPolicy { countryCode consentRequired }` hoặc mở site từ IP Việt Nam trong cửa sổ ẩn danh xem banner có hiện không.
  - Sửa: tắt "Dùng cài đặt tự động" trong trang Biểu ngữ cookie và chọn hiện banner cho Việt Nam, hoặc gọi `consentPolicyUpdate(consentPolicies: [{countryCode: VN, consentRequired: true, dataSaleOptOutRequired: false}])`. Cần cả hai: chỉ đổi API mà không tắt cài đặt tự động thì banner vẫn có thể không hiện.
- Banner có sẵn nút Chấp nhận, Từ chối, Quản lý tùy chọn: đạt yêu cầu "từ chối dễ như chấp nhận" (01-B).
- Chữ mặc định khá dài. Rút gọn trong Admin để banner nhỏ trên mobile; theme không đổi được nội dung chữ.
- Theme CSS có thể đè vị trí banner (ví dụ `section { margin }` làm banner nổi lên khỏi đáy). Shopify chèn `<style>` của nó sau CSS theme nên muốn chỉnh phải dùng `!important` (mẫu: `templates/remediation/shopify-cookie-banner-style.liquid`).

## 2. Tracking gắn trong theme

Tìm script gắn thẳng trong `layout/theme.liquid`, `snippets/*`, `sections/*`:

```bash
grep -rnE "gtag\(|googletagmanager|fbq\(|connect\.facebook|analytics\.tiktok|clarity\.ms" layout snippets sections
```

- Gắn thẳng `<script async src="https://www.googletagmanager.com/gtag/js?...">` = chạy trước khi đồng ý → 🔴 01-C (có bằng chứng `dynamic_scan`).
- Sửa: thay bằng `templates/remediation/shopify-consent-mode.liquid` (Consent Mode v2, mặc định từ chối, chỉ nạp GA4/GTM sau khi khách đồng ý qua Customer Privacy API, nghe sự kiện `visitorConsentCollected`). Bỏ luôn `<noscript>` iframe của GTM vì nó không qua được cổng.
- Nếu theme chỉ bật tracking trên tên miền thật (biến kiểu `tracking_host`), nhớ kiểm tra biến đó khớp tên miền chính sau khi đổi domain.

## 3. Tracking không nằm trong theme

- **Ứng dụng Google & YouTube, Facebook & Instagram** của Shopify: tuân theo Customer Privacy API. Không gắn trùng thẻ trong theme.
- **Cài đặt → Sự kiện khách hàng → Pixel tùy chỉnh:** mỗi pixel có mục Quyền (permission). Đặt yêu cầu Phân tích/Tiếp thị tương ứng, không để "Không bắt buộc".
- **App embeds** (Cửa hàng trực tuyến → Chủ đề → Tùy chỉnh → Nhúng ứng dụng) và app cũ dùng ScriptTag: liệt kê từng app, xem app nào nạp tracker (dựa vào `third_party_hosts` trong `scan.json`).
- Telemetry `monorail-edge.shopifysvc.com` là của nền tảng, Shopify tự áp trạng thái đồng ý; scanner không tính là tracking.

## 4. Form

- `{% form 'contact' %}` (liên hệ, báo giá): thêm một dòng nêu mục đích + link chính sách cạnh nút Gửi. Thu nhiều mục đích (tư vấn + gửi khuyến mại) thì tách ô đồng ý riêng, không tích sẵn (`templates/remediation/form-consent.html`).
- `{% form 'customer' %}` (đăng ký nhận tin): `accepts_marketing` không được tích sẵn.
- Dữ liệu form Shopify gửi về email chủ cửa hàng và lưu trên Shopify; nếu có worker/Apps Script đẩy sang Google Sheet thì ghi cả Google vào danh sách bên nhận trong chính sách.

## 5. Trang chính sách

- Cài đặt → Chính sách: Shopify tạo `/policies/privacy-policy`, `refund-policy`, `shipping-policy`, `terms-of-service`, `contact-information`. Mẫu tự sinh của Shopify viết theo luật nước ngoài: phải sửa theo luật VN (`references/law/10-generate-policy.md`).
- Trang `/pages/...` tự tạo: kiểm tra có dẫn NĐ 13/2023 (hết hiệu lực 01/01/2026) hay câu "không cung cấp cho bên thứ ba" trong khi dùng Shopify/Google. `dynamic_scan` tự bắt hai lỗi này.
- Thêm link "Cài đặt cookie" ở footer để khách rút/đổi lựa chọn (`templates/remediation/shopify-cookie-settings-link.liquid`, gọi `window.privacyBanner.showPreferences()`).

## 6. Chuyển dữ liệu ra nước ngoài (01-D)

Dữ liệu cửa hàng Shopify lưu ở nước ngoài, nên mọi cửa hàng Shopify có thu dữ liệu khách đều thuộc diện xét khoản 2 Điều 20 Luật 91/2025. Với cửa hàng nhỏ: tối đa 🟡, một dòng, khuyên hỏi người làm luật.

## 7. Bằng chứng đồng ý

Shopify lưu lựa chọn trong cookie `_tracking_consent` phía trình duyệt. Chưa rõ Shopify có lưu nhật ký đồng ý phía máy chủ mà chủ shop xuất ra được hay không (chưa xác minh). Ghi là câu hỏi mở cho người làm luật khi xét yêu cầu "lưu được bằng chứng đồng ý" (01-B).

## 8. Kiểm tra sau khi sửa

1. Đẩy lên theme thử (không phải theme đang chạy), xem trước.
2. `python scripts/dynamic_scan.py <URL theme thử>`. Thanh xem trước của Shopify (`#PBarNextFrameWrapper`) có thể che nút banner; nếu phiên decline/accept báo lỗi bấm, xóa phần tử đó hoặc kiểm tra sau khi publish.
3. Mong đợi: phiên `none` và `decline` 0 cookie theo dõi; phiên `accept` có `_ga`, `_gcl_au`...
4. Publish, chạy lại trên tên miền thật, đưa bảng 3 phiên vào báo cáo.
