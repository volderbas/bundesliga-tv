#!/usr/bin/env python3
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

# 1. HEDEF KANAL LİSTESİ VE EPG EŞLEŞTİRME TERİMLERİ
CHANNELS_CONFIG = [
    {"name": "ARD", "search": ["ard", "das erste"]},
    {"name": "ZDF", "search": ["zdf"]},
    {"name": "RTL", "search": ["rtl"]},
    {"name": "RTL2", "search": ["rtl2", "rtl 2", "rtl ii"]},
    {"name": "SAT.1", "search": ["sat.1", "sat1"]},
    {"name": "ProSieben", "search": ["prosieben", "pro7"]},
    {"name": "3sat", "search": ["3sat"]},
    {"name": "ONE", "search": ["one"]},
    {"name": "Sky Sport Bundesliga 1", "search": ["sky sport bundesliga 1", "sky buli 1", "sky sport 1"]},
    {"name": "Sky Sport Bundesliga 2", "search": ["sky sport bundesliga 2", "sky buli 2"]},
    {"name": "Sky Sport Bundesliga 3", "search": ["sky sport bundesliga 3", "sky buli 3"]},
    {"name": "Sky Sport Bundesliga 4", "search": ["sky sport bundesliga 4", "sky buli 4"]},
    {"name": "Sky Sport Bundesliga 5", "search": ["sky sport bundesliga 5", "sky buli 5"]},
    {"name": "DAZN 1", "search": ["dazn 1", "dazn1"]},
    {"name": "DAZN 2", "search": ["dazn 2", "dazn2"]}
]

# 2. AÇIK EPG / XMLTV VERİ KAYNAKLARI (AÇIK ALMAN TV VERİTABANLARI)
EPG_SOURCES = [
    "https://iptv-org.github.io/epg/guides/de/tvspielfilm.de.epg.xml",
    "https://raw.githubusercontent.com/iptv-org/epg/master/guides/de/tvtv.de.epg.xml"
]

def fetch_open_epg():
    channels_data = {cfg["name"]: [] for cfg in CHANNELS_CONFIG}
    now_utc = datetime.now(timezone.utc)
    
    xml_raw = None
    for src in EPG_SOURCES:
        try:
            resp = requests.get(src, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                xml_raw = resp.text
                print(f"EPG Verisi başarıyla çekildi: {src}")
                break
        except Exception as e:
            print(f"Kaynak erişim uyarısı ({src}): {e}")

    if not xml_raw:
        print("EPG kaynaklarına ulaşılamadı. Varsayılan şablon yükleniyor.")
        return fallback_epg(channels_data)

    try:
        root = ET.fromstring(xml_raw)
        
        # XML üzerindeki kanal ID'lerini eşleştir
        channel_map = {}
        for channel in root.findall("channel"):
            ch_id = channel.get("id", "")
            display_name = ""
            name_elem = channel.find("display-name")
            if name_elem is not None and name_elem.text:
                display_name = name_elem.text.lower()
            
            for cfg in CHANNELS_CONFIG:
                if any(term in ch_id.lower() or term in display_name for term in cfg["search"]):
                    channel_map[ch_id] = cfg["name"]

        # Program verilerini tara
        for programme in root.findall("programme"):
            ch_id = programme.get("channel", "")
            if ch_id in channel_map:
                ch_name = channel_map[ch_id]
                
                # Sadece ilk 2 programı al (çok dolmasın)
                if len(channels_data[ch_name]) >= 2:
                    continue

                start_raw = programme.get("start", "")
                end_raw = programme.get("stop", "")
                title_elem = programme.find("title")
                title = title_elem.text if title_elem is not None else "Program"

                # XMLZamanı Formatlama: 20260901140000 +0000
                start_time = parse_xml_time(start_raw)
                end_time = parse_xml_time(end_raw)

                channels_data[ch_name].append({
                    "time": start_time,
                    "endTime": end_time,
                    "title": title,
                    "url": f"https://www.google.de/search?q={ch_name}+{title}+tv+programm"
                })

    except Exception as e:
        print(f"XML Ayrıştırma Hatası: {e}")

    return fallback_epg(channels_data)

def parse_xml_time(time_str):
    try:
        if len(time_str) >= 12:
            hour = time_str[8:10]
            minute = time_str[10:12]
            return f"{hour}:{minute}"
    except Exception:
        pass
    return "--:--"

def fallback_epg(channels_data):
    now_str = datetime.now().strftime("%H:%M")
    for cfg in CHANNELS_CONFIG:
        ch_name = cfg["name"]
        if not channels_data[ch_name]:
            channels_data[ch_name].append({
                "time": now_str,
                "endTime": "--:--",
                "title": f"{ch_name} Güncel Yayın Akışı",
                "url": f"https://www.google.de/search?q={ch_name}+tv+programm+heute"
            })
    return channels_data

def main():
    print("Açık EPG Veri Havuzları Taranıyor...")
    epg_data = fetch_open_epg()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "streams": {},
        "channels": epg_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("epg.json başarıyla oluşturuldu ve güncellendi.")

if __name__ == "__main__":
    main()
