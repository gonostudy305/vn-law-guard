# Ghi công và nguồn gốc

- Thư mục `references/law/`, `examples/`, `scripts/scan.sh`, `scripts/fetch-site.sh` và `DISCLAIMER.md` lấy từ **vn-law-check** (https://github.com/mhfed/vn-law-check), giấy phép MIT, xem `LICENSE.upstream`.
- Chỉnh sửa duy nhất trên các file đó: đổi đường dẫn nội bộ sang bố cục mới (`references/law/...`).
- Bản lấy về: thư mục vn-law-check cục bộ ngày 06/11/2026; dữ liệu luật ghi "Cập nhật: 03/11/2026".
- Phần thêm mới (SKILL.md, `references/platforms/`, `references/build-checklist.md`, `references/evidence-standard.md`, `scripts/dynamic_scan.py`, `scripts/sync_upstream.sh`, `templates/`) do Contributors to vn-law-guard phát triển, phát hành theo MIT.
- Trang giới thiệu `site/` (https://gonovn.me/vn-law-guard/): HTML/CSS tĩnh dựng lại từ thiết kế của người duy trì. `site/assets/styles.css` là bản build Tailwind CSS (MIT); biểu tượng SVG từ Lucide (ISC); font Plus Jakarta Sans và JetBrains Mono tự host trong `site/assets/fonts/` (SIL Open Font License 1.1). Trang không dùng analytics, cookie hay request bên thứ ba.
