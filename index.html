#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Takip Edeceğimiz Kanallar ve TV Spielfilm Kanal Kodları
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"]},
    {"name": "ZDF", "search": ["zdf"]},
    {"name": "RTL", "search": ["rtl"]},
    {"name": "RTL2", "search": ["rtl2", "rtl 2"]},
    {"name": "SAT.1", "search": ["sat.1", "sat1"]},
    {"name": "ProSieben", "search": ["prosieben", "pro7"]},
    {"name": "3sat", "search": ["3sat"]},
    {"name": "ONE", "search": ["one"]},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1", "bundesliga 1"]},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2", "bundesliga 2"]},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3", "bundesliga 3"]},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4", "bundesliga 4"]},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5", "bundesliga 5"]},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"]},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"]}
]

def fetch_epg():
    epg_result = {cfg["name"]: [] for cfg in CHANNELS_CONFIG}
    
    # TV Spielfilm Canlı Yayın Akış Uç Noktası
    url = "https://live.tvspielfilm.de/static/broadcast/list/aktuell"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            broadcasts = response.json()
            
            for item in broadcasts:
                channel_name = item.get("channel", {}).get("title", "").lower()
                title = item.get("title", "").strip()
                start_ts = item.get("timeStart")
                end_ts = item.get("timeEnd")
                broadcast_id = item.get("id", "")

                if not title:
                    continue

                # Zaman Dönüştürme
                start_time = datetime.fromtimestamp(start_ts).strftime("%H:%M") if start_ts else "--:--"
                end_time = datetime.fromtimestamp(end_ts).strftime("%H:%M") if end_ts else "--:--"

                # TV Spielfilm Detay Sayfası Linki
                detail_url = f"https://www.tvspielfilm.de/tv-programm/sendung/{broadcast_id}.html" if broadcast_id else "https://www.tvspielfilm.de/"

                # Kanal Eşleştirme
                for cfg in CHANNELS_CONFIG:
                    ch_key = cfg["name"]
                    if any(term in channel_name for term in cfg["search"]):
                        epg_result[ch_key].append({
                            "time": start_time,
                            "endTime": end_time,
                            "title": title,
                            "url": detail_url
                        })
                        break
    except Exception as e:
        print(f"EPG çekilirken hata oluştu: {e}")

    # Yayın akışı bulunamayan kanallara varsayılan yönlendirme linki atama
    now_str = datetime.now().strftime("%H:%M")
    for cfg in CHANNELS_CONFIG:
        ch_name = cfg["name"]
        if not epg_result[ch_name]:
            epg_result[ch_name].append({
                "time": now_str,
                "endTime": "--:--",
                "title": f"{ch_name} Program Detayı İçin Tıklayın",
                "url": "https://www.tvspielfilm.de/tv-programm/"
            })

    return epg_result

def main():
    print("Yayın akışları güncelleniyor...")
    epg_data = fetch_epg()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "streams": {},  # Canlı yayınlar devreden çıkarıldı
        "channels": epg_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("epg.json başarıyla güncellendi.")

if __name__ == "__main__":
    main()
