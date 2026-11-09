# Changelog

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/), phiên bản theo [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Trang giới thiệu tĩnh `site/`, xuất bản tại https://gonovn.me/vn-law-guard/ qua GitHub Pages (workflow `pages.yml`). Không cookie, không analytics, font tự host.

## [0.2.0] - 2026-11-09

### Added
- `dynamic_scan.py --lang en`: báo cáo và ghi chú tín hiệu bằng tiếng Anh. Mã tín hiệu giữ nguyên.
- `README.en.md` cho người dùng nước ngoài; README tiếng Việt viết lại.
- Test không cần Internet: tín hiệu song ngữ, ping Consent Mode bị từ chối, trang đặt cookie trước khi đồng ý.
- CI GitHub Actions (Ubuntu + Windows, Python 3.10 và 3.13).
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `.gitattributes`.
- CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, mẫu issue và pull request.

### Changed
- Kiểm kê trang chủ lỗi không còn làm dừng cả lần quét; các phiên đồng ý vẫn chạy.
- Mã kỹ thuật `ACCEPT_DOES_NOT_ENABLE` dùng nhãn checklist `technical` thay cho `kỹ thuật`.

## [0.1.0] - 2026-11-06

### Added
- Phát hành đầu: quét động Playwright 3 phiên đồng ý, hướng dẫn Shopify / WordPress-WooCommerce / Haravan-Sapo / tự code, mẫu sửa lỗi, chuẩn bằng chứng, mẫu báo cáo, cổng go-live.
- Lõi checklist pháp lý từ mhfed/vn-law-check (MIT), dữ liệu luật cập nhật 03/11/2026.
