import http.server
import json
import re
import socketserver
import threading
from pathlib import Path
import pytest

from scripts.dynamic_scan import (
    TRACKERS,
    TRACKING_COOKIES,
    EXPIRED_REFS,
    POLICY_RED_FLAGS,
    LINK_KINDS,
    scan_site,
)


def test_tracker_signatures():
    # GA4 collect
    assert re.search(TRACKERS["Google Analytics"], "https://analytics.google.com/g/collect?v=2&tid=G-XXXXX")
    # Meta Pixel
    assert re.search(TRACKERS["Meta Pixel"], "https://connect.facebook.net/en_US/fbevents.js")
    assert re.search(TRACKERS["Meta Pixel"], "https://www.facebook.com/tr/?id=123456&ev=PageView")
    # TikTok Pixel
    assert re.search(TRACKERS["TikTok Pixel"], "https://analytics.tiktok.com/i18n/pixel/events.js")
    # YouTube Embed
    assert re.search(TRACKERS["YouTube embed"], "https://www.youtube.com/embed/dQw4w9WgXcQ")


def test_tracking_cookies():
    assert re.search(TRACKING_COOKIES, "_ga")
    assert re.search(TRACKING_COOKIES, "_fbp")
    assert re.search(TRACKING_COOKIES, "_ttp")
    assert re.search(TRACKING_COOKIES, "VISITOR_INFO1_LIVE")
    assert not re.search(TRACKING_COOKIES, "session_id")
    assert not re.search(TRACKING_COOKIES, "cart_token")


def test_expired_references_detection():
    sample_text = "Website hoạt động theo Nghị định 13/2023/NĐ-CP và Nghị định 85/2021/NĐ-CP."
    found = [pattern for pattern in EXPIRED_REFS if re.search(pattern, sample_text)]
    assert r"13/2023/NĐ-CP" in found
    assert r"85/2021/NĐ-CP" in found


def test_policy_red_flags():
    bad_policy = "Bằng việc tiếp tục sử dụng website này, quý khách mặc nhiên đồng ý với chính sách của chúng tôi."
    assert re.search(POLICY_RED_FLAGS["continue_means_consent"], bad_policy)


class MockWebHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Mock Test Site</title>
</head>
<body>
    <h1>Chào mừng đến với trang thử nghiệm tuân thủ</h1>
    <div id="shopify-pc__banner">
        <p>Chúng tôi sử dụng cookie để phân tích lưu lượng.</p>
        <button id="shopify-pc__banner__btn-accept">Chấp nhận</button>
        <button id="shopify-pc__banner__btn-decline">Từ chối</button>
    </div>
    <form action="/contact" method="POST">
        <input type="text" name="name" placeholder="Họ tên" />
        <input type="email" name="email" placeholder="Email" />
        <button type="submit">Gửi liên hệ</button>
    </form>
    <footer>
        <a href="/chinh-sach-bao-mat">Chính sách bảo mật</a>
        <p>Công ty TNHH Thử Nghiệm - MST: 0123456789</p>
    </footer>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Tắt log để giữ output pytest sạch sẽ


@pytest.fixture(scope="module")
def local_server():
    server = socketserver.TCPServer(("127.0.0.1", 0), MockWebHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_dynamic_scan_on_mock_site(local_server, tmp_path):
    out_dir = tmp_path / "scan_out"
    report = scan_site(local_server, out_dir=str(out_dir), with_mobile=False)

    assert report is not None
    assert (out_dir / "scan.json").exists()
    assert (out_dir / "scan.md").exists()

    data = json.loads((out_dir / "scan.json").read_text(encoding="utf-8"))
    assert data["url"].startswith("http://127.0.0.1")
    assert len(data.get("inventory", {}).get("forms", [])) >= 1
    assert data.get("phases", {}).get("none", {}).get("banner", {}).get("cmp") == "Shopify Customer Privacy"
