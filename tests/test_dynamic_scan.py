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


# --- Tín hiệu và báo cáo song ngữ (không cần trình duyệt) ---

from scripts.dynamic_scan import LANGS, MESSAGES, REPORT_TEXT, md_report, signals


def _phase(cookies=(), requests=(), banner=None, error=None):
    return {"tracking_cookies": list(cookies), "tracker_requests": list(requests), "banner": banner,
            "error": error, "clicked": None, "third_party_hosts": []}


def test_message_tables_have_same_keys():
    keys = [set(MESSAGES[l]) for l in LANGS]
    assert all(k == keys[0] for k in keys)
    texts = [set(REPORT_TEXT[l]) for l in LANGS]
    assert all(t == texts[0] for t in texts)


@pytest.mark.parametrize("lang", LANGS)
def test_signals_tracking_before_consent(lang):
    ga = {"vendor": "Google Analytics", "stage": "load", "gcs": None, "url": "https://www.google-analytics.com/g/collect"}
    phases = {"none": _phase(["_ga"], [ga]), "decline": _phase(["_ga"], [ga]), "accept": _phase(["_ga"], [ga])}
    inv = {"forms": [], "policy_links": {"privacy": [{"h": "/p", "t": "Privacy"}]}, "privacy_pages": []}
    codes = {s["code"] for s in signals(phases, inv, lang)}
    assert {"TRACKING_COOKIE_BEFORE_CHOICE", "TRACKER_REQUEST_BEFORE_CHOICE", "TRACKING_AFTER_DECLINE",
            "NO_BANNER_BUT_TRACKERS"} <= codes


def test_denied_consent_mode_ping_is_not_tracking():
    ping = {"vendor": "Google Analytics", "stage": "load", "gcs": "G100", "url": "https://www.google-analytics.com/g/collect?gcs=G100"}
    banner = {"cmp": "X", "has_decline": True}
    phases = {"none": _phase([], [ping], banner), "decline": _phase([], [ping], banner),
              "accept": _phase(["_ga"], [], banner)}
    inv = {"forms": [], "policy_links": {"privacy": [{"h": "/p", "t": "p"}]}, "privacy_pages": []}
    assert signals(phases, inv) == []


def test_english_report_has_no_vietnamese_headings():
    data = {"url": "https://example.vn", "lang": "en", "scanned_at": "2026-11-09T00:00:00+07:00",
            "phases": {"none": _phase()}, "screenshots": [], "signals": [],
            "inventory": {"platform": ["Shopify"], "policy_links": {}, "forms": [], "privacy_pages": []}}
    md = md_report(data)
    assert "Dynamic scan" in md and "No automatic signals" in md
    assert "Quét động" not in md


def test_invalid_lang_rejected(tmp_path):
    with pytest.raises(ValueError):
        scan_site("http://127.0.0.1:9", out_dir=str(tmp_path), lang="fr")


# --- Trang vi phạm: đặt cookie theo dõi ngay khi tải, không có banner ---

class BadSiteHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("""<!doctype html><html><head><title>Bad</title>
<script>document.cookie = "_ga=GA1.1.123.456; path=/";</script></head>
<body><form action="/contact"><input type="email" name="email"><button>Send</button></form>
<a href="/about">About</a></body></html>""".encode("utf-8"))

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def bad_server():
    server = socketserver.TCPServer(("127.0.0.1", 0), BadSiteHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_dynamic_scan_flags_cookie_before_consent(bad_server, tmp_path):
    data = scan_site(bad_server, out_dir=str(tmp_path), with_mobile=False, lang="en")
    codes = {s["code"] for s in data["signals"]}
    assert "_ga" in data["phases"]["none"]["tracking_cookies"]
    assert {"TRACKING_COOKIE_BEFORE_CHOICE", "FORM_NO_NOTICE", "NO_PRIVACY_LINK"} <= codes
    assert "Dynamic scan" in (tmp_path / "scan.md").read_text(encoding="utf-8")
