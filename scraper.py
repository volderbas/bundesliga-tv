#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

# 1. KANAL YAPILANDIRMALARI VE AÇIK YEDEK YAYIN LINKLERI (FALLBACK)
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"], "fallback": "https://marlin.ard-m3u8.de/live/ard.m3u8"},
    {"name": "ZDF", "search": ["zdf"], "fallback": "https://zdf-hls-15.akamaized.net/hls/live/2016498/de/veryhigh/master.m3u8"},
    {"name": "RTL", "search": ["rtl"], "fallback": ""},
    {"name": "RTL2", "search": ["rtl2", "rtl 2"], "fallback": ""},
    {"name": "SAT.1", "search": ["sat.1", "sat1"], "fallback": ""},
    {"name": "ProSieben", "search": ["prosieben", "pro7"], "fallback": ""},
    {"name": "3sat", "search": ["3sat"], "fallback": "https://zdf-hls-16.akamaized.net/hls/live/2016499/de/veryhigh/master.m3u8"},
    {"name": "ONE", "search": ["one"], "fallback": "https://marlin.ard-m3u8.de/live/one.m3u8"},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1", "bundesliga 1"], "fallback": ""},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2", "bundesliga 2"], "fallback": ""},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3", "bundesliga 3"], "fallback": ""},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4", "bundesliga 4"], "fallback": ""},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5", "bundesliga 5"], "fallback": ""},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"], "fallback": ""},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"], "fallback": ""}
]

# 2. VAVOO LINKLERINI ALTERNATIF SUNUCUDAN ÇEKME (GEO-BLOCK BYPASS)
def get_vavoo_streams():
    streams = {}
    
    # Doğrudan Vavoo JSON İndeksi (Cloudflare bypass uç noktası)
    vavoo_index_urls = [
        "https://vavoo.to/channels",
        "https://raw.githubusercontent.com/michaz1988/vavoo-m3u/main/vavoo.json"
    ]
    
    # Token Alma Denemesi
    token = ""
    try:
        auth_resp = requests.post("https://vavoo.to/api/box/ping2", json={"box": "12345"}, headers={"User-Agent": "VAVOO/2.6"}, timeout=5)
        if auth_resp.status_code == 200:
            token = auth_resp.json().get("token", "")
    except Exception:
        pass

    for index_url in vavoo_index_urls:
        try:
            url_to_fetch = f"{index_url}?token={token}" if token and "vavoo.to" in index_url else index_url
            resp = requests.get(url_to_fetch, headers={"User-Agent": "VAVOO/2.6"}, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    name = item.get("name", "").lower()
                    stream_url = item.get("url", "")
                    
                    for cfg in CHANNELS_CONFIG:
                        ch_key = cfg["name"]
                        if ch_key in streams:
                            continue
                            
                        if any(s in name for s in cfg["search"]):
                            final_url = f"{stream_url}?token={token}" if token and "?token=" not in stream_url else stream_url
                            streams[ch_key] = final_url
                            break
            if len(streams) > 0:
                break
        except Exception as e:
            print(f"İndeks çekme uyarısı ({index_url}): {e}")

    # Vavoo'da bulunamayan açık kanallara fallback ekle
    for cfg in CHANNELS_CONFIG:
        ch_key = cfg["name"]
        if ch_key not in streams or not streams[ch_key]:
            if cfg["fallback"]:
                streams[ch_key] = cfg["fallback"]

    print(f"Toplam {len(streams)} aktif akış adresi bağlandı.")
    return streams

# 3. TV SPIELFILM EPG VERISI ÇEKME
def parse_epg():
    channels_data = {cfg["name"]: [] for cfg in CHANNELS_CONFIG}
    api_url = "https://live.tvspielfilm.de/static/broadcast/list/aktuell"
    
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            broadcasts = resp.json()
            for item in broadcasts:
                ch_title = item.get("channel", {}).get("title", "").lower()
                prog_title = item.get("title", "")
                start_ts = item.get("timeStart")
                end_ts = item.get("timeEnd")

                if not prog_title:
                    continue

                start_str = datetime.fromtimestamp(start_ts).strftime("%H:%M") if start_ts else "--:--"
                end_str = datetime.fromtimestamp(end_ts).strftime("%H:%M") if end_ts else "--:--"

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
        print(f"EPG çekme hatası: {e}")

    # Boş kalan kanallar için default EPG verisi
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

def main():
    print("Vavoo Akışları Alınıyor...")
    vavoo_streams = get_vavoo_streams()

    print("EPG Verisi Alınıyor...")
    epg_data = parse_epg()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "streams": vavoo_streams,
        "channels": epg_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("İşlem Başarıyla Tamamlandı! epg.json oluşturuldu.")

if __name__ == "__main__":
    main()
