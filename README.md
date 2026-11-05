# VN Law Guard

> **Công cụ hỗ trợ rà soát kỹ thuật tuân thủ pháp luật Việt Nam cho Website & E-commerce**  
> Đo lường bằng chứng cookie & tracker trên trình duyệt thật — Giúp kỹ sư và chủ website rà soát lỗ hổng kỹ thuật trong một buổi làm việc.

---

## 🌟 Giới Thiệu & Điểm Khác Biệt

**VN Law Guard** được xây dựng nhằm giải quyết bài toán tuân thủ pháp luật thực tế của các website và nền tảng thương mại điện tử hoạt động tại Việt Nam: bảo vệ dữ liệu cá nhân (Luật 91/2025, NĐ 356/2025, NĐ 330/2026), thương mại điện tử (Luật 122/2025, NĐ 248/2026), bảo vệ quyền lợi người tiêu dùng, an ninh mạng và quảng cáo trực tuyến.

### 3 Năng Lực Kỹ Thuật Mở Rộng:

1. **Quét động bằng trình duyệt thật (`scripts/dynamic_scan.py`):**
   - Mở website bằng Chromium không giao diện (Playwright), mỗi phiên là một trình duyệt sạch.
   - Desktop 1366px chạy **3 phiên** (chưa chọn / bấm Từ chối / bấm Chấp nhận); mobile 390px chạy thêm 1 phiên chưa chọn để chụp và đo banner.
   - Ghi lại request gửi tới dịch vụ theo dõi (Google Analytics 4, Google Ads, Meta Pixel, TikTok Pixel, YouTube nhúng...) và cookie theo dõi ở từng phiên.
   - Tách riêng ping Consent Mode khi khách đã từ chối (`gcs=G100`, không đặt cookie) để không chấm nhầm thành tracking.
   - Kết quả là dấu hiệu kèm bằng chứng, phụ thuộc vị trí máy quét; không phải kết luận pháp lý.
2. **Hướng dẫn rà soát theo từng nền tảng (`references/platforms/`):**
   - Hướng dẫn chuyên sâu cho: **Shopify**, **WordPress / WooCommerce**, **Haravan / Sapo**, và **Custom Code (Next.js, PHP, Node)**.
   - Chỉ rõ vị trí cấu hình trong Admin và các file template cần điều chỉnh. Module Shopify rút từ dự án thật; module Haravan/Sapo chưa kiểm chứng trên dự án thật.
3. **Kho giải pháp vá lỗi thực tế (`templates/remediation/`):**
   - Cổng Google Consent Mode v2 kết hợp Shopify Customer Privacy API (`shopify-consent-mode.liquid`).
   - Mẫu nhúng video YouTube bấm-mới-tải (`youtube-facade.html`) triệt tiêu cookie bên thứ ba khi khách chưa đồng ý.
   - Mẫu ô đồng ý và điều khoản xử lý dữ liệu cho form liên hệ / báo giá (`form-consent.html`).

---

## 🤝 Ghi Công Nguồn Gốc (Acknowledgments & Upstream)

Dự án này trân trọng ghi nhận và kế thừa toàn bộ cơ sở tri thức pháp lý mở từ:
- **Dự án gốc:** [vn-law-check](https://github.com/mhfed/vn-law-check) của tác giả `mhfed` (Giấy phép MIT, xem `LICENSE.upstream` và `NOTICE.md`).
- Toàn bộ 11 tài liệu checklist luật trong thư mục `references/law/` được duy trì nguyên vẹn và liên tục cập nhật theo upstream bằng lệnh `bash scripts/sync_upstream.sh`.

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh

### 1. Cài đặt môi trường
Yêu cầu Python 3.10+ và Playwright:
```bash
pip install playwright
python -m playwright install chromium
```

### 2. Quét động một website đang chạy (URL công khai)
```bash
python scripts/dynamic_scan.py https://ten-website.vn --out ./bao-cao-kiem-toan
```
*Kết quả xuất ra gồm: tệp dữ liệu chi tiết `scan.json`, báo cáo tổng hợp `scan.md` và ảnh chụp màn hình bằng chứng thực tế tại từng trạng thái.*

### Chạy test
```bash
pip install pytest
python -m pytest tests -v
```
Test quét động dựng một trang thử trên `127.0.0.1`, không gọi ra Internet.

### 3. Quét tĩnh mã nguồn dự án (khi có source code)
```bash
bash scripts/scan.sh /duong-dan-toi-source-code
```

### 4. Tích hợp làm AI Skill cho Coding Agent
Skill viết theo định dạng `SKILL.md` chung, dùng được với các agent đọc định dạng này (Claude Code, Google Antigravity...):
- Clone repo rồi đặt (hoặc tạo liên kết) vào thư mục skills của agent, ví dụ `~/.claude/skills/vn-law-guard` (Claude Code), `.agents/skills/vn-law-guard` (theo dự án) hoặc `~/.gemini/config/skills/vn-law-guard`.
  ```bash
  git clone https://github.com/gonostudy305/vn-law-guard.git ~/.claude/skills/vn-law-guard
  ```
- Gọi lệnh trong chat: `/vn-law-guard` hoặc yêu cầu: *"Audit kỹ thuật website này theo luật Việt Nam"*.

---

## 📁 Cấu Trúc Thư Mục

```
vn-law-guard/
├── references/
│   ├── law/                       # Cơ sở tri thức pháp luật gốc (sync từ vn-law-check)
│   │   ├── 00-triage.md           # Phân loại độ phức tạp website
│   │   ├── 01-personal-data-protection.md
│   │   ├── 02-ecommerce.md
│   │   ├── 08-penalties-reference.md
│   │   └── legal-references.md
│   ├── platforms/                 # Hướng dẫn chi tiết theo nền tảng CMS/E-commerce
│   │   ├── shopify.md
│   │   ├── wordpress-woocommerce.md
│   │   ├── haravan-sapo.md
│   │   └── custom-code.md
│   ├── build-checklist.md         # Bảng kiểm soát trước khi Go-live website mới
│   └── evidence-standard.md       # Tiêu chuẩn bằng chứng kỹ thuật hợp lệ
├── scripts/
│   ├── dynamic_scan.py            # Engine quét động không đầu (Playwright)
│   ├── scan.sh                    # Quét tĩnh mã nguồn (bash)
│   ├── fetch-site.sh              # Tải HTML tĩnh hỗ trợ quét
│   └── sync_upstream.sh           # Script đồng bộ bộ luật từ upstream vn-law-check
├── templates/
│   ├── remediation/               # Kho mẫu vá lỗi (Shopify, YouTube Facade, Form)
│   │   ├── shopify-consent-mode.liquid
│   │   ├── shopify-cookie-settings-link.liquid
│   │   ├── shopify-cookie-banner-style.liquid
│   │   ├── generic-consent-mode.html
│   │   ├── youtube-facade.html
│   │   └── form-consent.html
│   └── report-template.md         # Mẫu báo cáo kiểm toán có đối chiếu bằng chứng
├── examples/                      # Báo cáo mẫu và khung chính sách bảo mật
├── DISCLAIMER.md                  # Tuyên bố miễn trừ trách nhiệm pháp lý
├── NOTICE.md                      # Chi tiết ghi công tác giả gốc
├── LICENSE                        # Giấy phép MIT
├── SKILL.md                       # Định nghĩa kỹ năng cho AI Coding Agents
└── README.md
```

---

## ⚖️ Tuyên Bố Miễn Trừ Trách Nhiệm (Legal Disclaimer)

- **VN Law Guard** là công cụ hỗ trợ kỹ thuật nhằm phát hiện các dấu hiệu rủi ro và thu thập bằng chứng đo đạc thực tế trên trình duyệt. Công cụ này **không đưa ra kết luận pháp lý chính thức**, không cấu thành dịch vụ tư vấn pháp luật và không thay thế ý kiến chuyên môn của Luật sư hoặc cơ quan quản lý nhà nước.
- Dự án không cam kết bất kỳ chứng nhận "an toàn 100%" hay "chống phạt". Người vận hành website chịu trách nhiệm cuối cùng về việc rà soát và quyết định áp dụng các biện pháp tuân thủ.
- Chi tiết xem tại [DISCLAIMER.md](DISCLAIMER.md).

---

## 📄 Giấy Phép (License)
Dự án được phát hành theo giấy phép mã nguồn mở [MIT License](LICENSE).
