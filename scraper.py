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

# 1. KISIM: TVMovie Yapılandırması
TVMOVIE_CHANNELS = {
    "ARD": "ard", "ZDF": "zdf", "RTL": "rtl", 
    "SAT.1": "sat1", "ProSieben": "pro-7", "3sat": "3sat"
}

# 2. KISIM: TVSpielfilm Yedek Kaynak Yapılandırması
TVSPIELFILM_CHANNELS = {
    "ARD": "ARD", "ZDF": "ZDF", "RTL": "RTL", 
    "SAT.1": "SAT1", "ProSieben": "PRO7", "3sat": "3SAT"
}

TIME_RANGE_RE = re.compile(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})")

def fetch_tvmovie(channel_name, slug):
    url = f"https://www.tvmovie.de/tv/sender-{slug}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []
    for a in soup.select('a[href*="-epg-"]'):
        text = " ".join(a.get_text(strip=True).split())
        m = TIME_RANGE_RE.search(text)
        if m:
            entries.append({
                "time": m.group(1),
                "endTime": m.group(2),
                "title": text[:m.start()].strip() or "Program",
                "genre": "TV"
            })
    return entries

def fetch_tvspielfilm(channel_name, slug):
    url = f"https://www.tvspielfilm.de/tv-programm/sendezeiten/{slug},sendungen.html"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []
    # TVSpielfilm tablosundan yayın akışı ayıklama
    for row in soup.select("tr.broadcast-element"):
        time_elem = row.select_one(".time")
        title_elem = row.select_one(".title")
        if time_elem and title_elem:
            time_text = time_elem.get_text(strip=True)
            entries.append({
                "time": time_text,
                "endTime": "--:--", # TVSpielfilm liste görünümünde bitiş saati ayrı hesaplanır
                "title": title_elem.get_text(strip=True),
                "genre": "TV"
            })
    return entries

def main():
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "channels": {}
    }

    for name in TVMOVIE_CHANNELS:
        data = []
        # Birinci Kaynak Denemesi: TVMovie
        try:
            data = fetch_tvmovie(name, TVMOVIE_CHANNELS[name])
        except Exception as e:
            print(f"[UYARI] {name} için TVMovie başarısız: {e}")

        # İkinci Kaynak Denemesi (Fallback): TVSpielfilm
        if not data and name in TVSPIELFILM_CHANNELS:
            try:
                print(f"[YEDEK KAYNAK] {name} için TVSpielfilm çekiliyor...")
                data = fetch_tvspielfilm(name, TVSPIELFILM_CHANNELS[name])
            except Exception as e:
                print(f"[HATA] {name} için TVSpielfilm de başarısız: {e}")

        result["channels"][name] = data

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
