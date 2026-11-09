# Đóng góp / Contributing

Cảm ơn bạn đã muốn đóng góp. Mọi người, kể cả người nước ngoài, đều có thể gửi issue hoặc pull request bằng tiếng Việt hoặc tiếng Anh.
Thanks for contributing. Issues and pull requests are welcome in Vietnamese or English.

## Dự án gồm hai phần, đóng góp ở hai nơi khác nhau

| Muốn sửa | Gửi tới |
|---|---|
| Checklist, căn cứ, mức phạt trong `references/law/`, `examples/`, `scripts/scan.sh`, `scripts/fetch-site.sh` | Dự án gốc [mhfed/vn-law-check](https://github.com/mhfed/vn-law-check). Repo này lấy về bằng `scripts/sync_upstream.sh`, không sửa trực tiếp để không lệch bản gốc. |
| Bộ quét động, hướng dẫn nền tảng, mẫu sửa lỗi, mẫu báo cáo, tài liệu | Repo này. |

Nếu phát hiện sai sót pháp lý mà cần cảnh báo ngay, mở issue "Cập nhật luật" ở đây; chúng tôi sẽ chuyển lên dự án gốc.

## Quy tắc nội dung pháp lý

1. Mỗi khẳng định cần nguồn: số hiệu văn bản, điều, khoản, kèm link (ưu tiên vbpl.vn, Công báo, cổng của Chính phủ/Bộ).
2. Chưa đối chiếu được văn bản gốc thì ghi rõ "CHƯA XÁC MINH" hoặc "theo nguồn thứ cấp". Không đưa mức phạt từ trí nhớ.
3. Văn phong trung tính: không dọa phạt, không hứa "an toàn 100%", không "chứng nhận tuân thủ".
4. Không đưa tên, dữ liệu của website hay khách hàng thật vào ví dụ khi chưa có đồng ý. Dùng `example.vn`.

## Quy tắc code

- Python 3.10+, chỉ phụ thuộc `playwright`. Thêm thư viện mới cần lý do rõ ràng.
- Bộ quét chỉ đọc: không gửi form, không đăng nhập, không bấm thanh toán.
- Mã tín hiệu (`code`) là giao diện ổn định: không đổi tên mã đã phát hành; thêm mã mới thì thêm chữ cho **cả** `vi` và `en` trong `MESSAGES`.
- Thêm nền tảng mới: một file trong `references/platforms/`, ghi rõ đã kiểm chứng trên dự án thật hay chưa.
- Mẫu sửa lỗi: dùng ID giả (`G-XXXXXXXXXX`), ghi rõ chỗ cần thay, đã thử bằng `dynamic_scan.py` trước và sau.

## Kiểm tra trước khi gửi PR

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest
```

Test không gọi Internet. Thay đổi hành vi bộ quét cần có test (xem `tests/test_dynamic_scan.py` để biết cách dựng trang thử).

## Commit

Dùng tiền tố `feat:`, `fix:`, `docs:`, `test:`, `chore:`. Ghi lại thay đổi đáng chú ý vào `CHANGELOG.md`.

Tham gia dự án đồng nghĩa đồng ý với [Quy tắc ứng xử](CODE_OF_CONDUCT.md).
