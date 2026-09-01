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

# Ana akım ve Premium Spor Kanalları
TARGET_CHANNELS = [
    "ARD", "ZDF", "RTL", "RTL2", "SAT.1", "PRO 7", "3SAT", "ONE",
    "Sky Sport Bundesliga 1", "Sky Sport Bundesliga 2", "Sky Sport Bundesliga 3",
    "Sky Sport Bundesliga 4", "Sky Sport Bundesliga 5",
    "DAZN 1", "DAZN 2"
]

TIME_RANGE_RE = re.compile(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})")

def fetch_tvmovie_now():
    url = "https://www.tvmovie.de/tv-programm-jetzt"
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    channels_data = {ch: [] for ch in TARGET_CHANNELS}
    
    for a in soup.select('a[href*="-epg-"]'):
        text = " ".join(a.get_text(strip=True).split())
        m = TIME_RANGE_RE.search(text)
        if not m:
            continue
            
        start, end = m.group(1), m.group(2)
        title = text[:m.start()].strip() or "Program"
        href = a.get("href", "")
        detail_url = href if href.startswith("http") else f"https://www.tvmovie.de{href}"

        parent = a.find_parent(class_=re.compile(r'channel|sender|broadcast|tv-list', re.I)) or a.parent
        parent_text = parent.get_text() if parent else ""

        matched_channel = None
        for ch in TARGET_CHANNELS:
            check_name = "PRO7" if ch == "PRO 7" else ch
            if check_name.lower() in parent_text.lower():
                matched_channel = ch
                break

        if matched_channel:
            exists = any(item['title'] == title and item['time'] == start for item in channels_data[matched_channel])
            if not exists:
                channels_data[matched_channel].append({
                    "time": start,
                    "endTime": end,
                    "title": title[:100],
                    "genre": "TV",
                    "url": detail_url
                })

    if "PRO 7" in channels_data:
        channels_data["ProSieben"] = channels_data.pop("PRO 7")

    return channels_data

def main():
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "channels": {}
    }

    try:
        channels_data = fetch_tvmovie_now()
        result["channels"] = channels_data
        total_programs = sum(len(v) for v in channels_data.values())
    except Exception as e:
        print(f"[HATA] Ana akış çekilemedi: {e}")
        total_programs = 0

    if total_programs == 0:
        print("Veri çekilemedi, işlem iptal edildi.")
        sys.exit(1)

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Başarıyla güncellendi! Toplam {total_programs} yayın çekildi.")

if __name__ == "__main__":
    main()
