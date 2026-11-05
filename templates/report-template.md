# Rà soát pháp lý website: [tên miền]

> 🤖 Báo cáo do AI tạo từ việc đo trên trình duyệt thật và mã nguồn, chỉ để tham khảo, không phải ý kiến pháp lý. Phần lớn mục 🔴 là chỉnh sửa nhỏ trong code, làm được trong vài giờ. Việc gì quan trọng thì hỏi lại người làm luật.

[Nếu dữ liệu luật cũ hơn 3 tháng: ⚠️ Bộ checklist cập nhật ngày …, có thể đã cũ.]

| | |
|---|---|
| Ngày đo | [scan.json > scanned_at] |
| Nền tảng | [scan.json > inventory.platform] |
| Mức (triage) | [0-3] và lý do một dòng |
| Chủ site | [tổ chức / hộ kinh doanh / cá nhân; quy mô nếu biết] |
| Phạm vi | Trang chủ, [trang nội bộ đã mở], các trang chính sách; desktop 1366 + mobile 390; máy quét đặt tại Việt Nam |

## 1. Tóm tắt

- 🔴 [n] việc sửa trong code · 🟡 [n] nên cải thiện / giấy tờ · 🟢 [n] đạt
- Ba việc nên làm trước: …

## 2. Hành vi cookie đo được

| Phiên | Cookie theo dõi | Request theo dõi | Nhận xét |
|---|---|---|---|
| Chưa chọn | | | |
| Bấm Từ chối | | | |
| Bấm Chấp nhận | | | |

Ảnh: `desktop-first-visit.png`, `mobile-first-visit.png`.

## 3. Phát hiện

| # | Mức | Mục checklist | Phát hiện | Bằng chứng | Căn cứ | Đề xuất sửa | Trạng thái sau sửa |
|---|---|---|---|---|---|---|---|
| 1 | 🔴 | 01-C | | `scan.json` phiên … / file:dòng / ảnh | | mẫu `templates/remediation/…` | |

Quy tắc: cột Bằng chứng không được trống với 🔴 và 🟢 (xem `references/evidence-standard.md`). Mức phạt chỉ ghi cho 🔴, lấy từ `references/law/08-penalties-reference.md`, ghi "mức tối đa theo quy định là …", chọn đúng cột tổ chức / cá nhân-hộ kinh doanh.

## 4. Nghĩa vụ giấy tờ, thủ tục (tối đa 🟡 với site nhỏ)

- Mỗi nghĩa vụ một dòng + căn cứ + "nên hỏi người làm luật".

## 5. Không áp dụng

Một dòng gom các lĩnh vực không áp dụng và lý do.

## 6. Cần luật sư xác nhận

- …

## 7. Giới hạn

- Đo từ một vị trí (Việt Nam), một thời điểm; banner của nhiều nền tảng thay đổi theo vùng.
- Scanner mở trang chủ, một trang nội bộ và trang chính sách; trang khác (thanh toán, tài khoản) chưa đo nếu không ghi ở mục Phạm vi.
- Không kiểm tra được xử lý dữ liệu phía máy chủ, hợp đồng với nhà cung cấp, quy trình nội bộ.
- Xác minh văn bản còn hiệu lực tại thuvienphapluat.vn / vbpl.vn trước khi quyết định.
