#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timedelta, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

def detect_broadcaster(match_date_utc, league_code):
    # 2. Bundesliga maçlarının tamamı Sky Sport Bundesliga'dadır.
    if league_code == "bl2":
        return "Sky Sport Bundesliga"
    
    # 1. Bundesliga Almanya Hak Dağılımı:
    # Cuma & Pazar = DAZN, Cumartesi & Hafta İçi = Sky
    weekday = match_date_utc.weekday()
    if weekday in [4, 6]:  # Cuma (4) ve Pazar (6)
        return "DAZN 1 / DAZN 2"
    else:                  # Cumartesi (5) ve Hafta İçi
        return "Sky Sport Bundesliga"

def fetch_bundesliga_data(league_code):
    matches = []
    # OpenLigaDB Canlı Maç ve Fikstür Uç Noktası
    url = f"https://api.openligadb.de/getmatchdata/{league_code}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for m in data:
                raw_date = m.get("matchDateTimeUTC")
                dt_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                # TSİ (UTC+3) Saat Hesaplaması
                dt_tr = dt_utc + timedelta(hours=3)
                
                team1 = m.get("team1", {}).get("teamName", "")
                team2 = m.get("team2", {}).get("teamName", "")

                # Anlık Skor Mantığı
                is_finished = m.get("matchIsFinished", False)
                results = m.get("matchResults", [])
                score = "vs"
                if results:
                    final_res = results[-1]
                    score = f"{final_res.get('pointsTeam1')} - {final_res.get('pointsTeam2')}"

                # Tıklandığında Açılacak Canlı Ticker / SofaScore / Kicker Linkleri
                sofascore_search = f"https://www.sofascore.com/search?q={team1}+{team2}"
                kicker_search = f"https://www.google.de/search?q=site:kicker.de+{team1}+{team2}+live+ticker"

                matches.append({
                    "team1": team1,
                    "team2": team2,
                    "icon1": m.get("team1", {}).get("teamIconUrl"),
                    "icon2": m.get("team2", {}).get("teamIconUrl"),
                    "time_tr": dt_tr.strftime("%H:%M"),
                    "date_tr": dt_tr.strftime("%d.%m.%Y"),
                    "score": score,
                    "is_finished": is_finished,
                    "broadcaster": detect_broadcaster(dt_utc, league_code),
                    "sofascore_url": sofascore_search,
                    "kicker_url": kicker_search
                })
    except Exception as e:
        print(f"{league_code} veri çekme hatası: {e}")
    return matches

def main():
    print("Bundesliga 1 ve 2 Canlı Maç Verileri Çekiliyor...")
    b1_matches = fetch_bundesliga_data("bl1")
    b2_matches = fetch_bundesliga_data("bl2")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_str": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "bundesliga_1": b1_matches,
        "bundesliga_2": b2_matches
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("epg.json başarıyla güncellendi.")

if __name__ == "__main__":
    main()
