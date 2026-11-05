# BUILD: cổng kiểm tra cho website mới hoặc trước khi go-live

Dùng khi làm website mới, chuyển nền tảng, hoặc đổi tên miền. Mỗi mục ghi rõ ai làm (dev / chủ site / người làm luật) và cách kiểm. Chi tiết căn cứ ở checklist tương ứng trong `references/law/`.

## Giai đoạn 1: thiết kế (trước khi code)

- [ ] Xác định mức (00-triage): có form? tracking? bán hàng/đặt hàng? tài khoản? chatbot? → danh sách checklist phải đạt.
- [ ] Liệt kê dữ liệu cá nhân sẽ thu: trường nào, mục đích nào, lưu ở đâu (nền tảng, email, Sheet, CRM), lưu bao lâu, ai nhận. Bảng này là đầu vào của chính sách bảo mật (01-A) và câu hỏi chuyển dữ liệu ra nước ngoài (01-D).
- [ ] Chọn cách xin đồng ý cookie theo nền tảng (`references/platforms/`), mặc định từ chối.
- [ ] Mỗi mục đích phụ (khuyến mại, chia sẻ đối tác) có ô đồng ý riêng.
- [ ] Bán hàng/đặt hàng: chuẩn bị nội dung công bố bắt buộc (02-C), xác định thông báo hay đăng ký với Bộ Công Thương (02-A, 02-B). Thủ tục: chủ site + người làm luật.

## Giai đoạn 2: xây dựng

- [ ] Không gắn thẳng thẻ GA/GTM/Pixel; đi qua cổng đồng ý (`templates/remediation/`).
- [ ] Video/bản đồ nhúng dùng bấm-để-tải (`youtube-facade.html`) hoặc youtube-nocookie.
- [ ] Form: câu thông báo mục đích + link chính sách; ô đồng ý không tích sẵn; lưu thời điểm + phiên bản câu đồng ý (`form-consent.html`).
- [ ] Footer: link chính sách bảo mật, điều khoản, đổi trả, vận chuyển, thanh toán, khiếu nại, liên hệ; tên doanh nghiệp, mã số thuế, địa chỉ, điện thoại, email; link "Cài đặt cookie"; logo/link Bộ Công Thương khi đã thông báo/đăng ký.
- [ ] Chính sách bảo mật theo `references/law/10-generate-policy.md` + mục cookie (`privacy-cookie-section.md`), dẫn Luật 91/2025 và NĐ 356/2025. Chỉ một trang chính sách bảo mật "chính"; trang tự sinh của nền tảng (vd Shopify `/policies/privacy-policy`) phải cùng nội dung hoặc chuyển hướng.
- [ ] Chatbot AI: thông báo người dùng đang nói chuyện với AI (07).
- [ ] Giá, phí, khuyến mại hiện đủ trước khi đặt hàng (02-H, 04).

## Giai đoạn 3: trước go-live (cổng chặn)

Chạy trên bản staging/theme thử:

```bash
python scripts/dynamic_scan.py https://staging.ten-mien.vn --out ./golive-scan
```

Chỉ go-live khi:

- [ ] Phiên `none` và `decline`: 0 cookie theo dõi, 0 request theo dõi (trừ ping `gcs=G100` nếu đã chấp nhận dùng chế độ nâng cao).
- [ ] Phiên `accept`: có cookie/request của đúng công cụ đã công bố trong chính sách (đo lường không bị hỏng).
- [ ] Banner có nút Từ chối, hiển thị gọn trên mobile 390 (không che quá ~40% màn hình), không che nút gọi/chat chính.
- [ ] `signals` trong `scan.json` không còn mục 01-*. Mục 02-* đã xem bằng mắt.
- [ ] Bảng cookie trong chính sách khớp phiên `accept`.

## Giai đoạn 4: sau go-live

- [ ] Chạy lại `dynamic_scan.py` trên tên miền thật (nền tảng có thể bật/tắt banner theo tên miền, vd Shopify theo vùng).
- [ ] Biến kiểu `tracking_host` khớp tên miền chính.
- [ ] Đo lại mỗi khi thêm app, plugin, thẻ quảng cáo mới, hoặc 3 tháng một lần.
- [ ] Đặt lịch: website đăng ký Bộ Công Thương theo khung cũ được hoạt động đến 30/06/2027 (Điều 41 Luật 122/2025), cần làm lại thủ tục theo luật mới trước mốc đó (chủ site + người làm luật).
