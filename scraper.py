#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timedelta, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

def detect_broadcaster(match_date_utc, league_code):
    if league_code == "bl2":
        return "Sky Sport Bundesliga"
    
    # 1. Bundesliga: Cuma & Pazar = DAZN, Cumartesi & Hafta İçi = Sky
    weekday = match_date_utc.weekday()
    if weekday in [4, 6]:  # Cuma (4) veya Pazar (6)
        return "DAZN 1 / DAZN 2"
    else:                  # Cumartesi (5) ve Hafta İçi
        return "Sky Sport Bundesliga"

def fetch_current_group(league_code):
    """Mevcut bulunulan haftayı tespit eder."""
    url = f"https://api.openligadb.de/getcurrentgroup/{league_code}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("groupOrderID", 1)
    except Exception as e:
        print(f"Mevcut hafta çekilemedi ({league_code}): {e}")
    return 1

def fetch_season_matches(league_code):
    """34 haftalık tüm fikstürü çeker ve haftalara göre gruplar."""
    # En güncel sezon verisi (2025/2026 Sezonu için)
    url = f"https://api.openligadb.de/getmatchdata/{league_code}/2025"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    
    if resp.status_code != 200 or not resp.json():
        # Yedek sorgu: Sezon belirtmeden dene
        url = f"https://api.openligadb.de/getmatchdata/{league_code}"
        resp = requests.get(url, headers=HEADERS, timeout=15)

    data = resp.json() if resp.status_code == 200 else []
    
    matchdays = {}

    for m in data:
        group_id = m.get("group", {}).get("groupOrderID", 1)
        group_name = m.get("group", {}).get("groupName", f"{group_id}. Spieltag")
        
        raw_date = m.get("matchDateTimeUTC")
        if raw_date:
            dt_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            dt_tr = dt_utc + timedelta(hours=3)
            time_tr = dt_tr.strftime("%H:%M")
            date_tr = dt_tr.strftime("%d.%m.%Y")
        else:
            dt_utc = datetime.now(timezone.utc)
            time_tr = "Belli Değil"
            date_tr = "Tarih Netleşmedi"

        team1 = m.get("team1", {}).get("teamName", "")
        team2 = m.get("team2", {}).get("teamName", "")

        is_finished = m.get("matchIsFinished", False)
        results = m.get("matchResults", [])
        score = "vs"
        if results:
            final_res = results[-1]
            score = f"{final_res.get('pointsTeam1')} - {final_res.get('pointsTeam2')}"

        sofascore_search = f"https://www.sofascore.com/search?q={team1}+{team2}"
        kicker_search = f"https://www.google.de/search?q=site:kicker.de+{team1}+{team2}+live+ticker"

        match_obj = {
            "match_id": m.get("matchID"),
            "team1": team1,
            "team2": team2,
            "time_tr": time_tr,
            "date_tr": date_tr,
            "score": score,
            "is_finished": is_finished,
            "broadcaster": detect_broadcaster(dt_utc, league_code),
            "sofascore_url": sofascore_search,
            "kicker_url": kicker_search
        }

        if group_id not in matchdays:
            matchdays[group_id] = {
                "group_name": group_name,
                "matches": []
            }
        matchdays[group_id]["matches"].append(match_obj)

    return matchdays

def main():
    print("Bundesliga tüm haftaların fikstür verileri çekiliyor...")
    
    curr_b1 = fetch_current_group("bl1")
    curr_b2 = fetch_current_group("bl2")

    b1_data = fetch_season_matches("bl1")
    b2_data = fetch_season_matches("bl2")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_str": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "current_b1_week": curr_b1,
        "current_b2_week": curr_b2,
        "bundesliga_1": b1_data,
        "bundesliga_2": b2_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("epg.json başarıyla güncellendi.")

if __name__ == "__main__":
    main()
