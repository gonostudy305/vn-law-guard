# VN Law Guard

[![tests](https://github.com/gonostudy305/vn-law-guard/actions/workflows/tests.yml/badge.svg)](https://github.com/gonostudy305/vn-law-guard/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Tiếng Việt** · [English](README.en.md)

🌐 [Trang giới thiệu kỹ thuật](https://gonovn.me/vn-law-guard/?ref=github) · [Dịch vụ rà soát cho doanh nghiệp (không cần biết kỹ thuật)](https://khamweb.gonovn.me/?ref=github)

Bộ công cụ rà soát kỹ thuật website theo pháp luật Việt Nam: **đo bằng chứng cookie và tracking trên trình duyệt thật**, đối chiếu với checklist pháp lý, và **mẫu sửa lỗi** cho từng nền tảng. Dùng được như một AI skill (Claude Code, Antigravity…) hoặc chạy độc lập bằng Python.

> Đây là công cụ hỗ trợ rà soát, **không phải ý kiến pháp lý** và không cấp "chứng nhận tuân thủ". Xem [DISCLAIMER.md](DISCLAIMER.md).

## Dành cho ai

- Lập trình viên, agency làm website cho doanh nghiệp Việt Nam, muốn bàn giao website kèm bằng chứng đo cookie.
- Chủ website, marketer cần biết website có đang chạy tracking trước khi khách đồng ý không.
- Doanh nghiệp, lập trình viên nước ngoài làm website cho thị trường Việt Nam: có báo cáo tiếng Anh (`--lang en`) và [README tiếng Anh](README.en.md).

## Làm được gì

| Phần | Nội dung |
|---|---|
| Quét động [`scripts/dynamic_scan.py`](scripts/dynamic_scan.py) | Mở website bằng Chromium (Playwright), 3 phiên sạch ở desktop 1366: chưa chọn / bấm Từ chối / bấm Chấp nhận, thêm 1 phiên mobile 390. Ghi cookie và request theo dõi từng phiên (GA4, Google Ads, Meta, TikTok, YouTube nhúng…), nhận diện banner (Shopify, OneTrust, Cookiebot, CookieYes, Complianz, banner tự viết), kiểm kê form, trang chính sách, thông tin doanh nghiệp. Xuất `scan.json`, `scan.md`, ảnh chụp. |
| Quét tĩnh [`scripts/scan.sh`](scripts/scan.sh) | Quét mã nguồn (từ vn-law-check). |
| Checklist pháp lý [`references/law/`](references/law/) | Dữ liệu cá nhân, thương mại điện tử, an ninh mạng, người tiêu dùng, quảng cáo, giao dịch điện tử, AI, mức phạt. Giữ nguyên từ [vn-law-check](https://github.com/mhfed/vn-law-check). |
| Hướng dẫn theo nền tảng [`references/platforms/`](references/platforms/) | Shopify (rút từ dự án thật), WordPress/WooCommerce, Haravan/Sapo (chưa kiểm chứng trên dự án thật), website tự code. |
| Mẫu sửa lỗi [`templates/remediation/`](templates/remediation/) | Consent Mode v2 cho Shopify và web thường, video YouTube bấm-mới-tải, thông báo và ô đồng ý cho form, mục cookie trong chính sách bảo mật. |
| Quy trình | [Chuẩn bằng chứng](references/evidence-standard.md), [mẫu báo cáo](templates/report-template.md), [cổng kiểm tra go-live](references/build-checklist.md). |

Dữ liệu luật cập nhật đến **03/11/2026** (xem đầu [`legal-references.md`](references/law/legal-references.md)). Luật Việt Nam đang thay đổi nhanh: luôn kiểm tra lại văn bản còn hiệu lực tại [vbpl.vn](https://vbpl.vn) hoặc [thuvienphapluat.vn](https://thuvienphapluat.vn).

## Cài đặt

Cần Python 3.10+ và Git. Quét tĩnh (`scan.sh`) cần bash: có sẵn trên macOS/Linux, trên Windows dùng Git Bash hoặc WSL.

```bash
git clone https://github.com/gonostudy305/vn-law-guard.git
cd vn-law-guard
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Linux server/CI thiếu thư viện hệ thống thì dùng `python -m playwright install --with-deps chromium`.

## Sử dụng

### Quét một website

```bash
python scripts/dynamic_scan.py https://ten-mien.vn --out ./bao-cao
python scripts/dynamic_scan.py https://example.com --out ./report --lang en
```

| Tùy chọn | Ý nghĩa |
|---|---|
| `--out` | Thư mục kết quả (mặc định `vn-legal-audit`) |
| `--lang vi\|en` | Ngôn ngữ báo cáo `scan.md` và ghi chú tín hiệu (mặc định `vi`) |
| `--no-mobile` | Bỏ phiên mobile 390 |

Mỗi tín hiệu có mã cố định (ví dụ `TRACKING_COOKIE_BEFORE_CHOICE`) và mục checklist tương ứng (ví dụ `01-C`), để máy và người cùng đọc được. Cách đọc bằng chứng: [`references/evidence-standard.md`](references/evidence-standard.md).

Lưu ý khi đọc kết quả:
- Kết quả phụ thuộc **vị trí máy quét**: nhiều nền tảng chỉ hiện banner với IP thuộc vùng bắt buộc xin đồng ý. Muốn đo như khách Việt Nam thì chạy từ IP Việt Nam.
- Bộ quét mở trang chủ, một trang nội bộ và trang chính sách. Trang thanh toán, tài khoản cần kiểm tra thêm bằng tay.
- Ping Consent Mode khi khách đã từ chối (`gcs=G100`) không đặt cookie và không bị tính là tracking.

### Dùng như AI skill

Đặt repo vào thư mục skills của agent:

```bash
# Claude Code
git clone https://github.com/gonostudy305/vn-law-guard.git ~/.claude/skills/vn-law-guard
```

Antigravity: `~/.gemini/config/skills/vn-law-guard`. Theo dự án: `.agents/skills/vn-law-guard`. Sau đó yêu cầu agent, ví dụ: *"Audit website https://… theo luật Việt Nam"* hoặc *"Kiểm tra website trước khi go-live"*. Agent làm theo [`SKILL.md`](SKILL.md): quét → phân loại → đối chiếu checklist → báo cáo có bằng chứng → chỉ sửa code khi bạn đồng ý.

### Cập nhật dữ liệu luật từ vn-law-check

```bash
bash scripts/sync_upstream.sh          # xem thay đổi
bash scripts/sync_upstream.sh --apply  # chép sau khi đã xem
```

## Sử dụng có trách nhiệm

- Chỉ quét website của bạn, của khách hàng đã đồng ý, hoặc website bạn được phép kiểm tra. Bộ quét chỉ đọc trang công khai, không gửi form, không đăng nhập, không thanh toán, nhưng vẫn tạo lượt truy cập thật (khoảng 5 phiên trình duyệt mỗi lần chạy).
- Không công bố tên website bị phát hiện lỗi khi chưa được chủ website đồng ý.
- Kết luận cuối cùng về nghĩa vụ pháp lý, mức phạt thuộc về luật sư hoặc cơ quan có thẩm quyền.

## Phát triển

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Test dựng các trang thử trên `127.0.0.1`, không gọi ra Internet. Góp ý, sửa luật, thêm nền tảng: xem [CONTRIBUTING.md](CONTRIBUTING.md). Lỗi bảo mật: xem [SECURITY.md](SECURITY.md). Lịch sử thay đổi: [CHANGELOG.md](CHANGELOG.md).

## Ghi công

Toàn bộ checklist pháp lý trong `references/law/`, `examples/`, `scripts/scan.sh`, `scripts/fetch-site.sh` lấy từ [mhfed/vn-law-check](https://github.com/mhfed/vn-law-check) (MIT). Chi tiết: [NOTICE.md](NOTICE.md), [LICENSE.upstream](LICENSE.upstream).

## Giấy phép

[MIT](LICENSE).
