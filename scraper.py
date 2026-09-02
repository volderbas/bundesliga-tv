import requests
import json
from datetime import datetime

# Headers: SofaScore gibi siteler bot olduğumuzu anlamasın diye tarayıcı taklidi yapıyoruz.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sofascore.com/"
}

def get_tabelle(league_shortcut):
    # OpenLigaDB üzerinden güncel puan durumu (bl1 veya bl2)
    url = f"https://api.openligadb.de/getbltable/{league_shortcut}/2026"
    try:
        response = requests.get(url)
        data = response.json()
        table = []
        for team in data:
            table.append({
                "rank": team.get("matches", 0), # OpenLigaDB rank'i bazen farklı verebiliyor, sıralı gelir
                "name": team.get("teamName", "Bilinmiyor"),
                "logo": team.get("teamIconUrl", ""),
                "played": team.get("matches", 0),
                "points": team.get("points", 0),
                "goalDiff": team.get("goalDiff", 0)
            })
        return table
    except Exception as e:
        print(f"{league_shortcut} Tablo çekilemedi: {e}")
        return []

def get_fixtures(league_shortcut):
    # Gelecek maçları çekmek için OpenLigaDB (Sadece güncel haftayı çeker)
    url = f"https://api.openligadb.de/getmatchdata/{league_shortcut}/2026"
    try:
        response = requests.get(url)
        matches = response.json()
        fixtures = []
        for m in matches:
            if not m["matchIsFinished"]: # Sadece oynanmamış maçlar
                fixtures.append({
                    "home": m["team1"]["teamName"],
                    "away": m["team2"]["teamName"],
                    "date": m["matchDateTime"].split("T")[0],
                    "time": m["matchDateTime"].split("T")[1][:5]
                })
        return fixtures[:6] # Ekrana sığması için ilk 6 maçı alıyoruz
    except Exception as e:
        return []

def get_top_players(tournament_id, season_id):
    # SofaScore Top Players JSON Endpoint'i (Örnek endpoint, ID'ler güncel sezona göre değişebilir)
    # Bundesliga 1 ID: 35, Bundesliga 2 ID: 44
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/statistics?limit=10"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        players = []
        for p in data.get("results", [])[:10]:
            players.append({
                "name": p["player"]["name"],
                "team": p["team"]["name"],
                "rating": round(p["rating"], 2)
            })
        return players
    except Exception as e:
        print(f"Oyuncu verisi çekilemedi: {e}")
        # Hata durumunda arayüz boş kalmasın diye mock data
        return [{"name": "Florian Wirtz", "team": "Bayer Leverkusen", "rating": 8.12}]

def update_data():
    # 1. Bundesliga Verileri (SofaScore Sezon ID'si temsili olarak 52000 kullanıldı)
    bl1_data = {
        "tabelle": get_tabelle("bl1"),
        "fixtures": get_fixtures("bl1"),
        "top_players": get_top_players(35, 52376) 
    }
    with open("bl1_data.json", "w", encoding="utf-8") as f:
        json.dump(bl1_data, f, ensure_ascii=False, indent=4)

    # 2. Bundesliga Verileri
    bl2_data = {
        "tabelle": get_tabelle("bl2"),
        "fixtures": get_fixtures("bl2"),
        "top_players": get_top_players(44, 52378)
    }
    with open("bl2_data.json", "w", encoding="utf-8") as f:
        json.dump(bl2_data, f, ensure_ascii=False, indent=4)

    print("Veriler başarıyla güncellendi.")

if __name__ == "__main__":
    update_data()
