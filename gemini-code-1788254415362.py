#!/usr/bin/env python3
"""
Bundesliga TV — Almanya Yayın Akışı Scraper'ı
================================================
Kaynak: tvmovie.de

NE YAPAR:
Her kanal için https://www.tvmovie.de/tv/sender-<slug> sayfasını çeker,
programları (saat, başlık, tür) ayıklar ve hepsini tek bir epg.json dosyasına yazar.
index.html bu epg.json dosyasını okuyup arayüzü günceller.
"""

import json
import re
import sys
from datetime import datetime, timezone

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Önce bağımlılıkları kur: pip install requests beautifulsoup4 --break-system-packages")
    sys.exit(1)

# Takip edilen 8 kanal ve tvmovie.de slug karşılıkları
CHANNELS = {
    "ARD":       "ard",
    "ZDF":       "zdf",
    "RTL":       "rtl",
    "RTL2":      "rtl-ii",
    "SAT.1":     "sat1",
    "ProSieben": "pro-7",
    "3sat":      "3sat",
    "ONE":       "one",
}

BASE_URL = "https://www.tvmovie.de/tv/sender-{slug}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

TIME_RANGE_RE = re.compile(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})")
KNOWN_CATEGORIES = ["Film", "Serie", "Unterhaltung", "Reportage", "Sport", "Kinder"]


def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def guess_category_tr(raw_category: str) -> str:
    mapping = {
        "Film": "Film", 
        "Serie": "Dizi", 
        "Unterhaltung": "Eğlence",
        "Reportage": "Belgesel", 
        "Sport": "Spor", 
        "Kinder": "Çocuk",
    }
    return mapping.get(raw_category, raw_category or "Program")


def parse_channel(channel_name: str, slug: str, debug: bool = False):
    url = BASE_URL.format(slug=slug)
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  [HATA] {channel_name}: {e}")
        return []

    if debug:
        fname = f"debug_{channel_name.lower().replace('.', '').replace(' ', '_')}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [debug] ham HTML kaydedildi -> {fname}")

    soup = BeautifulSoup(html, "html.parser")

    entries = []
    seen_hrefs = set()
    for a in soup.select('a[href*="-epg-"]'):
        href = a.get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        text = " ".join(a.get_text(separator=" ", strip=True).split())
        m = TIME_RANGE_RE.search(text)
        if not m:
            continue
        start, end = m.group(1), m.group(2)

        before_time = text[: m.start()].strip()
        category_found = next((c for c in KNOWN_CATEGORIES if c in before_time), "")
        title_guess = before_time
        if category_found:
            idx = before_time.rfind(category_found)
            title_guess = before_time[idx + len(category_found):].strip()
        title_guess = title_guess[:120] if title_guess else before_time[:120]

        entries.append({
            "time": start,
            "endTime": end,
            "title": title_guess or "(başlık ayıklanamadı)",
            "genre": guess_category_tr(category_found),
        })

        if debug and len(entries) <= 5:
            print(f"    -> {start}-{end} | {title_guess!r} | kategori tahmini: {category_found!r}")

    return entries


def main():
    debug = "--debug" in sys.argv
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "channels": {},
    }

    for name, slug in CHANNELS.items():
        print(f"Çekiliyor: {name} ({BASE_URL.format(slug=slug)})")
        items = parse_channel(name, slug, debug=debug)
        print(f"  -> {len(items)} program bulundu")
        result["channels"][name] = items

    out_path = "epg.json"
    total = sum(len(v) for v in result["channels"].values())

    if total == 0:
        print("\n[UYARI] Hiçbir kanalda program bulunamadı — eski epg.json dosyasını BOZMAMAK için üzerine yazılmadı.")
        if debug:
            print("debug_*.html dosyalarını inceleyebilirsin.")
        sys.exit(1)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nBaşarılı! {out_path} güncellendi (Toplam {total} program).")


if __name__ == "__main__":
    main()