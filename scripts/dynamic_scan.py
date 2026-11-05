#!/usr/bin/env python3
"""Quét động một website bằng trình duyệt thật để lấy bằng chứng cho audit pháp lý VN.

    python scripts/dynamic_scan.py https://ten-mien.vn --out ./vn-legal-audit

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


def signals(phases, inv):
    """Gợi ý (không phải kết luận) kèm mục checklist tương ứng trong references/law/."""
    out = []
    def add(code, ref, msg):
        out.append({"code": code, "checklist": ref, "note": msg})
    none, dec, acc = phases.get("none"), phases.get("decline"), phases.get("accept")
    banner = none and none.get("banner")
    # Không tự tính là tracking: file nạp thư viện, telemetry nền tảng (Shopify tự áp consent),
    # widget chat Zalo (xem tay), và ping Consent Mode khi cả ads lẫn analytics bị từ chối (gcs=G100).
    real_track = lambda p: [h for h in p["tracker_requests"] if h["vendor"] not in NON_DECISIVE
                            and h["gcs"] != "G100"]
    if none and none["tracking_cookies"]:
        add("TRACKING_COOKIE_BEFORE_CHOICE", "01-C", f"Cookie theo dõi có khi chưa chọn gì: {', '.join(none['tracking_cookies'])}")
    if none and real_track(none):
        add("TRACKER_REQUEST_BEFORE_CHOICE", "01-C", f"{len(real_track(none))} request theo dõi khi chưa chọn (đã loại ping Consent Mode bị từ chối)")
    if dec and not dec.get("error") and (dec["tracking_cookies"] or real_track(dec)):
        add("TRACKING_AFTER_DECLINE", "01-C", f"Sau khi bấm Từ chối vẫn có cookie {dec['tracking_cookies']} / {len(real_track(dec))} request theo dõi")
    any_tracker = any(p and p["tracker_requests"] for p in phases.values())
    if not banner and any_tracker:
        add("NO_BANNER_BUT_TRACKERS", "01-C", "Có dịch vụ theo dõi nhưng không thấy banner cookie (kiểm tra lại: banner có thể chỉ hiện theo vùng)")
    if banner and not banner.get("has_decline"):
        add("NO_DECLINE_BUTTON", "01-B", "Banner không có nút Từ chối ngang hàng với Chấp nhận")
    if acc and not acc.get("error") and not acc["tracking_cookies"] and any_tracker:
        add("ACCEPT_DOES_NOT_ENABLE", "kỹ thuật", "Bấm Chấp nhận nhưng không thấy cookie theo dõi: đo lường có thể đã hỏng")
    embeds = sorted({h["vendor"] for p in (none, dec) if p for h in p["tracker_requests"]
                     if h["vendor"] in ("YouTube embed", "Google Maps embed")})
    if embeds:
        pages = sorted({p.get("second_page") or "trang chủ" for p in (none, dec) if p and any(
            h["vendor"] in embeds for h in p["tracker_requests"])})
        add("EMBED_BEFORE_CONSENT", "01-C", f"{', '.join(embeds)} nạp trước khi đồng ý (trang: {', '.join(pages)}). "
            "Dùng youtube-nocookie.com hoặc ảnh thay thế bấm-để-tải")
    forms = [f for f in inv.get("forms", []) if f["collects_personal"]]
    for f in forms:
        if any(c["prechecked"] for c in f["checkboxes"]):
            add("PRECHECKED_CONSENT", "01-B", f"Form {f['action'] or '(không action)'} có ô tích sẵn")
        if not f["mentions_policy"]:
            add("FORM_NO_NOTICE", "01-B", f"Form {f['action'] or '(không action)'} thu thông tin cá nhân nhưng không nhắc chính sách/mục đích")
    pol = inv.get("policy_links", {})
    if not pol.get("privacy"):
        add("NO_PRIVACY_LINK", "01-A", "Không thấy link chính sách bảo mật trên trang chủ")
    for pp in inv.get("privacy_pages", []):
        u = pp["url"]
        if pp.get("error"):
            add("PRIVACY_PAGE_ERROR", "01-A", f"Link chính sách bảo mật {u} không mở được: {pp['error']}")
            continue
        if pp.get("expired_refs"):
            add("POLICY_CITES_EXPIRED_LAW", "01-A", f"{u} dẫn văn bản đã hết hiệu lực: {', '.join(pp['expired_refs'])}")
        if not pp.get("error") and not pp.get("mentions_cookie") and any_tracker:
            add("POLICY_NO_COOKIE_SECTION", "01-C", f"{u} không nhắc cookie dù site có dịch vụ theo dõi")
        flags = pp.get("red_flags") or {}
        if flags.get("continue_means_consent"):
            add("CONTINUE_MEANS_CONSENT", "01-B", f"{u} coi việc tiếp tục sử dụng là đồng ý: \"{flags['continue_means_consent']}\"")
        if flags.get("no_third_party_claim") and any_tracker:
            add("THIRD_PARTY_CLAIM_MISMATCH", "01-A", f"{u} nói không chia sẻ bên thứ ba nhưng site gửi dữ liệu cho dịch vụ bên ngoài: \"{flags['no_third_party_claim']}\"")
    if len(inv.get("privacy_pages", [])) > 1:
        add("MULTIPLE_PRIVACY_PAGES", "01-A", "Có nhiều trang chính sách bảo mật: " + ", ".join(p["url"] for p in inv["privacy_pages"]) + ". Kiểm tra nội dung có mâu thuẫn không")
    if inv.get("ecommerce_signals"):
        for k in ("return", "shipping", "complaint", "terms"):
            if not pol.get(k):
                add(f"ECOM_NO_{k.upper()}_LINK", "02-C", f"Có dấu hiệu bán hàng nhưng không thấy link '{k}' trên trang chủ")
        if not inv.get("bct_link"):
            add("ECOM_NO_BCT_LINK", "02-B", "Không thấy link online.gov.vn (thông báo/đăng ký Bộ Công Thương). Khung mới: cần tra cứu lại")
        if not inv["business_info"]["tax_or_registration"]:
            add("ECOM_NO_TAX_ID", "02-C", "Không thấy mã số thuế/số đăng ký doanh nghiệp trên trang chủ")
    return out


def md_report(data):
    L = [f"# Quét động: {data['url']}", "",
         f"Thời điểm: {data['scanned_at']} · Nền tảng: {', '.join(data['inventory'].get('platform', []))}",
         "", "> Dấu hiệu kèm bằng chứng, không phải kết luận pháp lý. Kết quả phụ thuộc vị trí máy quét.", "",
         "## Ba phiên đồng ý (desktop 1366)", "",
         "| Phiên | Banner | Nút đã bấm | Cookie theo dõi | Request theo dõi (vendor: số, gcs) | Lỗi |", "|---|---|---|---|---|---|"]
    for k in ("none", "decline", "accept"):
        p = data["phases"].get(k)
        if not p:
            continue
        b = p.get("banner") or {}
        vend = {}
        for h in p["tracker_requests"]:
            key = h["vendor"]
            vend.setdefault(key, [0, set()])
            vend[key][0] += 1
            if h["gcs"]:
                vend[key][1].add(h["gcs"])
        vs = "; ".join(f"{n}: {c}{' gcs=' + ','.join(sorted(g)) if g else ''}" for n, (c, g) in vend.items()) or "0"
        L.append(f"| {k} | {b.get('cmp', 'không thấy')} | {p.get('clicked') or '-'} | {', '.join(p['tracking_cookies']) or '0'} | {vs} | {p.get('error') or ''} |")
    L += ["", "## Gợi ý cần xem (map sang checklist trong references/law/)", ""]
    for s in data["signals"] or [{"code": "-", "checklist": "-", "note": "Không có tín hiệu tự động. Vẫn phải đối chiếu checklist thủ công."}]:
        L.append(f"- `{s['code']}` ({s['checklist']}): {s['note']}")
    inv = data["inventory"]
    L += ["", "## Kiểm kê trang chủ", ""]
    for k, v in inv.get("policy_links", {}).items():
        L.append(f"- Link {k}: {', '.join(x['h'] for x in v) or 'không thấy'}")
    L.append(f"- Link Bộ Công Thương: {', '.join(inv.get('bct_link') or []) or 'không thấy'}")
    L.append(f"- Thông tin DN: {json.dumps(inv.get('business_info'), ensure_ascii=False)}")
    L.append(f"- Dấu hiệu bán hàng: {', '.join(inv.get('ecommerce_signals') or []) or 'không'}")
    for pp in inv.get("privacy_pages") or [{"url": "không thấy"}]:
        L.append(f"- Chính sách bảo mật: {json.dumps(pp, ensure_ascii=False)}")
    L += ["", "## Form", ""]
    for f in inv.get("forms", []):
        L.append(f"- action=`{f['action']}` cá nhân={f['collects_personal']} nhắc chính sách={f['mentions_policy']} checkbox={f['checkboxes']} fields={f['fields']}")
    mob = data["phases"].get("mobile_none")
    if mob and mob.get("banner"):
        L += ["", "## Banner trên mobile 390", "", f"- {json.dumps(mob['banner'], ensure_ascii=False)}"]
    L += ["", "## Ảnh chụp", ""] + [f"- {s}" for s in data["screenshots"]]
    hosts = sorted(set(h for p in data["phases"].values() if p for h in p.get("third_party_hosts", [])))
    L += ["", "## Máy chủ bên thứ ba đã gọi (mọi phiên)", "", ", ".join(hosts)]
    return "\n".join(L) + "\n"


def scan_site(url, out_dir="vn-legal-audit", with_mobile=True):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    desk = {"width": 1366, "height": 900}
    mob = {"width": 390, "height": 844}
    data = {"url": url, "scanned_at": datetime.now(VN_TZ).isoformat(timespec="seconds"), "phases": {}, "screenshots": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        data["inventory"] = inventory(browser, url)
        for action in ("none", "decline", "accept"):
            shot = "desktop-first-visit.png" if action == "none" else None
            data["phases"][action] = run_phase(browser, url, action, desk, out, shot)
            if shot:
                data["screenshots"].append(str(out / shot))
        if with_mobile:
            data["phases"]["mobile_none"] = run_phase(browser, url, "none", mob, out, "mobile-first-visit.png")
            data["screenshots"].append(str(out / "mobile-first-visit.png"))
        browser.close()
    data["signals"] = signals({k: v for k, v in data["phases"].items() if k in ("none", "decline", "accept")}, data["inventory"])
    (out / "scan.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "scan.md").write_text(md_report(data), encoding="utf-8")
    return data


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", default="vn-legal-audit")
    ap.add_argument("--no-mobile", action="store_true")
    a = ap.parse_args()
    if not re.match(r"^https?://", a.url):
        sys.exit("URL phải bắt đầu bằng http:// hoặc https://")
    out = Path(a.out)
    data = scan_site(a.url, out_dir=a.out, with_mobile=not a.no_mobile)
    print(f"Đã ghi {out / 'scan.md'} và {out / 'scan.json'}")
    for s in data["signals"]:
        print(f"  [{s['checklist']}] {s['code']}: {s['note']}")


if __name__ == "__main__":
    main()
