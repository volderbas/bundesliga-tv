#!/usr/bin/env python3
import json
import requests
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"
}

def fetch_basic_matches(league_code):
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
            time_tr, date_tr = "TBD", "TBD"

        team1 = m.get("team1", {}).get("teamName", "")
        team2 = m.get("team2", {}).get("teamName", "")
        
        results = m.get("matchResults", [])
        score = "vs"
        if results:
            final_res = results[-1]
            score = f"{final_res.get('pointsTeam1')} - {final_res.get('pointsTeam2')}"

        events = []
        for g in m.get("goals", []):
            events.append({
                "type": "goal",
                "minute": g.get("matchMinute"),
                "player": g.get("goalGetterName"),
                "score": f"{g.get('scoreTeam1')}-{g.get('scoreTeam2')}"
            })

        # Varsayılan kadro yapısı (Canlı çekim olmadığında gösterilecek örnek yapı)
        lineups = {
            "team1": ["İlk 11 Açıklanmadı"],
            "team2": ["İlk 11 Açıklanmadı"]
        }

        match_obj = {
            "match_id": m.get("matchID"),
            "team1": team1,
            "team2": team2,
            "time_tr": time_tr,
            "date_tr": date_tr,
            "score": score,
            "broadcaster": "Sky Sport / DAZN" if league_code == "bl1" else "Sky Sport",
            "events": events,
            "lineups": lineups
        }

        if group_id not in matchdays:
            matchdays[group_id] = {"group_name": group_name, "matches": []}
        matchdays[group_id]["matches"].append(match_obj)

    return matchdays

def main():
    b1_data = fetch_basic_matches("bl1")
    b2_data = fetch_basic_matches("bl2")

    output = {
        "date_str": datetime.now().strftime("%d.%m.%Y - %H:%M"),
        "current_week": 1,
        "bundesliga_1": b1_data,
        "bundesliga_2": b2_data
    }

    with open("epg.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
