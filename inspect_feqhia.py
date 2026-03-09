#!/usr/bin/env python3
"""
inspect_feqhia.py — فحص بنية HTML لموقع dorar.net/feqhia
يطبع تقريراً كاملاً يُستخدم لبناء السكريبت الرئيسي.

Usage:
    python inspect_feqhia.py
"""

import re
import time
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL  = "https://dorar.net"
TOC_URL   = f"{BASE_URL}/feqhia"
# صفحة محتوى حقيقية (أول مبحث في كتاب الطهارة)
SAMPLE_PAGE_URL = f"{BASE_URL}/feqhia/3"
PAGE_RE   = re.compile(r"/feqhia/(\d+)")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
        "Chrome/109.0.0.0"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

_session = requests.Session()
_session.headers.update(HEADERS)


def fetch(url: str) -> BeautifulSoup:
    r = _session.get(url, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "html.parser")


def sep(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── 1) فحص صفحة الفهرس (TOC) ─────────────────────────────────────────────────
def inspect_toc(soup: BeautifulSoup):
    sep("1) صفحة الفهرس — روابط /feqhia/رقم")

    all_links = soup.find_all("a", href=PAGE_RE)
    ids = sorted({int(PAGE_RE.search(a["href"]).group(1)) for a in all_links})
    print(f"  عدد الروابط الفريدة: {len(ids)}")
    print(f"  أول ٥ IDs : {ids[:5]}")
    print(f"  آخر ٥ IDs : {ids[-5:]}")
    print(f"  أدنى ID   : {min(ids)}")
    print(f"  أعلى ID   : {max(ids)}")

    sep("2) البحث عن حاوية الفهرس (ul/nav/div)")
    candidates = []

    for ul in soup.find_all("ul"):
        links = ul.find_all("a", href=PAGE_RE)
        if len(links) >= 5:
            cls   = ul.get("class", [])
            pid   = ul.get("id", "")
            depth = len(list(ul.parents))
            candidates.append((len(links), depth, str(cls), pid, ul.name))

    candidates.sort(reverse=True)
    print(f"  أكبر ul تحتوي روابط feqhia:")
    for count, depth, cls, pid, tag in candidates[:5]:
        print(f"    <{tag}> id='{pid}' class={cls} — {count} رابط  (عمق={depth})")

    sep("3) عمق التداخل في القائمة")
    # أعمق ul
    best_ul = None
    best_count = 0
    for ul in soup.find_all("ul"):
        c = len(ul.find_all("a", href=PAGE_RE))
        if c > best_count:
            best_count = c
            best_ul = ul

    if best_ul:
        # عدد مستويات ul المتداخلة
        def max_depth(tag, current=0):
            sub = tag.find("ul", recursive=False)
            return max_depth(sub, current+1) if sub else current

        first_li = best_ul.find("li", recursive=False)
        if first_li:
            d = max_depth(first_li)
            print(f"  أعمق تداخل ul: {d} مستويات")

        # اطبع أول كتابين بشكل شجري
        print("\n  عينة من الشجرة (أول كتابين):")
        top_lis = best_ul.find_all("li", recursive=False)[:2]
        for li in top_lis:
            _print_tree(li, 0)


def _print_tree(li, depth, max_d=4):
    if depth > max_d:
        return
    a = li.find("a", recursive=False) or li.find("span", recursive=False)
    href = a.get("href", "") if a else ""
    pid  = PAGE_RE.search(href).group(1) if PAGE_RE.search(href) else "—"
    text = a.get_text(strip=True)[:50] if a else "?"
    print(f"  {'  '*depth}[{pid}] {text}")
    sub_ul = li.find("ul", recursive=False)
    if sub_ul:
        for child_li in sub_ul.find_all("li", recursive=False)[:3]:
            _print_tree(child_li, depth+1, max_d)
        remaining = len(sub_ul.find_all("li", recursive=False)) - 3
        if remaining > 0:
            print(f"  {'  '*(depth+1)}... و{remaining} أكثر")


# ── 2) فحص صفحة محتوى ────────────────────────────────────────────────────────
def inspect_content_page(soup: BeautifulSoup, url: str):
    sep(f"4) صفحة المحتوى: {url}")

    # العنوان
    h1 = soup.find("h1")
    og = soup.find("meta", property="og:title")
    print(f"  h1           : {h1.get_text(strip=True) if h1 else 'غير موجود'}")
    print(f"  og:title     : {og['content'] if og else 'غير موجود'}")

    # breadcrumb
    sep("5) Breadcrumb")
    bc = soup.find("ol", class_="breadcrumb")
    if bc:
        items = [li.get_text(strip=True) for li in bc.find_all("li")]
        print(f"  {' > '.join(items)}")
    else:
        print("  لم يُعثر على breadcrumb بـ class='breadcrumb'")
        # جرّب بدائل
        for tag in soup.find_all(["nav", "ol", "ul"]):
            cls = " ".join(tag.get("class", []))
            if "bread" in cls.lower() or "crumb" in cls.lower():
                print(f"  بديل محتمل: <{tag.name}> class='{cls}'")

    # حاوية المحتوى
    sep("6) حاوية المحتوى الرئيسية")
    for candidate in [
        ("id", "cntnt"),
        ("class", "amiri_custom_content"),
        ("class", "w-100"),
    ]:
        attr, val = candidate
        el = soup.find(attrs={attr: lambda v, x=val: v and x in (v if isinstance(v, list) else [v])})
        if el:
            txt_len = len(el.get_text(strip=True))
            print(f"  ✅ وُجد [{attr}='{val}'] — طول النص: {txt_len} حرف")
        else:
            print(f"  ❌ [{attr}='{val}'] غير موجود")

    # الحواشي
    sep("7) الحواشي (span.tip)")
    tips = soup.find_all("span", class_="tip")
    print(f"  عدد الحواشي: {len(tips)}")
    if tips:
        print(f"  عينة: {tips[0].get_text(strip=True)[:80]}…")

    # spans خاصة
    sep("8) Spans ذات classes خاصة")
    special = {}
    for sp in soup.find_all("span", class_=True):
        for cls in sp.get("class", []):
            if cls in ("aaya", "hadith", "sora", "title-1", "title-2"):
                special[cls] = special.get(cls, 0) + 1
    if special:
        for k, v in special.items():
            print(f"  {k}: {v}")
    else:
        print("  لا توجد")

    # التنقل
    sep("9) روابط التنقل (السابق/التالي)")
    for a in soup.find_all("a", href=PAGE_RE):
        txt = a.get_text(strip=True)
        if txt in ("التالي", "السابق"):
            print(f"  [{txt}] → {a['href']}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=== inspect_feqhia.py ===\n")

    print(f"⏳ جلب صفحة الفهرس: {TOC_URL}")
    toc_soup = fetch(TOC_URL)
    inspect_toc(toc_soup)

    time.sleep(1)

    print(f"\n⏳ جلب صفحة محتوى: {SAMPLE_PAGE_URL}")
    page_soup = fetch(SAMPLE_PAGE_URL)
    inspect_content_page(page_soup, SAMPLE_PAGE_URL)

    print("\n\n✅ انتهى الفحص — شارك النتائج لبناء السكريبت الرئيسي")


if __name__ == "__main__":
    main()
