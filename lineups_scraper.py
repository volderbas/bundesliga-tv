"""
Sofascore'dan resmi (confirmed) ilk 11 verisi çekme — curl_cffi ile.
pip install curl_cffi
"""
from curl_cffi import requests as cf_requests
import json
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
}

BUNDESLIGA_1_ID = 35
BUNDESLIGA_2_ID = 44  # sofascore.com/de/football/tournament/germany/2-bundesliga/44

def sofa_get(path: str):
    url = f"https://api.sofascore.com/api/v1/{path}"
    # impersonate="chrome124" -> TLS/JA3 parmak izini Chrome ile aynı yapar,
    # Cloudflare'in bot tespitini bu sayede atlatıyoruz.
    r = cf_requests.get(url, headers=HEADERS, impersonate="chrome124", timeout=15)
    r.raise_for_status()
    return r.json()


def get_todays_matches(tournament_id: int, date_str: str = None):
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    data = sofa_get(f"sport/football/scheduled-events/{date_str}")
    return [
        ev for ev in data.get("events", [])
        if ev.get("tournament", {}).get("uniqueTournament", {}).get("id") == tournament_id
    ]


def get_confirmed_lineup(event_id: int):
    data = sofa_get(f"event/{event_id}/lineups")
    if not data.get("confirmed"):
        return None  # henüz resmiyet kazanmamış -> hiç kaydetme, istemiyorsun
    def simplify(side):
        return [
            {
                "name": p["player"]["name"],
                "position": p.get("position"),
                "shirtNumber": p.get("shirtNumber"),
            }
            for p in data[side]["players"] if p.get("substitute") is False
        ]
    return {
        "home": simplify("home"),
        "away": simplify("away"),
        "homeFormation": data["home"].get("formation"),
        "awayFormation": data["away"].get("formation"),
    }


if __name__ == "__main__":
    all_results = {}
    for league_name, tid in [("Bundesliga", BUNDESLIGA_1_ID), ("2. Bundesliga", BUNDESLIGA_2_ID)]:
        matches = get_todays_matches(tid)
        print(f"\n{league_name}: bugün {len(matches)} maç")
        for m in matches:
            eid = m["id"]
            try:
                lineup = get_confirmed_lineup(eid)
            except Exception as e:
                print(f"  [hata] event {eid}: {e}")
                lineup = None
            key = f'{m["homeTeam"]["name"]} - {m["awayTeam"]["name"]}'
            if lineup:
                all_results[key] = {**lineup, "league": league_name}
                print(f"  OK: {key}")
            else:
                print(f"  henüz açıklanmadı: {key}")

    # mevcut lineups.json'u boş sonuçla ezme -- en az 1 maç varsa yaz
    if all_results:
        with open("lineups.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\nYazıldı: lineups.json ({len(all_results)} maç)")
    else:
        print("\n[bilgi] Hiçbir maçta resmi ilk 11 açıklanmamış — lineups.json'a dokunulmadı.")
