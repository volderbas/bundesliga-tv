#!/usr/bin/env python3
import json
import re
import sys
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*"
}

# 1. TV SPIELFILM EPG HEDEF KANALLAR
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"], "vavoo": "ARD"},
    {"name": "ZDF", "search": ["zdf"], "vavoo": "ZDF"},
    {"name": "RTL", "search": ["rtl"], "vavoo": "RTL"},
    {"name": "RTL2", "search": ["rtl2", "rtl 2", "rtl ii"], "vavoo": "RTL 2"},
    {"name": "SAT.1", "search": ["sat.1", "sat1"], "vavoo": "SAT.1"},
    {"name": "ProSieben", "search": ["prosieben", "pro7"], "vavoo": "ProSieben"},
    {"name": "3sat", "search": ["3sat"], "vavoo": "3sat"},
    {"name": "ONE", "search": ["one"], "vavoo": "ONE"},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1", "sky bundesliga 1"], "vavoo": "Sky Sport Bundesliga 1"},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2", "sky bundesliga 2"], "vavoo": "Sky Sport Bundesliga 2"},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3", "sky bundesliga 3"], "vavoo": "Sky Sport Bundesliga 3"},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4", "sky bundesliga 4"], "vavoo": "Sky Sport Bundesliga 4"},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5", "sky bundesliga 5"], "vavoo": "Sky Sport Bundesliga 5"},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"], "vavoo": "DAZN 1"},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"], "vavoo": "DAZN 2"}
]

TARGET_URLS = [
    "https://www.tvspielfilm.de/tv-programm/sendungen/jetzt.html",
    "https://www.tvspielfilm.de/tv-programm/sendungen/sport.html",
    "https://www.tvspielfilm.de/tv-programm/sendungen/pay-tv.html"
]

# 2. VAVOO CANLI YAYIN LINKLERINI OTOMATIK ÇEKME FONKSIYONU
def get_vavoo_streams():
    stream_map = {}
    try:
        # Vavoo Oturum (Session Token) Alma
        auth_resp = requests.post(
            "https://vavoo.to/api/box/ping2",
            json={"box": "12345"},
            headers={"User-Agent": "VAVOO/2.6"},
            timeout=10
        )
        token = auth_resp.json().get("token", "") if auth_resp.status_code == 200 else ""
        
        # Almanya Kanal Listesini Çekme
        channels_url = f"https://vavoo.to/channels?token={token}" if token else "https://vavoo.to/channels"
        resp = requests.get(channels_url, headers={"User-Agent": "VAVOO/2.6"}, timeout=15)
        
        if resp.status_code == 200:
            vavoo_list = resp.json()
            for ch in vavoo_list:
                country = ch.get("country", "").upper()
                name = ch.get("name", "").strip()
                url = ch.get("url", "")
                
                # Sadece Almanya kanallarına odaklan
                if country == "GERMANY" or country == "DE":
                    for cfg in CHANNELS_CONFIG:
                        target = cfg["name"].lower()
                        # Kanal ismi eşleşmesi denetimi
                        if name.lower() == target or cfg["vavoo"].lower() in name.lower():
                            # Dinamik token eklenmiş m3u8 linkini kaydet
                            stream_map[cfg["name"]] = f"{url}?token={token}" if token and "?token=" not in url else url
                            break
        print(f"Vavoo: Toplam {len(stream_map)} kanal akış linki başarıyla üretildi.")
    except Exception as e:
        print(f"Vavoo API akışları çekilirken bir uyarı oluştu: {e}")
    
    return stream_map

# 3. EPG VERISINI TV SPIELFILM ÜZERİNDEN TOPLAMA
def parse_epg(channels_data):
    for url in TARGET_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("tr, .broadcast-list-item, .tv-guide-channel, article, div[class*='broadcast']")

            for row in rows:
                row_text = row.get_text(" ", strip=True)
                row_text_lower = row_text.lower()

                matched_channel = None
                for cfg in CHANNELS_CONFIG:
                    for keyword in cfg["search"]:
                        if keyword in row_text_lower:
                            matched_channel = cfg["name"]
                            break
                    if matched_channel:
                        break

                if not matched_channel:
                    continue

                time_match = re.search(r"(\d{2}:\d{2})\s*[-–]?\s*(\d{2}:\d{2})?", row_text)
                if not time_match:
                    continue

                start_time = time_match.group(1)
                end_time = time_match.group(2) if time_match.group(2) else "--:--"

                title_elem = row.select_one("a[title], .title, strong, h3, h4, .broadcast-title")
                title = title_elem.get_text(strip=True) if title_elem else "Program Bilgisi"

                genres = ["REPORTAGE", "SERIE", "UNTERHALTUNG", "KINDER", "SPORT", "DOKU-SOAP", "MAGAZIN", "NACHRICHTEN", "DOKU", "LIVE"]
                for g in genres:
                    if title.upper().startswith(g):
                        title = title[len(g):].strip()

                href = title_elem.get("href", "#") if title_elem else "#"
                detail_url = href if href.startswith("http") else f"https://www.tvspielfilm.de{href}" if href != "#" else "#"

                exists = any(item['title'] == title and item['time'] == start_time for item in channels_data[matched_channel])
                if not exists:
                    channels_data[matched_channel].append({
                        "time": start_time,
                        "endTime": end_time,
                        "title": title[:90],
                        "url": detail_url
                    })
        except Exception as e:
            print(f"EPG çekilirken bir hata oluştu ({url}): {e}")

def main():
    print("Vavoo Canlı Akış Linkleri Alınıyor...")
    vavoo_streams = get_vavoo_streams()

    channels_data = {item["name"]: [] for item in CHANNELS_CONFIG}
    print("TV Spielfilm EPG Verileri Çekiliyor...")
    parse_epg(channels_data)

    # Verisi eksik kanallar için varsayılan yapılandırma
    for cfg in CHANNELS_CONFIG:
        ch_name = cfg["name"]
        if not channels_data[ch_name]:
            channels_data[ch_name].append({
                "time": "--:--",
                "endTime": "--:--",
                "title": f"{ch_name} Canlı Yayın",
                "url": "#"
            })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "streams": vavoo_streams,  # Otomatik çekilen canlı m3u8 adresleri
        "channels": channels_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("İşlem Başarıyla Tamamlandı! epg.json oluşturuldu.")

if __name__ == "__main__":
    main()
