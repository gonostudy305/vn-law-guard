# Chuẩn bằng chứng

Mỗi kết luận 🔴 hoặc 🟢 cần bằng chứng đúng loại dưới đây. Thiếu thì hạ xuống "dấu hiệu, cần kiểm tra" và nói cần đo gì thêm.

| Loại phát hiện | Bằng chứng đủ | Chưa đủ |
|---|---|---|
| Tracking chạy trước khi đồng ý (01-C) | Phiên `none` trong `scan.json` có cookie theo dõi (`_ga`, `_gcl_au`, `_fbp`, `YSC`…) hoặc request tới GA/Ads/Meta không phải ping `gcs=G100`, kèm URL request | Chỉ thấy `gtag(` trong HTML; chỉ thấy file `gtm.js` được tải |
| Từ chối vẫn bị theo dõi (01-C) | Phiên `decline` có cookie/request theo dõi sau khi bấm nút Từ chối (`clicked` khác rỗng) | Phiên `decline` có `error` (không bấm được nút) |
| Không có nút Từ chối (01-B) | `banner.has_decline = false` + ảnh chụp | Banner không nhận ra được (`banner: null`): kiểm tra bằng tay, có thể banner chỉ hiện theo vùng |
| Ô tích sẵn (01-B) | `forms[].checkboxes[].prechecked = true` + file:dòng nếu có mã nguồn | |
| Chính sách sai/thiếu (01-A) | URL trang + câu trích (≤ 160 ký tự) từ `privacy_pages` | Không mở được trang |
| Thiếu thông tin TMĐT (02-B, 02-C) | Đã xem footer và trang liên hệ/giới thiệu bằng mắt (scanner chỉ đọc trang chủ) | Chỉ dựa vào `ECOM_NO_*` của scanner |
| Đạt 🟢 về cookie | Cả 3 phiên đúng kỳ vọng: `none`, `decline` không có cookie theo dõi; `accept` có | Chỉ đo phiên `accept` |

## Ghi chú kỹ thuật

- `gcs=G1xy`: x = ad_storage, y = analytics_storage (1 granted, 0 denied). `G100` = cả hai từ chối, không đặt cookie. `G1--` = chưa thiết lập Consent Mode.
- Request tới `googletagmanager.com/gtag/js` hay `gtm.js` chỉ là tải thư viện. Với Consent Mode chế độ nâng cao, thư viện có thể tải trước khi đồng ý mà vẫn không đặt cookie: chấm theo cookie và request `collect`, không theo việc tải thư viện. Có nên dùng chế độ nâng cao (gửi ping không cookie) hay chế độ cơ bản (không gửi gì) là câu hỏi cho người làm luật; mặc định khuyên chế độ cơ bản.
- Cookie bên thứ ba (YouTube, Google Maps) đến từ iframe nhúng: tính là theo dõi trước khi đồng ý nếu xuất hiện ở phiên `none`. Sửa bằng `templates/remediation/youtube-facade.html`.
- Shopify: `monorail-edge.shopifysvc.com` là telemetry của nền tảng, Shopify tự áp trạng thái đồng ý; không tự chấm.
- Kết quả phụ thuộc vị trí máy quét. Khách có người dùng ở nhiều nước thì ghi rõ chỉ đo từ Việt Nam.
- Lưu `scan.json`, ảnh chụp cùng báo cáo để đối chiếu khi đo lại sau khi sửa.
