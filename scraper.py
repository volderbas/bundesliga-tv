#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

# 1. KANAL LISTESI VE AÇIK RESMI AKIŞLAR
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"], "stream": "https://marlin.ard-m3u8.de/live/ard.m3u8"},
    {"name": "ZDF", "search": ["zdf"], "stream": "https://zdf-hls-15.akamaized.net/hls/live/2016498/de/veryhigh/master.m3u8"},
    {"name": "RTL", "search": ["rtl"], "stream": ""},
    {"name": "RTL2", "search": ["rtl2", "rtl 2"], "stream": ""},
    {"name": "SAT.1", "search": ["sat.1", "sat1"], "stream": ""},
    {"name": "ProSieben", "search": ["prosieben", "pro7"], "stream": ""},
    {"name": "3sat", "search": ["3sat"], "stream": "https://zdf-hls-16.akamaized.net/hls/live/2016499/de/veryhigh/master.m3u8"},
    {"name": "ONE", "search": ["one"], "stream": "https://marlin.ard-m3u8.de/live/one.m3u8"},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1"], "stream": ""},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2"], "stream": ""},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3"], "stream": ""},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4"], "stream": ""},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5"], "stream": ""},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"], "stream": ""},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"], "stream": ""}
]

# 2. DİNAMİK CANLI AKIŞ LİNKLERİNİ TOPLAMA
def get_streams():
    streams = {}
    
    # 1. Öncelik: Tanımlı açık resmi linkler (ARD, ZDF, 3sat, ONE)
    for cfg in CHANNELS_CONFIG:
        if cfg["stream"]:
            streams[cfg["name"]] = cfg["stream"]

    # 2. Öncelik: Vavoo/IPTV Açık Yayın Havuzu (Sky, DAZN, RTL, SAT1 vb. için)
    try:
        # GitHub engeline takılmayan güncel IPTV/Vavoo M3U JSON havuzu
        resp = requests.get("https://raw.githubusercontent.com/iptv-org/iptv/master/streams/de.json", timeout=10)
        if resp.status_code == 200:
            iptv_data = resp.json()
            for item in iptv_data:
                channel_id = item.get("channel", "").lower()
                url = item.get("url", "")
                
                for cfg in CHANNELS_CONFIG:
                    ch_key = cfg["name"]
                    if ch_key in streams:
                        continue
                    if any(s in channel_id for s in cfg["search"]):
                        streams[ch_key] = url
                        break
    except Exception as e:
        print(f"IPTV havuzu çekilemedi: {e}")

    return streams

# 3. TV SPIELFILM KAZIMA (HTML PARSER) - TAM PROGRAM AKIŞI
def get_epg():
    channels_data = {cfg["name"]: [] for cfg in CHANNELS_CONFIG}
    
    # TV Spielfilm ana yayın akışı sayfası
    url = "https://www.tvspielfilm.de/tv-programm/sendezeiten/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            # HTML içeriğini basit re ile tarayarak program saatlerini ve adlarını çek
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Kanal satırlarını bul
            rows = soup.find_all("tr")
            for row in rows:
                text = row.get_text(" ", strip=True)
                text_lower = text.lower()
                
                for cfg in CHANNELS_CONFIG:
                    ch_key = cfg["name"]
                    if any(s in text_lower for s in cfg["search"]):
                        # Başlık ve saat bilgisini ayıkla
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            time_str = cols[0].get_text(strip=True)
                            title_str = cols[1].get_text(strip=True)
                            
                            if ":" in time_str:
                                channels_data[ch_key].append({
                                    "time": time_str[:5],
                                    "endTime": "--:--",
                                    "title": title_str[:80],
                                    "url": "https://www.tvspielfilm.de/tv-programm/"
                                })
    except Exception as e:
        print(f"EPG çekme hatası: {e}")

    # Eksik kalan kanallara güncel saat ile varsayılan bilgi ver
    now_str = datetime.now().strftime("%H:%M")
    for cfg in CHANNELS_CONFIG:
        ch_name = cfg["name"]
        if not channels_data[ch_name]:
            channels_data[ch_name].append({
                "time": now_str,
                "endTime": "--:--",
                "title": f"{ch_name} Canlı Yayın Akışı",
                "url": "https://www.tvspielfilm.de/tv-programm/"
            })

    return channels_data

def main():
    print("Akış linkleri toplanıyor...")
    streams = get_streams()

    print("EPG verisi güncelleniyor...")
    epg = get_epg()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "streams": streams,
        "channels": epg
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("epg.json başarıyla kaydedildi!")

if __name__ == "__main__":
    main()
