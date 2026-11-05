# Website tự code (Next.js, React, Vue, PHP, HTML tĩnh...)

## 1. Quét

- Có mã nguồn: `bash scripts/scan.sh <thư-mục>` (tĩnh) + `python scripts/dynamic_scan.py <URL staging hoặc production>` (động). Quét tĩnh tìm chỗ gắn, quét động xác nhận hành vi thật.
- SPA: script theo dõi thường nằm trong bundle hoặc được nạp qua GTM, grep HTML không thấy. Chỉ tin kết quả động.

## 2. Cổng đồng ý

- Mặc định từ chối: `gtag('consent','default',{...denied})` chạy trước mọi thẻ Google, và chỉ chèn thẻ `gtag/js`, `gtm.js`, pixel sau khi người dùng chấp nhận (`templates/remediation/generic-consent-mode.html`).
- Next.js: không đặt `<Script src="...gtag/js">` thẳng trong layout; chèn có điều kiện theo trạng thái đồng ý, hoặc dùng một CMP có hỗ trợ Consent Mode.
- Lưu lựa chọn kèm phiên bản nội dung banner, ví dụ `{"v": "2026-11", "analytics": false, "marketing": false, "ts": "..."}`, để chứng minh người dùng đã đồng ý với nội dung nào (01-B, bằng chứng đồng ý). Nếu ghi nhật ký phía server thì dùng mã ngẫu nhiên, không gắn với tên/email.
- Có đường mở lại tùy chọn (link "Cài đặt cookie" ở footer). Khi rút đồng ý thì gọi `gtag('consent','update', {...denied})` và xóa cookie `_ga*`, `_gcl_*`, `_fbp`.

## 3. Form và API

- Ô đồng ý không tích sẵn, tách theo mục đích; server từ chối request thiếu đồng ý bắt buộc.
- Lưu thời điểm đồng ý và nội dung câu đồng ý cùng bản ghi.
- Dữ liệu gửi sang dịch vụ ngoài (email, CRM, Google Sheet, AI API) phải nằm trong danh sách bên nhận của chính sách; dịch vụ đặt ngoài Việt Nam → xét 01-D.
- Chatbot gọi AI: xem `references/law/07-ai-transparency.md`.

## 4. Kiểm tra

Đặt `dynamic_scan.py` vào CI trên staging, cho fail khi phiên `none` hoặc `decline` có cookie theo dõi.
