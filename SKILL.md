---
name: vn-law-guard
description: "Audit và rà soát kỹ thuật website đúng pháp luật Việt Nam cho doanh nghiệp: dữ liệu cá nhân (Luật 91/2025, NĐ 356/2025, NĐ 330/2026), thương mại điện tử (Luật 122/2025, NĐ 248/2026), người tiêu dùng, quảng cáo, an ninh mạng, AI. Kế thừa lõi luật mở từ vn-law-check (MIT) và mở rộng 3 năng lực kỹ thuật: quét động bằng trình duyệt thật Playwright (bắt request/cookie trước và sau khi đồng ý), module riêng cho Shopify, WordPress/WooCommerce, Haravan/Sapo, và bộ mẫu vá lỗi (Remediation). Dùng khi người dùng muốn audit kỹ thuật website, kiểm tra cookie banner/Consent Mode, chuẩn bị website trước khi go-live, soạn chính sách bảo mật, sửa form thu thập dữ liệu, hoặc xuất báo cáo bằng chứng khách quan cho khách hàng doanh nghiệp. Also: Vietnam website legal compliance audit, PDPL, cookie consent Vietnam, Shopify Vietnam compliance."
---

# VN Law Guard: Công cụ hỗ trợ rà soát kỹ thuật tuân thủ pháp luật Việt Nam

Lõi pháp lý (checklist, căn cứ, mức phạt) lấy nguyên từ [vn-law-check](https://github.com/mhfed/vn-law-check) (MIT, xem `LICENSE.upstream`, `NOTICE.md`) trong `references/law/`. Skill này thêm phần kỹ thuật: bằng chứng đo trên trình duyệt thật, cách kiểm tra và sửa theo từng nền tảng, và quy trình go-live cho website mới.

## Nguyên tắc bắt buộc

Toàn bộ 8 nguyên tắc trong `references/law/RULES.md` vẫn áp dụng: không kết luận "vi phạm/không vi phạm", không bịa số điều, mức phạt chỉ lấy từ `references/law/08-penalties-reference.md`, giữ thang 🔴🟡🟢⚪, 🔴 chỉ cho lỗi sửa được trong code. Thêm:

1. **Không có bằng chứng thì không chấm.** Mỗi dòng 🔴 hoặc 🟢 về cookie/tracking phải kèm bằng chứng từ `scripts/dynamic_scan.py` (request, cookie, ảnh chụp) hoặc file:dòng trong code. Chỉ grep HTML thì chỉ được ghi "dấu hiệu", không chấm 🟢.
2. **Phân biệt ping Consent Mode với tracking.** Request tới Google có `gcs=G100` (hoặc `G1--`) là ping khi người dùng *chưa/không* đồng ý, không đặt cookie. Ghi nhận, không tự xếp 🔴; nói rõ đây là Consent Mode chế độ nâng cao và để người làm luật quyết. Cookie `_ga`, `_gcl_au`, `_fbp` xuất hiện trước khi đồng ý mới là bằng chứng mạnh.
3. **Kiểm tra ngày dữ liệu luật.** Đọc dòng "Cập nhật" đầu `references/law/legal-references.md`. Cách ngày audit hơn 3 tháng thì ghi cảnh báo ở đầu báo cáo và đề nghị chạy `scripts/sync_upstream.sh`.
4. **Sửa code chỉ khi người dùng đồng ý**, sau khi đã có báo cáo. Website đang chạy (production) thì làm trên bản thử trước, đo lại bằng `dynamic_scan.py`, rồi mới đưa lên.
5. **Không đưa dữ liệu khách ra ngoài.** Scanner chỉ truy cập trang công khai, không gửi form, không đăng nhập, không bấm thanh toán.
6. Báo cáo cho khách doanh nghiệp: luôn có dòng "không phải ý kiến pháp lý" và mục "Cần luật sư xác nhận". Không bán/ghi là "chứng nhận tuân thủ".

## Chọn chế độ

| Người dùng muốn | Chế độ | Bắt đầu ở |
|---|---|---|
| Kiểm tra website đang chạy, làm báo cáo cho khách | **AUDIT** | Quy trình A |
| Làm website mới, hoặc chuẩn bị go-live / chuyển nền tảng | **BUILD** | `references/build-checklist.md` |
| Đã có báo cáo, muốn sửa | **FIX** | Quy trình C |
| Soạn chính sách bảo mật / cookie | **POLICY** | `references/law/10-generate-policy.md` + `templates/remediation/privacy-cookie-section.md` |

## Quy trình A: AUDIT

1. **Quét động** (bắt buộc khi có URL):
   ```bash
   python scripts/dynamic_scan.py https://ten-mien.vn --out ./vn-legal-audit
   ```
   Cần `pip install playwright && python -m playwright install chromium`. Script chạy 3 phiên sạch (chưa chọn / Từ chối / Chấp nhận) ở desktop 1366 và mobile 390, ghi `scan.json`, `scan.md` và ảnh chụp. Đọc `scan.md` trước.
2. **Quét tĩnh** khi có mã nguồn: `bash scripts/scan.sh <thư-mục>` (bản gốc vn-law-check).
3. **Phân loại mức** theo `references/law/00-triage.md`, dùng dữ liệu quét động thay cho đoán (form, tracker, giỏ hàng, chatbot).
4. **Nền tảng:** `scan.json > platform` cho biết Shopify / WordPress / WooCommerce / Haravan / Sapo / khác. Mở đúng file trong `references/platforms/` để biết chỗ cần xem trong admin/theme và cách sửa đặc thù. Nền tảng không có module thì dùng `references/platforms/custom-code.md`.
5. **Mở checklist áp dụng** trong `references/law/` theo bảng ở bước 3. Đối chiếu từng mục với bằng chứng.
6. **Xuất báo cáo** theo `templates/report-template.md` (có cột Bằng chứng). Lưu cạnh thư mục quét.

## Quy trình C: FIX

1. Lấy các dòng 🔴 trong báo cáo, sắp theo "sửa trong một buổi" trước.
2. Với mỗi dòng, tìm mẫu trong `templates/remediation/` và hướng dẫn theo nền tảng trong `references/platforms/`.
3. Trình bày thay đổi dự kiến (file, đoạn code) và chờ người dùng đồng ý.
4. Sửa trên bản thử. Chạy lại `dynamic_scan.py` trên bản thử, so `scan.json` trước/sau.
5. Chỉ đưa lên production khi người dùng xác nhận. Đo lại trên production và cập nhật báo cáo (cột "Trạng thái sau sửa").

## Tài nguyên

- `references/law/`: checklist pháp lý gốc (00-triage … 10-generate-policy, legal-references, RULES).
- `references/platforms/`: shopify.md, wordpress-woocommerce.md, haravan-sapo.md, custom-code.md.
- `references/build-checklist.md`: cổng kiểm tra go-live cho website mới.
- `references/evidence-standard.md`: thế nào là bằng chứng đủ cho từng loại phát hiện.
- `scripts/dynamic_scan.py`: quét động (Playwright). `scripts/scan.sh`, `scripts/fetch-site.sh`: quét tĩnh gốc. `scripts/sync_upstream.sh`: cập nhật lõi luật từ upstream.
- `templates/remediation/`: Consent Mode v2 cho Shopify (`shopify-consent-mode.liquid`, `shopify-cookie-settings-link.liquid`, `shopify-cookie-banner-style.liquid`) và web thường (`generic-consent-mode.html`), video bấm-để-tải (`youtube-facade.html`), ô đồng ý cho form (`form-consent.html`), mục cookie trong chính sách bảo mật (`privacy-cookie-section.md`).
- `templates/report-template.md`: mẫu báo cáo có bằng chứng.
- `examples/`: mẫu báo cáo và mẫu chính sách gốc của vn-law-check.
