# VN Law Guard

[![tests](https://github.com/gonostudy305/vn-law-guard/actions/workflows/tests.yml/badge.svg)](https://github.com/gonostudy305/vn-law-guard/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Tiếng Việt](README.md) · **English**

🌐 [Technical overview](https://vn-consent-evidence-guard.lovable.app/?ref=github) · [Done-for-you review service for businesses (Vietnamese)](https://du-lieu-sach-viet.lovable.app/?ref=github)

A technical review kit for websites operating in Vietnam: it **measures cookie and tracking behaviour in a real browser**, maps the findings to Vietnamese legal checklists, and ships **fix templates** per platform. Use it as an AI coding-agent skill (Claude Code, Antigravity…) or as a standalone Python tool.

> This is a review aid, **not legal advice**, and it does not certify compliance. See [Disclaimer](#disclaimer).

## Who it is for

- Developers and agencies building sites for the Vietnamese market who want to hand over a site with measured consent evidence.
- Foreign companies and developers launching in Vietnam: scanner reports are available in English (`--lang en`).
- Site owners and marketers who need to know whether tracking runs before visitors consent.

## What it covers

| Part | Contents |
|---|---|
| Dynamic scan [`scripts/dynamic_scan.py`](scripts/dynamic_scan.py) | Opens the site in Chromium (Playwright): 3 clean desktop sessions at 1366px (no choice / Decline / Accept) plus 1 mobile session at 390px. Records tracking cookies and requests per session (GA4, Google Ads, Meta, TikTok, embedded YouTube…), detects consent banners (Shopify, OneTrust, Cookiebot, CookieYes, Complianz, custom), inventories forms, policy pages and business details. Outputs `scan.json`, `scan.md` and screenshots. |
| Static scan [`scripts/scan.sh`](scripts/scan.sh) | Source-code scan (from vn-law-check). |
| Legal checklists [`references/law/`](references/law/) | Personal data protection, e-commerce, cybersecurity, consumer protection, advertising, e-transactions, AI transparency, penalties. Kept unchanged from [vn-law-check](https://github.com/mhfed/vn-law-check). **Written in Vietnamese.** |
| Platform guides [`references/platforms/`](references/platforms/) | Shopify (from a real project), WordPress/WooCommerce, Haravan/Sapo (not yet field-tested), custom code. Vietnamese. |
| Fix templates [`templates/remediation/`](templates/remediation/) | Consent Mode v2 for Shopify and plain sites, click-to-load YouTube, form notice and consent checkbox, cookie section for the privacy policy. |

### Laws referenced (as of 3 Nov 2026)

| Area | Main instruments |
|---|---|
| Personal data | Law on Personal Data Protection No. 91/2025/QH15 (in force 1 Jan 2026); Decree 356/2025/ND-CP (replaces Decree 13/2023, which expired 1 Jan 2026); sanctions: Decree 330/2026/ND-CP |
| E-commerce | Law on E-commerce No. 122/2025/QH15 (in force 1 Jul 2026); Decree 248/2026/ND-CP. Sites notified under the old framework may operate until 30 Jun 2027. Foreign platforms selling to Vietnamese buyers have specific duties (checklist `02-ecommerce`, section G). |
| Others | Consumer protection, cybersecurity, advertising, e-transactions, AI: see [`legal-references.md`](references/law/legal-references.md). |

Many figures come from secondary sources and are marked "CHƯA XÁC MINH" (not verified) where unconfirmed. Always check the current text at [vbpl.vn](https://vbpl.vn) or [thuvienphapluat.vn](https://thuvienphapluat.vn) and with Vietnamese counsel.

### Working with the Vietnamese checklists

The checklists are in Vietnamese because they quote Vietnamese legal text. When used as an agent skill, ask the agent to *"audit https://… against Vietnamese law and write the report in English"*: it reads the Vietnamese sources and reports in English, keeping the original legal citations. The scanner itself can report in English with `--lang en`.

## Install

Requires Python 3.10+ and Git. The static scan (`scan.sh`) needs bash: built into macOS/Linux; on Windows use Git Bash or WSL.

```bash
git clone https://github.com/gonostudy305/vn-law-guard.git
cd vn-law-guard
python -m pip install -r requirements.txt
python -m playwright install chromium
```

On bare Linux servers/CI use `python -m playwright install --with-deps chromium`.

## Usage

```bash
python scripts/dynamic_scan.py https://example.com --out ./report --lang en
```

| Option | Meaning |
|---|---|
| `--out` | Output folder (default `vn-legal-audit`) |
| `--lang vi\|en` | Language of `scan.md` and signal notes (default `vi`) |
| `--no-mobile` | Skip the 390px mobile session |

Each signal has a stable code (e.g. `TRACKING_COOKIE_BEFORE_CHOICE`) and a checklist reference (e.g. `01-C`).

Reading results:
- Results depend on **where the scanner runs**: many platforms show a banner only to visitors from regions that require consent. To see what Vietnamese visitors see, scan from a Vietnamese IP.
- The scanner opens the homepage, one internal page and the privacy pages. Check checkout/account pages manually.
- Denied Consent Mode pings (`gcs=G100`) set no cookies and are not counted as tracking.

### As an AI skill

```bash
# Claude Code
git clone https://github.com/gonostudy305/vn-law-guard.git ~/.claude/skills/vn-law-guard
```

Antigravity: `~/.gemini/config/skills/vn-law-guard`. Per project: `.agents/skills/vn-law-guard`. The agent follows [`SKILL.md`](SKILL.md): scan → triage → checklist review → evidence-based report → code changes only after you approve.

## Responsible use

- Only scan sites you own, clients who agreed, or sites you are authorised to test. The scanner is read-only (no form submission, login or payment) but creates real visits (about 5 browser sessions per run).
- Do not publish the names of sites with findings without the owner's consent.
- Final legal conclusions belong to a lawyer or the competent authority.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Tests spin up local pages on `127.0.0.1` and do not call the Internet. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CHANGELOG.md](CHANGELOG.md).

## Disclaimer

The content is compiled from public Vietnamese legal documents and secondary sources (law firms, press), not fully verified against the Official Gazette. It is not legal advice and does not replace a lawyer or the authorities. Findings are initial review signals, not legal conclusions. You are responsible for how you apply it. Full text (Vietnamese): [DISCLAIMER.md](DISCLAIMER.md).

## Credits and license

Legal checklists in `references/law/`, `examples/`, `scripts/scan.sh` and `scripts/fetch-site.sh` come from [mhfed/vn-law-check](https://github.com/mhfed/vn-law-check) (MIT); see [NOTICE.md](NOTICE.md). This project is released under the [MIT License](LICENSE).
