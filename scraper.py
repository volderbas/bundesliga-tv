#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

CHANNELS = {
    "ARD": "ard",
    "ZDF": "zdf",
    "RTL": "rtl",
    "RTL2": "rtl-ii",
    "SAT.1": "sat1",
    "ProSieben": "pro-7",
    "3sat": "3sat",
    "ONE": "one"
}

TIME_RANGE_RE = re.compile(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})")

def fetch_tvmovie(slug):
    url = f"https://www.tvmovie.de/tv/sender-{slug}"
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    entries = []
    seen = set()
    for a in soup.select('a[href*="-epg-"]'):
        href = a.get("href", "")
        if href in seen:
            continue
        seen.add(href)
        
        text = " ".join(a.get_text(strip=True).split())
        m = TIME_RANGE_RE.search(text)
        if not m:
            continue
            
        start, end = m.group(1), m.group(2)
        title = text[:m.start()].strip() or "Program"
        
        entries.append({
            "time": start,
            "endTime": end,
            "title": title[:100],
            "genre": "TV"
        })
    return entries

def main():
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "channels": {}
    }

    total_programs = 0
    for name, slug in CHANNELS.items():
        try:
            items = fetch_tvmovie(slug)
            result["channels"][name] = items
            total_programs += len(items)
        except Exception as e:
            print(f"[HATA] {name} çekilemedi: {e}")
            result["channels"][name] = []

    # Eğer hiçbir program çekilemediyse mevcudu bozma
    if total_programs == 0:
        print("Hiç veri çekilemedi, iptal ediliyor.")
        sys.exit(1)

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Başarıyla güncellendi. Toplam {total_programs} yayın bulundu.")

if __name__ == "__main__":
    main()
