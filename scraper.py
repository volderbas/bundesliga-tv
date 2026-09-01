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
    
    weekday = match_date_utc.weekday()
    if weekday in [4, 6]:
        return "DAZN 1 / DAZN 2"
    else:
        return "Sky Sport Bundesliga"

def fetch_current_group(league_code):
    url = f"https://api.openligadb.de/getcurrentgroup/{league_code}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("groupOrderID", 1)
    except Exception:
        pass
    return 1

def fetch_season_matches(league_code):
    url = f"https://api.openligadb.de/getmatchdata/{league_code}/2026"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    
    if resp.status_code != 200 or not resp.json():
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
            time_tr = "TBD"
            date_tr = "TBD"

        team1 = m.get("team1", {}).get("teamName", "")
        team2 = m.get("team2", {}).get("teamName", "")
        match_id = m.get("matchID")

        is_finished = m.get("matchIsFinished", False)
        results = m.get("matchResults", [])
        score = "vs"
        if results:
            final_res = results[-1]
            score = f"{final_res.get('pointsTeam1')} - {final_res.get('pointsTeam2')}"

        # Arama motoru linki YERİNE direkt canlı veri simülatörü & widget bağlantısı
        direct_data_url = f"https://www.openligadb.de/daten/match-detail/{match_id}"

        match_obj = {
            "match_id": match_id,
            "team1": team1,
            "team2": team2,
            "time_tr": time_tr,
            "date_tr": date_tr,
            "score": score,
            "is_finished": is_finished,
            "broadcaster": detect_broadcaster(dt_utc, league_code),
            "data_url": direct_data_url
        }

        if group_id not in matchdays:
            matchdays[group_id] = {
                "group_name": group_name,
                "matches": []
            }
        matchdays[group_id]["matches"].append(match_obj)

    return matchdays

def main():
    curr_b1 = fetch_current_group("bl1")
    curr_b2 = fetch_current_group("bl2")

    b1_data = fetch_season_matches("bl1")
    b2_data = fetch_season_matches("bl2")

    output = {
        "date_str": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "current_b1_week": curr_b1,
        "current_b2_week": curr_b2,
        "bundesliga_1": b1_data,
        "bundesliga_2": b2_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
