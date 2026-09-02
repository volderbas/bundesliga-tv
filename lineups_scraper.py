"""
Sofascore'dan resmi (confirmed) ilk 11 verisi çekme — curl_cffi ile.
pip install curl_cffi
"""
from curl_cffi import requests as cf_requests
import json
import time
import sys
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
}

BUNDESLIGA_1_ID = 35
BUNDESLIGA_2_ID = 44  # sofascore.com/de/football/tournament/germany/2-bundesliga/44

_session = cf_requests.Session(impersonate="chrome131", headers=HEADERS)


def warm_up():
    """Once normal bir tarayıcı gibi önce ana sayfayı ziyaret et — bazı
    Cloudflare kurallarında doğrudan API'ye gitmek şüpheli görünüyor,
    önce çerez/oturum almak engellenme ihtimalini azaltıyor."""
    try:
        _session.get("https://www.sofascore.com/", timeout=15)
        time.sleep(1)
    except Exception as e:
        print(f"[uyarı] warm-up başarısız (önemli değil, devam ediliyor): {e}")


def sofa_get(path: str, retries: int = 3):
    url = f"https://api.sofascore.com/api/v1/{path}"
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = _session.get(url, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            print(f"  [deneme {attempt}/{retries}] {path} -> {e}")
            time.sleep(2 * attempt)
    raise last_err


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
    try:
        warm_up()
        for league_name, tid in [("Bundesliga", BUNDESLIGA_1_ID), ("2. Bundesliga", BUNDESLIGA_2_ID)]:
            try:
                matches = get_todays_matches(tid)
            except Exception as e:
                print(f"[hata] {league_name} maç listesi alınamadı: {e}")
                continue
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
                    print(f"  henüz açıklanmadı / alınamadı: {key}")
    except Exception as e:
        # Sofascore tamamen engellemiş olabilir (403 vb.) — workflow'un
        # geri kalanını (özellikle push adımını) bozmayalım, sadece uyar.
        print(f"[UYARI] lineup scraping genel olarak başarısız: {e}")

    if all_results:
        with open("lineups.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\nYazıldı: lineups.json ({len(all_results)} maç)")
    else:
        print("\n[bilgi] Hiçbir maçta resmi ilk 11 alınamadı — lineups.json'a dokunulmadı.")

    # Bu script başarısız olsa bile workflow'daki diğer adımlar (özellikle
    # epg.json push'u) çalışmaya devam etsin diye her zaman 0 ile çık.
    sys.exit(0)
