#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Hedef Kanal Yapılandırmaları ve TV Spielfilm ID Eşleşmeleri
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"], "id": "ARD"},
    {"name": "ZDF", "search": ["zdf"], "id": "ZDF"},
    {"name": "RTL", "search": ["rtl"], "id": "RTL"},
    {"name": "RTL2", "search": ["rtl2", "rtl 2", "rtl ii"], "id": "RTL2"},
    {"name": "SAT.1", "search": ["sat.1", "sat1"], "id": "SAT1"},
    {"name": "ProSieben", "search": ["prosieben", "pro7"], "id": "PRO7"},
    {"name": "3sat", "search": ["3sat"], "id": "3SAT"},
    {"name": "ONE", "search": ["one"], "id": "ONE"},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1"], "id": "SKY-B1"},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2"], "id": "SKY-B2"},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3"], "id": "SKY-B3"},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4"], "id": "SKY-B4"},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5"], "id": "SKY-B5"},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"], "id": "DAZN1"},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"], "id": "DAZN2"}
]

# 1. TV SPIELFILM ONAYLI JSON EPG API
def fetch_epg_from_api():
    channels_data = {cfg["name"]: [] for cfg in CHANNELS_CONFIG}
    # TV Spielfilm'in doğrudan mobil/web API uç noktası
    api_url = "https://live.tvspielfilm.de/static/broadcast/list/aktuell"
    
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                ch_title = item.get("channel", {}).get("title", "").lower()
                prog_title = item.get("title", "Program")
                start_ts = item.get("timeStart")
                end_ts = item.get("timeEnd")

                # Zaman formatlama
                start_str = datetime.fromtimestamp(start_ts).strftime("%H:%M") if start_ts else "--:--"
                end_str = datetime.fromtimestamp(end_ts).strftime("%H:%M") if end_ts else "--:--"

                # Eşleşen kanala ekle
                for cfg in CHANNELS_CONFIG:
                    if any(s in ch_title for s in cfg["search"]):
                        channels_data[cfg["name"]].append({
                            "time": start_str,
                            "endTime": end_str,
                            "title": prog_title[:90],
                            "url": f"https://www.tvspielfilm.de/tv-programm/sendung/{item.get('id', '')}.html"
                        })
                        break
    except Exception as e:
        print(f"EPG API Çekme Hatası: {e}")

    # Boş kalan kanalları doldur
    for cfg in CHANNELS_CONFIG:
        ch_name = cfg["name"]
        if not channels_data[ch_name]:
            channels_data[ch_name].append({
                "time": datetime.now().strftime("%H:%M"),
                "endTime": "--:--",
                "title": f"{ch_name} Canlı Yayın",
                "url": "#"
            })
            
    return channels_data

# 2. VAVOO AKIŞ LINKLERI
def fetch_vavoo_streams():
    streams = {}
    try:
        # Vavoo Ana Kanal Listesi
        session = requests.Session()
        session.headers.update({"User-Agent": "VAVOO/2.6"})
        
        # Auth Token Al
        auth = session.post("https://vavoo.to/api/box/ping2", json={"box": "12345"}, timeout=10)
        token = auth.json().get("token", "") if auth.status_code == 200 else ""

        url = f"https://vavoo.to/channels?token={token}" if token else "https://vavoo.to/channels"
        resp = session.get(url, timeout=15)
        
        if resp.status_code == 200:
            vavoo_data = resp.json()
            for ch in vavoo_data:
                name = ch.get("name", "").lower()
                stream_url = ch.get("url", "")
                
                for cfg in CHANNELS_CONFIG:
                    ch_key = cfg["name"]
                    if ch_key in streams:
                        continue
                    if any(s in name for s in cfg["search"]):
                        streams[ch_key] = f"{stream_url}?token={token}" if token and "?token=" not in stream_url else stream_url
                        break
    except Exception as e:
        print(f"Vavoo Yayın Linki Hatası: {e}")

    return streams

def main():
    print("EPG verisi çekiliyor...")
    epg_data = fetch_epg_from_api()

    print("Vavoo canlı yayın linkleri çekiliyor...")
    stream_data = fetch_vavoo_streams()

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "streams": stream_data,
        "channels": epg_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("epg.json başarıyla güncellendi.")

if __name__ == "__main__":
    main()
