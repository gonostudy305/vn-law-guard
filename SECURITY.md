# Bảo mật / Security

## Báo lỗi bảo mật

Không mở issue công khai cho lỗi bảo mật. Hãy dùng **Report a vulnerability** trong tab [Security](https://github.com/gonostudy305/vn-law-guard/security/advisories/new) của repo (GitHub private vulnerability reporting).

Please do not open public issues for security problems. Use **Report a vulnerability** in the repository's [Security](https://github.com/gonostudy305/vn-law-guard/security/advisories/new) tab.

Chúng tôi sẽ phản hồi trong khoảng 7 ngày.

## Phạm vi

- Lỗi khiến bộ quét gửi dữ liệu ra ngoài website đang quét, ghi file ngoài thư mục `--out`, hoặc chạy mã từ trang được quét trên máy người dùng.
- Mẫu sửa lỗi (`templates/remediation/`) làm lộ dữ liệu người dùng hoặc mở lỗ hổng (XSS…) trên website áp dụng.

Sai sót về nội dung pháp lý không phải lỗi bảo mật: mở issue "Cập nhật luật".

## Lưu ý khi dùng

`scan.json`, `scan.md` và ảnh chụp có thể chứa URL, email, số điện thoại công khai của website được quét. Không commit kết quả quét của khách hàng vào repo công khai.
