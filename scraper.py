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

# TV Spielfilm Kanal Kodları ve Haritalaması
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"]},
    {"name": "ZDF", "search": ["zdf"]},
    {"name": "RTL", "search": ["rtl"]},
    {"name": "RTL2", "search": ["rtl2", "rtl 2", "rtl ii"]},
    {"name": "SAT.1", "search": ["sat.1", "sat1"]},
    {"name": "ProSieben", "search": ["prosieben", "pro7", "pro 7"]},
    {"name": "3sat", "search": ["3sat"]},
    {"name": "ONE", "search": ["one"]},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1"]},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2"]},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3"]},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4"]},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5"]},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"]},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"]}
]

def fetch_tvspielfilm():
    url = "https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    channels_data = {item["name"]: [] for item in CHANNELS_CONFIG}
    rows = soup.select("tr, .broadcast-list-item, table tbody tr")

    for row in rows:
        row_text = row.get_text(" ", strip=True)
        
        # Kanalla eşleştir
        matched_channel = None
        for cfg in CHANNELS_CONFIG:
            for keyword in cfg["search"]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', row_text.lower()):
                    matched_channel = cfg["name"]
                    break
            if matched_channel:
                break
        
        if not matched_channel:
            continue

        # Saat aralığını bul (Örn: 14:00 - 15:00 veya 14:00)
        time_match = re.search(r"(\d{2}:\d{2})\s*[-–]?\s*(\d{2}:\d{2})?", row_text)
        if not time_match:
            continue

        start_time = time_match.group(1)
        end_time = time_match.group(2) if time_match.group(2) else "--:--"

        # Başlığı çek
        title_elem = row.select_one("a[title], .title, strong, h3, a")
        title = title_elem.get_text(strip=True) if title_elem else "Program"
        
        # Gereksiz kategori kelimelerini temizle
        genres = ["REPORTAGE", "SERIE", "UNTERHALTUNG", "KINDER", "SPORT", "DOKU-SOAP", "MAGAZIN", "NACHRICHTEN", "DOKU"]
        for g in genres:
            if title.upper().startswith(g):
                title = title[len(g):].strip()

        href = title_elem.get("href", "#") if title_elem else "#"
        detail_url = href if href.startswith("http") else f"https://www.tvspielfilm.de{href}" if href != "#" else "#"

        # Ekle (Tekrarları önle)
        exists = any(item['title'] == title and item['time'] == start_time for item in channels_data[matched_channel])
        if not exists:
            channels_data[matched_channel].append({
                "time": start_time,
                "endTime": end_time,
                "title": title[:90],
                "genre": "TV",
                "url": detail_url
            })

    return channels_data

def main():
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "channels": {}
    }

    try:
        channels_data = fetch_tvspielfilm()
        result["channels"] = channels_data
        total_programs = sum(len(v) for v in channels_data.values())
    except Exception as e:
        print(f"[HATA] TV Spielfilm veri çekme başarısız: {e}")
        total_programs = 0

    if total_programs == 0:
        print("Veri çekilemedi, işlem iptal edildi.")
        sys.exit(1)

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Başarıyla güncellendi! Toplam {total_programs} yayın verisi oluşturuldu.")

if __name__ == "__main__":
    main()
