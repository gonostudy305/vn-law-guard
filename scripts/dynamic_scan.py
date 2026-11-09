#!/usr/bin/env python3
"""Quét động một website bằng trình duyệt thật để lấy bằng chứng cho audit pháp lý VN.

    python scripts/dynamic_scan.py https://ten-mien.vn --out ./vn-legal-audit [--lang en]

EN: Scans a live website in a real browser (3 clean sessions: no choice / Decline / Accept)
and records tracking requests and cookies per session, plus a homepage inventory, as evidence
for a Vietnamese legal-compliance review. Read-only; signals, not legal conclusions.
Use --lang en for an English report.

Chỉ quét website của bạn hoặc website bạn được phép kiểm tra.

Chạy 3 phiên trình duyệt sạch, mỗi phiên: mở trang chủ -> (thao tác) -> mở thêm 1 trang nội bộ.
  none     không bấm gì trên banner cookie (người dùng phớt lờ banner)
  decline  bấm Từ chối
  accept   bấm Chấp nhận
Ghi lại request tới các dịch vụ theo dõi và cookie theo dõi ở từng phiên, kèm kiểm kê trang
(banner, form, link chính sách, thông tin doanh nghiệp, bên thứ ba, nền tảng) và ảnh chụp
desktop 1366 / mobile 390.

Chỉ đọc trang công khai: không gửi form, không đăng nhập, không bấm thanh toán.
Kết quả là DẤU HIỆU kèm bằng chứng, không phải kết luận pháp lý. Kết quả phụ thuộc vị trí
máy quét (banner của nhiều nền tảng chỉ hiện với IP thuộc vùng bắt buộc xin đồng ý).

Cần: pip install playwright && python -m playwright install chromium
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

VN_TZ = timezone(timedelta(hours=7))

# Dịch vụ theo dõi: tên -> regex trên URL request
TRACKERS = {
    "Google Analytics": r"google-analytics\.com/(g/)?collect|analytics\.google\.com/g/collect|/g/collect\?",
    "Google Tag (loader)": r"googletagmanager\.com/(gtag/js|gtm\.js)",
    "Google Ads / DoubleClick": r"googleadservices\.com|doubleclick\.net|google\.com/pagead|googlesyndication\.com|google\.com/ccm/collect",
    "Meta Pixel": r"connect\.facebook\.net|facebook\.com/tr[/?]",
    "TikTok Pixel": r"analytics\.tiktok\.com",
    "Microsoft Clarity / Bing UET": r"clarity\.ms|bat\.bing\.com",
    "Hotjar": r"hotjar\.com|hotjar\.io",
    "LinkedIn Insight": r"snap\.licdn\.com|px\.ads\.linkedin\.com",
    "X/Twitter Ads": r"static\.ads-twitter\.com|analytics\.twitter\.com",
    "Criteo": r"criteo\.(com|net)",
    "Yandex Metrica": r"mc\.yandex\.",
    "YouTube embed": r"youtube\.com/(embed|youtubei|api/stats|s/player)",
    "Google Maps embed": r"google\.com/maps/(embed|vt)|maps\.googleapis\.com",
    "Zalo (pixel/widget)": r"zalo\.me|zaloapp\.com|zadn\.vn",
    "Shopify analytics": r"monorail-edge\.shopifysvc\.com|/api/collect|/\.well-known/shopify/monorail",
}
NON_DECISIVE = {"Google Tag (loader)", "Shopify analytics", "Zalo (pixel/widget)"}
# Cookie theo dõi (phân tích/quảng cáo). Cookie không khớp được coi là chưa phân loại.
TRACKING_COOKIES = r"^(_ga|_gid|_gat|_gcl_|_fbp|_fbc|_ttp|_tt_|_clck|_clsk|_hj|_uet|_uetsid|_uetvid|IDE|test_cookie|_pin_unauth|_shopify_y|_shopify_s|_shopify_sa_|_shopify_analytics|_shopify_marketing|__zi|zpsid|YSC|VISITOR_INFO1_LIVE|VISITOR_PRIVACY_METADATA|__Secure-YNID|__Secure-ROLLOUT_TOKEN|__Secure-YEC|NID)"

# Banner cookie phổ biến: (tên, selector banner, nút chấp nhận, nút từ chối, nút tùy chọn)
CMPS = [
    ("Shopify Customer Privacy", "#shopify-pc__banner", "#shopify-pc__banner__btn-accept",
     "#shopify-pc__banner__btn-decline", "#shopify-pc__banner__btn-manage-prefs"),
    ("OneTrust", "#onetrust-banner-sdk", "#onetrust-accept-btn-handler", "#onetrust-reject-all-handler",
     "#onetrust-pc-btn-handler"),
    ("Cookiebot", "#CybotCookiebotDialog", "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
     "#CybotCookiebotDialogBodyButtonDecline", "#CybotCookiebotDialogBodyLevelButtonCustomize"),
    ("CookieYes", ".cky-consent-container", ".cky-btn-accept", ".cky-btn-reject", ".cky-btn-customize"),
    ("Complianz", ".cmplz-cookiebanner", ".cmplz-accept", ".cmplz-deny", ".cmplz-view-preferences"),
]
ACCEPT_TEXT = r"^(chấp nhận|đồng ý|tôi đồng ý|chấp nhận tất cả|accept|accept all|allow all|allow|ok|got it)\b"
DECLINE_TEXT = r"^(từ chối|không đồng ý|từ chối tất cả|chỉ cookie cần thiết|chỉ dùng cookie cần thiết|reject|reject all|decline|deny|necessary only|only necessary)\b"

LINK_KINDS = {
    "privacy": r"bảo mật|quyền riêng tư|dữ liệu cá nhân|privacy",
    "terms": r"điều khoản|quy chế|terms",
    "return": r"đổi trả|hoàn tiền|refund|return",
    "shipping": r"vận chuyển|giao hàng|giao nhận|shipping",
    "payment": r"thanh toán|payment",
    "complaint": r"khiếu nại|complaint",
    "contact": r"liên hệ|contact",
}
EXPIRED_REFS = [r"13/2023/NĐ-CP", r"52/2013/NĐ-CP", r"85/2021/NĐ-CP", r"47/2014/TT-BCT"]
POLICY_RED_FLAGS = {
    "continue_means_consent": r"tiếp tục (sử dụng|truy cập)[^.]{0,80}(đồng ý|chấp nhận)|by continuing to (use|browse)",
    "no_third_party_claim": r"không (cung cấp|chia sẻ|tiết lộ)[^.]{0,40}(bên thứ (ba|3))",
}
PLATFORMS = [
    ("Shopify", r"cdn\.shopify\.com|Shopify\.theme|myshopify\.com"),
    ("WooCommerce", r"woocommerce|wc-ajax"),
    ("WordPress", r"wp-content|wp-includes|wp-json"),
    ("Haravan", r"haravan|hstatic\.net"),
    ("Sapo", r"bizweb|sapo\.vn|dktcdn\.net"),
    ("Wix", r"wixstatic\.com|static\.parastorage\.com"),
    ("Webflow", r"webflow\.(com|io)"),
    ("Next.js", r"__NEXT_DATA__|/_next/static"),
    ("Nuxt", r"__NUXT__|/_nuxt/"),
]
ECOM_SIGNS = r"thêm vào giỏ|mua ngay|giỏ hàng|add to cart|/cart\b|/checkout"


def classify(url):
    for name, rx in TRACKERS.items():
        if re.search(rx, url, re.I):
            return name
    return None


def gcs_of(url):
    q = parse_qs(urlparse(url).query)
    return (q.get("gcs") or [None])[0]


def same_origin_page(page, base):
    host = urlparse(base).netloc
    hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    skip = re.compile(r"cart|checkout|account|login|register|policy|policies|chinh-sach|\.(jpg|png|webp|pdf)$", re.I)
    for h in hrefs:
        p = urlparse(h)
        if p.netloc == host and p.path not in ("", "/") and not p.fragment and not skip.search(p.path):
            return h.split("#")[0]
    return None


def find_banner(page, wait_ms=6000):
    """Trả về (tên CMP, locator banner, nút accept, nút decline, nút prefs) hoặc banner chung."""
    deadline = wait_ms
    step = 500
    while deadline > 0:
        for name, sel, acc, dec, pref in CMPS:
            loc = page.locator(sel)
            if loc.count() and loc.first.is_visible():
                return {"cmp": name, "banner": sel, "accept": acc, "decline": dec, "prefs": pref}
        generic = page.evaluate(
            """([accRx, decRx]) => {
                const acc = new RegExp(accRx, 'i'), dec = new RegExp(decRx, 'i');
                const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
                const inCookieBox = e => { let n = e; for (let i = 0; i < 7 && n; i++, n = n.parentElement) {
                    if (/cookie/i.test(n.innerText || '') && (n.innerText || '').length < 2500) return true; } return false; };
                const els = [...document.querySelectorAll('button, a, [role=button]')].filter(e => vis(e) && inCookieBox(e));
                const mark = (e, k) => { e.setAttribute('data-vnlegal', k); return true; };
                let a = els.find(e => acc.test((e.innerText || '').trim()));
                let d = els.find(e => dec.test((e.innerText || '').trim()));
                if (a) mark(a, 'accept'); if (d) mark(d, 'decline');
                return {accept: !!a, decline: !!d};
            }""", [ACCEPT_TEXT, DECLINE_TEXT])
        if generic["accept"] or generic["decline"]:
            return {"cmp": "Không rõ (nhận theo chữ trên nút)", "banner": None,
                    "accept": '[data-vnlegal="accept"]' if generic["accept"] else None,
                    "decline": '[data-vnlegal="decline"]' if generic["decline"] else None, "prefs": None}
        page.wait_for_timeout(step)
        deadline -= step
    return None


def visible(page, sel):
    if not sel:
        return False
    loc = page.locator(sel)
    return bool(loc.count()) and loc.first.is_visible()


def run_phase(browser, url, action, viewport, out_dir, shot_name):
    ctx = browser.new_context(viewport=viewport, locale="vi-VN", timezone_id="Asia/Ho_Chi_Minh",
                              is_mobile=viewport["width"] < 768, has_touch=viewport["width"] < 768)
    reqs = []
    stage = ["load"]
    ctx.on("request", lambda r: reqs.append({"url": r.url, "stage": stage[0]}))
    page = ctx.new_page()
    result = {"action": action, "viewport": viewport["width"], "clicked": None, "error": None}
    try:
        page.goto(url, wait_until="load", timeout=45000)
        page.wait_for_timeout(2500)
        banner = find_banner(page)
        result["banner"] = None
        if banner:
            info = dict(banner)
            info["has_decline"] = visible(page, banner["decline"])
            info["has_prefs"] = visible(page, banner["prefs"])
            if banner["banner"] and visible(page, banner["banner"]):
                box = page.locator(banner["banner"]).first.bounding_box()
                if box:
                    info["box"] = {k: round(v) for k, v in box.items()}
                    info["viewport_height_pct"] = round(100 * box["height"] / viewport["height"])
            result["banner"] = info
        if shot_name:
            page.screenshot(path=str(out_dir / shot_name))
        stage[0] = "after_action"
        if action in ("accept", "decline"):
            sel = banner and banner.get(action)
            if sel and visible(page, sel):
                page.locator(sel).first.click(timeout=5000)
                result["clicked"] = sel
                page.wait_for_timeout(3000)
            else:
                result["error"] = f"Không tìm thấy nút {action} trên banner"
        else:
            page.wait_for_timeout(3000)
        result["consent_mode"] = page.evaluate(
            """() => (window.dataLayer || []).filter(x => x && x[0] === 'consent')
                     .map(x => ({type: x[1], state: x[2]}))""")
        nxt = same_origin_page(page, url)
        result["second_page"] = nxt
        if nxt:
            stage[0] = "second_page"
            page.goto(nxt, wait_until="load", timeout=45000)
            page.wait_for_timeout(4000)
        result["banner_after"] = visible(page, banner["banner"]) if banner and banner.get("banner") else None
    except Exception as e:  # ghi lại lỗi của phiên này, vẫn chạy các phiên khác
        result["error"] = f"{type(e).__name__}: {e}"
    cookies = ctx.cookies()
    result["tracking_cookies"] = sorted({c["name"] for c in cookies if re.match(TRACKING_COOKIES, c["name"])})
    result["other_cookies"] = sorted({c["name"] for c in cookies if not re.match(TRACKING_COOKIES, c["name"])})
    hits = []
    for r in reqs:
        name = classify(r["url"])
        if name:
            hits.append({"vendor": name, "stage": r["stage"], "gcs": gcs_of(r["url"]), "url": r["url"][:300]})
    result["tracker_requests"] = hits
    result["third_party_hosts"] = sorted({urlparse(r["url"]).netloc for r in reqs
                                          if urlparse(r["url"]).netloc
                                          and urlparse(r["url"]).netloc.split(":")[0] != urlparse(url).netloc})
    ctx.close()
    return result


def inventory(browser, url):
    ctx = browser.new_context(viewport={"width": 1366, "height": 900}, locale="vi-VN")
    page = ctx.new_page()
    inv = {}
    page.goto(url, wait_until="load", timeout=45000)
    page.wait_for_timeout(2500)
    html = page.content()
    text = page.inner_text("body")
    inv["platform"] = [n for n, rx in PLATFORMS if re.search(rx, html, re.I)] or ["Không nhận ra"]
    inv["ecommerce_signals"] = sorted(set(m.lower() for m in re.findall(ECOM_SIGNS, html, re.I)))[:10]
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => ({t: (e.innerText||'').trim().slice(0,80), h: e.href}))")
    found = {}
    for kind, rx in LINK_KINDS.items():
        # Chỉ xét link chữ ngắn (link menu/footer), tránh bắt nhầm tiêu đề bài viết
        hit = [l for l in links if len(l["t"]) <= 40
               and (re.search(rx, l["t"], re.I) or re.search(rx.replace(" ", "-"), urlparse(l["h"]).path, re.I))]
        uniq = []
        for l in hit:
            if l["h"] not in [u["h"] for u in uniq]:
                uniq.append(l)
        found[kind] = uniq[:3]
    inv["policy_links"] = found
    inv["bct_link"] = [l["h"] for l in links if "online.gov.vn" in l["h"]][:2]
    inv["business_info"] = {
        "tax_or_registration": re.findall(r"(?:mã số thuế|MST|mã số doanh nghiệp|GPKD|giấy chứng nhận đăng ký[^:]{0,40})\s*[:：]?\s*([0-9][0-9 .\-]{8,16})", text, re.I)[:3],
        "phones": sorted(set(m.replace(" ", "").replace(".", "") for m in re.findall(r"(?:\+84|0)[0-9 .]{8,12}[0-9]", text)))[:6],
        "emails": sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)))[:5],
        "has_address": bool(re.search(r"địa chỉ|address|phường|quận|thành phố|tp\.? ?hồ chí minh|hà nội", text, re.I)),
    }
    inv["forms"] = page.evaluate(r"""() => [...document.querySelectorAll('form')].map(f => {
        const inputs = [...f.querySelectorAll('input, textarea, select')].filter(i => i.type !== 'hidden');
        const boxes = inputs.filter(i => i.type === 'checkbox');
        const t = (f.innerText || '').replace(/\s+/g, ' ');
        return {
          action: f.getAttribute('action') || '', method: (f.method || '').toLowerCase(),
          fields: inputs.map(i => i.type + ':' + (i.name || i.id || '')).slice(0, 15),
          collects_personal: inputs.some(i => /email|tel/.test(i.type) || /name|ten|phone|sdt|dien.?thoai|email|address|dia.?chi/i.test(i.name || i.id || '')),
          checkboxes: boxes.map(b => ({name: b.name || b.id, prechecked: b.defaultChecked || b.checked})),
          mentions_policy: /chính sách|bảo mật|quyền riêng tư|dữ liệu cá nhân|privacy/i.test(t),
          visible: f.getBoundingClientRect().height > 0,
        };
    })""")
    inv["iframes"] = page.eval_on_selector_all("iframe[src]", "els => els.map(e => e.src.slice(0, 160))")[:15]
    # Đọc trang chính sách bảo mật nếu có
    inv["privacy_pages"] = []
    for link in (found.get("privacy") or [])[:2]:
        try:
            resp = page.goto(link["h"], wait_until="load", timeout=45000)
            if resp and resp.status >= 400:
                inv["privacy_pages"].append({"url": link["h"], "error": f"HTTP {resp.status}"})
                continue
            page.wait_for_timeout(1500)
            # Chỉ đọc phần nội dung chính: bỏ banner cookie, header, footer để không bắt nhầm chữ "cookie" của banner
            ptext = page.evaluate("""() => {
                const root = (document.querySelector('main, article, #MainContent, .main-content') || document.body).cloneNode(true);
                root.querySelectorAll('header, footer, nav, script, style, #shopify-pc__banner, [id*="cookie" i], [class*="cookie" i]')
                    .forEach(e => e.remove());
                return root.innerText || '';
            }""")
            inv["privacy_pages"].append({
                "url": link["h"],
                "length": len(ptext),
                "expired_refs": [r for r in EXPIRED_REFS if re.search(r, ptext)],
                "cites_current": [r for r in ["91/2025/QH15", "356/2025/NĐ-CP"] if r in ptext],
                "mentions_cookie": bool(re.search(r"cookie", ptext, re.I)),
                "red_flags": {k: (m.group(0)[:160] if (m := re.search(rx, ptext, re.I)) else None)
                              for k, rx in POLICY_RED_FLAGS.items()},
            })
        except Exception as e:
            inv["privacy_pages"].append({"url": link["h"], "error": str(e)})
    ctx.close()
    return inv

# Thông điệp tín hiệu theo ngôn ngữ báo cáo. Mã (code) giữ cố định để máy đọc; chỉ chữ thay đổi.
MESSAGES = {
    "vi": {
        "TRACKING_COOKIE_BEFORE_CHOICE": "Cookie theo dõi có khi chưa chọn gì: {cookies}",
        "TRACKER_REQUEST_BEFORE_CHOICE": "{n} request theo dõi khi chưa chọn (đã loại ping Consent Mode bị từ chối)",
        "TRACKING_AFTER_DECLINE": "Sau khi bấm Từ chối vẫn có cookie [{cookies}] / {n} request theo dõi",
        "NO_BANNER_BUT_TRACKERS": "Có dịch vụ theo dõi nhưng không thấy banner cookie (kiểm tra lại: banner có thể chỉ hiện theo vùng)",
        "NO_DECLINE_BUTTON": "Banner không có nút Từ chối ngang hàng với Chấp nhận",
        "ACCEPT_DOES_NOT_ENABLE": "Bấm Chấp nhận nhưng không thấy cookie theo dõi: đo lường có thể đã hỏng",
        "EMBED_BEFORE_CONSENT": "{embeds} nạp trước khi đồng ý (trang: {pages}). Dùng youtube-nocookie.com hoặc ảnh thay thế bấm-để-tải",
        "PRECHECKED_CONSENT": "Form {form} có ô tích sẵn",
        "FORM_NO_NOTICE": "Form {form} thu thông tin cá nhân nhưng không nhắc chính sách/mục đích",
        "NO_PRIVACY_LINK": "Không thấy link chính sách bảo mật trên trang chủ",
        "PRIVACY_PAGE_ERROR": "Link chính sách bảo mật {url} không mở được: {error}",
        "POLICY_CITES_EXPIRED_LAW": "{url} dẫn văn bản đã hết hiệu lực: {refs}",
        "POLICY_NO_COOKIE_SECTION": "{url} không nhắc cookie dù site có dịch vụ theo dõi",
        "CONTINUE_MEANS_CONSENT": "{url} coi việc tiếp tục sử dụng là đồng ý: \"{quote}\"",
        "THIRD_PARTY_CLAIM_MISMATCH": "{url} nói không chia sẻ bên thứ ba nhưng site gửi dữ liệu cho dịch vụ bên ngoài: \"{quote}\"",
        "MULTIPLE_PRIVACY_PAGES": "Có nhiều trang chính sách bảo mật: {urls}. Kiểm tra nội dung có mâu thuẫn không",
        "ECOM_NO_LINK": "Có dấu hiệu bán hàng nhưng không thấy link '{kind}' trên trang chủ",
        "ECOM_NO_BCT_LINK": "Không thấy link online.gov.vn (thông báo/đăng ký Bộ Công Thương). Khung mới: cần tra cứu lại",
        "ECOM_NO_TAX_ID": "Không thấy mã số thuế/số đăng ký doanh nghiệp trên trang chủ",
        "NONE": "Không có tín hiệu tự động. Vẫn phải đối chiếu checklist thủ công.",
        "homepage": "trang chủ",
        "no_action": "(không action)",
    },
    "en": {
        "TRACKING_COOKIE_BEFORE_CHOICE": "Tracking cookies present before any choice: {cookies}",
        "TRACKER_REQUEST_BEFORE_CHOICE": "{n} tracking requests before any choice (denied Consent Mode pings excluded)",
        "TRACKING_AFTER_DECLINE": "After clicking Decline there are still cookies [{cookies}] / {n} tracking requests",
        "NO_BANNER_BUT_TRACKERS": "Trackers found but no cookie banner detected (re-check: some banners only show in certain regions)",
        "NO_DECLINE_BUTTON": "Banner has no Decline button on equal footing with Accept",
        "ACCEPT_DOES_NOT_ENABLE": "Clicking Accept sets no tracking cookies: measurement may be broken",
        "EMBED_BEFORE_CONSENT": "{embeds} loaded before consent (page: {pages}). Use youtube-nocookie.com or a click-to-load placeholder",
        "PRECHECKED_CONSENT": "Form {form} has a pre-ticked checkbox",
        "FORM_NO_NOTICE": "Form {form} collects personal data without mentioning a policy/purpose",
        "NO_PRIVACY_LINK": "No privacy policy link found on the homepage",
        "PRIVACY_PAGE_ERROR": "Privacy policy link {url} could not be opened: {error}",
        "POLICY_CITES_EXPIRED_LAW": "{url} cites legal documents no longer in force: {refs}",
        "POLICY_NO_COOKIE_SECTION": "{url} does not mention cookies although the site uses trackers",
        "CONTINUE_MEANS_CONSENT": "{url} treats continued use as consent: \"{quote}\"",
        "THIRD_PARTY_CLAIM_MISMATCH": "{url} claims no sharing with third parties, but the site sends data to external services: \"{quote}\"",
        "MULTIPLE_PRIVACY_PAGES": "Several privacy policy pages: {urls}. Check they do not contradict each other",
        "ECOM_NO_LINK": "Selling signals found but no '{kind}' link on the homepage",
        "ECOM_NO_BCT_LINK": "No online.gov.vn link (Ministry of Industry and Trade notification/registration). New framework: verify",
        "ECOM_NO_TAX_ID": "No tax code / business registration number found on the homepage",
        "NONE": "No automatic signals. The checklists still need a manual review.",
        "homepage": "homepage",
        "no_action": "(no action)",
    },
}

REPORT_TEXT = {
    "vi": {
        "title": "Quét động", "time": "Thời điểm", "platform": "Nền tảng",
        "note": "> Dấu hiệu kèm bằng chứng, không phải kết luận pháp lý. Kết quả phụ thuộc vị trí máy quét.",
        "sessions": "Ba phiên đồng ý (desktop 1366)",
        "cols": "| Phiên | Banner | Nút đã bấm | Cookie theo dõi | Request theo dõi (vendor: số, gcs) | Lỗi |",
        "not_found": "không thấy", "no": "không",
        "signals": "Gợi ý cần xem (map sang checklist trong references/law/)",
        "inventory": "Kiểm kê trang chủ", "bct": "Link Bộ Công Thương", "biz": "Thông tin DN",
        "ecom": "Dấu hiệu bán hàng", "privacy": "Chính sách bảo mật", "forms": "Form",
        "form_line": "- action=`{action}` cá nhân={personal} nhắc chính sách={policy} checkbox={boxes} fields={fields}",
        "mobile": "Banner trên mobile 390", "shots": "Ảnh chụp", "hosts": "Máy chủ bên thứ ba đã gọi (mọi phiên)",
        "inventory_error": "Không kiểm kê được trang chủ",
    },
    "en": {
        "title": "Dynamic scan", "time": "Scanned at", "platform": "Platform",
        "note": "> Signals with evidence, not a legal conclusion. Results depend on the scanner's location.",
        "sessions": "Three consent sessions (desktop 1366)",
        "cols": "| Session | Banner | Clicked | Tracking cookies | Tracking requests (vendor: count, gcs) | Error |",
        "not_found": "not found", "no": "none",
        "signals": "Signals to review (mapped to checklists in references/law/)",
        "inventory": "Homepage inventory", "bct": "Ministry of Industry and Trade link", "biz": "Business info",
        "ecom": "Selling signals", "privacy": "Privacy policy", "forms": "Forms",
        "form_line": "- action=`{action}` personal={personal} mentions_policy={policy} checkboxes={boxes} fields={fields}",
        "mobile": "Banner on mobile 390", "shots": "Screenshots", "hosts": "Third-party hosts contacted (all sessions)",
        "inventory_error": "Homepage inventory failed",
    },
}
LANGS = tuple(MESSAGES)


def signals(phases, inv, lang="vi"):
    """Gợi ý (không phải kết luận) kèm mục checklist tương ứng trong references/law/."""
    M = MESSAGES[lang]
    out = []

    def add(code, ref, key=None, **kw):
        out.append({"code": code, "checklist": ref, "note": M[key or code].format(**kw)})

    none, dec, acc = phases.get("none"), phases.get("decline"), phases.get("accept")
    banner = none and none.get("banner")
    # Không tự tính là tracking: file nạp thư viện, telemetry nền tảng (Shopify tự áp consent),
    # widget chat Zalo (xem tay), và ping Consent Mode khi cả ads lẫn analytics bị từ chối (gcs=G100).
    real_track = lambda p: [h for h in p["tracker_requests"] if h["vendor"] not in NON_DECISIVE
                            and h["gcs"] != "G100"]
    if none and none["tracking_cookies"]:
        add("TRACKING_COOKIE_BEFORE_CHOICE", "01-C", cookies=", ".join(none["tracking_cookies"]))
    if none and real_track(none):
        add("TRACKER_REQUEST_BEFORE_CHOICE", "01-C", n=len(real_track(none)))
    if dec and not dec.get("error") and (dec["tracking_cookies"] or real_track(dec)):
        add("TRACKING_AFTER_DECLINE", "01-C", cookies=", ".join(dec["tracking_cookies"]), n=len(real_track(dec)))
    any_tracker = any(p and p["tracker_requests"] for p in phases.values())
    if not banner and any_tracker:
        add("NO_BANNER_BUT_TRACKERS", "01-C")
    if banner and not banner.get("has_decline"):
        add("NO_DECLINE_BUTTON", "01-B")
    if acc and not acc.get("error") and not acc["tracking_cookies"] and any_tracker:
        add("ACCEPT_DOES_NOT_ENABLE", "technical")
    embeds = sorted({h["vendor"] for p in (none, dec) if p for h in p["tracker_requests"]
                     if h["vendor"] in ("YouTube embed", "Google Maps embed")})
    if embeds:
        pages = sorted({p.get("second_page") or M["homepage"] for p in (none, dec) if p and any(
            h["vendor"] in embeds for h in p["tracker_requests"])})
        add("EMBED_BEFORE_CONSENT", "01-C", embeds=", ".join(embeds), pages=", ".join(pages))
    for f in [f for f in inv.get("forms", []) if f["collects_personal"]]:
        form = f["action"] or M["no_action"]
        if any(c["prechecked"] for c in f["checkboxes"]):
            add("PRECHECKED_CONSENT", "01-B", form=form)
        if not f["mentions_policy"]:
            add("FORM_NO_NOTICE", "01-B", form=form)
    pol = inv.get("policy_links", {})
    if "error" not in inv and not pol.get("privacy"):
        add("NO_PRIVACY_LINK", "01-A")
    for pp in inv.get("privacy_pages", []):
        u = pp["url"]
        if pp.get("error"):
            add("PRIVACY_PAGE_ERROR", "01-A", url=u, error=pp["error"])
            continue
        if pp.get("expired_refs"):
            add("POLICY_CITES_EXPIRED_LAW", "01-A", url=u, refs=", ".join(pp["expired_refs"]))
        if not pp.get("mentions_cookie") and any_tracker:
            add("POLICY_NO_COOKIE_SECTION", "01-C", url=u)
        flags = pp.get("red_flags") or {}
        if flags.get("continue_means_consent"):
            add("CONTINUE_MEANS_CONSENT", "01-B", url=u, quote=flags["continue_means_consent"])
        if flags.get("no_third_party_claim") and any_tracker:
            add("THIRD_PARTY_CLAIM_MISMATCH", "01-A", url=u, quote=flags["no_third_party_claim"])
    if len(inv.get("privacy_pages", [])) > 1:
        add("MULTIPLE_PRIVACY_PAGES", "01-A", urls=", ".join(p["url"] for p in inv["privacy_pages"]))
    if inv.get("ecommerce_signals"):
        for k in ("return", "shipping", "complaint", "terms"):
            if not pol.get(k):
                add(f"ECOM_NO_{k.upper()}_LINK", "02-C", key="ECOM_NO_LINK", kind=k)
        if not inv.get("bct_link"):
            add("ECOM_NO_BCT_LINK", "02-B")
        if not inv["business_info"]["tax_or_registration"]:
            add("ECOM_NO_TAX_ID", "02-C")
    return out


def md_report(data):
    lang = data.get("lang", "vi")
    T, M = REPORT_TEXT[lang], MESSAGES[lang]
    inv = data["inventory"]
    L = [f"# {T['title']}: {data['url']}", "",
         f"{T['time']}: {data['scanned_at']} · {T['platform']}: {', '.join(inv.get('platform', []))}",
         "", T["note"], "", f"## {T['sessions']}", "", T["cols"], "|---|---|---|---|---|---|"]
    for k in ("none", "decline", "accept"):
        p = data["phases"].get(k)
        if not p:
            continue
        b = p.get("banner") or {}
        vend = {}
        for h in p["tracker_requests"]:
            vend.setdefault(h["vendor"], [0, set()])
            vend[h["vendor"]][0] += 1
            if h["gcs"]:
                vend[h["vendor"]][1].add(h["gcs"])
        vs = "; ".join(f"{n}: {c}{' gcs=' + ','.join(sorted(g)) if g else ''}" for n, (c, g) in vend.items()) or "0"
        L.append(f"| {k} | {b.get('cmp', T['not_found'])} | {p.get('clicked') or '-'} | "
                 f"{', '.join(p['tracking_cookies']) or '0'} | {vs} | {p.get('error') or ''} |")
    L += ["", f"## {T['signals']}", ""]
    for s in data["signals"] or [{"code": "-", "checklist": "-", "note": M["NONE"]}]:
        L.append(f"- `{s['code']}` ({s['checklist']}): {s['note']}")
    L += ["", f"## {T['inventory']}", ""]
    if inv.get("error"):
        L.append(f"- {T['inventory_error']}: {inv['error']}")
    for k, v in inv.get("policy_links", {}).items():
        L.append(f"- Link {k}: {', '.join(x['h'] for x in v) or T['not_found']}")
    L.append(f"- {T['bct']}: {', '.join(inv.get('bct_link') or []) or T['not_found']}")
    L.append(f"- {T['biz']}: {json.dumps(inv.get('business_info'), ensure_ascii=False)}")
    L.append(f"- {T['ecom']}: {', '.join(inv.get('ecommerce_signals') or []) or T['no']}")
    for pp in inv.get("privacy_pages") or [{"url": T["not_found"]}]:
        L.append(f"- {T['privacy']}: {json.dumps(pp, ensure_ascii=False)}")
    L += ["", f"## {T['forms']}", ""]
    for f in inv.get("forms", []):
        L.append(T["form_line"].format(action=f["action"], personal=f["collects_personal"], policy=f["mentions_policy"],
                                       boxes=f["checkboxes"], fields=f["fields"]))
    mob = data["phases"].get("mobile_none")
    if mob and mob.get("banner"):
        L += ["", f"## {T['mobile']}", "", f"- {json.dumps(mob['banner'], ensure_ascii=False)}"]
    L += ["", f"## {T['shots']}", ""] + [f"- {s}" for s in data["screenshots"]]
    hosts = sorted(set(h for p in data["phases"].values() if p for h in p.get("third_party_hosts", [])))
    L += ["", f"## {T['hosts']}", "", ", ".join(hosts)]
    return "\n".join(L) + "\n"


def scan_site(url, out_dir="vn-legal-audit", with_mobile=True, lang="vi"):
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    desk = {"width": 1366, "height": 900}
    mob = {"width": 390, "height": 844}
    data = {"url": url, "lang": lang, "scanned_at": datetime.now(VN_TZ).isoformat(timespec="seconds"),
            "phases": {}, "screenshots": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            data["inventory"] = inventory(browser, url)
        except Exception as e:  # vẫn chạy các phiên đồng ý dù trang chủ kiểm kê lỗi
            data["inventory"] = {"error": f"{type(e).__name__}: {e}"}
        for action in ("none", "decline", "accept"):
            shot = "desktop-first-visit.png" if action == "none" else None
            data["phases"][action] = run_phase(browser, url, action, desk, out, shot)
            if shot:
                data["screenshots"].append(str(out / shot))
        if with_mobile:
            data["phases"]["mobile_none"] = run_phase(browser, url, "none", mob, out, "mobile-first-visit.png")
            data["screenshots"].append(str(out / "mobile-first-visit.png"))
        browser.close()
    data["signals"] = signals({k: v for k, v in data["phases"].items() if k in ("none", "decline", "accept")},
                              data["inventory"], lang)
    (out / "scan.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "scan.md").write_text(md_report(data), encoding="utf-8")
    return data


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", default="vn-legal-audit")
    ap.add_argument("--no-mobile", action="store_true")
    ap.add_argument("--lang", choices=LANGS, default="vi", help="ngôn ngữ báo cáo / report language (vi, en)")
    a = ap.parse_args()
    if not re.match(r"^https?://", a.url):
        sys.exit("URL must start with http:// or https:// (URL phải bắt đầu bằng http:// hoặc https://)")
    out = Path(a.out)
    data = scan_site(a.url, out_dir=a.out, with_mobile=not a.no_mobile, lang=a.lang)
    print(f"{out / 'scan.md'} · {out / 'scan.json'}")
    for s in data["signals"]:
        print(f"  [{s['checklist']}] {s['code']}: {s['note']}")


if __name__ == "__main__":
    main()
