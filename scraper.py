import json
import requests
from datetime import datetime

def run_scraper():
    leagues = {
        "bl1": "bl1",
        "bl2": "bl2"
    }

    for league_key, league_code in leagues.items():
        print(f"[{league_key.upper()}] OpenLigaDB verileri çekiliyor...")
        
        # 1. Aktif Haftayı Bul
        current_week = 1
        try:
            curr_res = requests.get(f"https://api.openligadb.de/getcurrentgroup/{league_code}", timeout=10).json()
            current_week = curr_res.get('groupOrderID', 1)
        except Exception as e:
            print(f"Aktif hafta çekilemedi: {e}")

        # 2. Bütün Sezonun Maçlarını Tek İstekte Çek (34 Hafta)
        spieltage = {}
        try:
            matches_res = requests.get(f"https://api.openligadb.de/getmatchdata/{league_code}", timeout=10).json()
            
            for m in matches_res:
                group_id = str(m.get('group', {}).get('groupOrderID', 1))
                if group_id not in spieltage:
                    spieltage[group_id] = []

                home_team = m.get('team1', {}).get('teamName', '')
                away_team = m.get('team2', {}).get('teamName', '')
                is_finished = m.get('isMatchFinished', False)

                # Skor
                score_str = ""
                results = m.get('matchResults', [])
                final_res = next((r for r in results if r.get('resultName') == "Endergebnis"), None)
                if not final_res and results:
                    final_res = results[-1]
                
                if is_finished and final_res:
                    score_str = f"{final_res.get('pointsTeam1', 0)} - {final_res.get('pointsTeam2', 0)}"

                # Tarih ve Saat
                match_date_raw = m.get('matchDateTime', '')
                date_val, time_val = "", ""
                if match_date_raw:
                    try:
                        dt = datetime.fromisoformat(match_date_raw.replace('Z', '+00:00'))
                        date_val = dt.strftime('%Y-%m-%d')
                        time_val = dt.strftime('%H:%M')
                    except Exception:
                        pass

                # Gol Atanlar
                goals = []
                for g in m.get('goals', []):
                    minute = f"{g.get('matchMinute', '')}'" if g.get('matchMinute') else ""
                    scorer = g.get('goalGetterName', '')
                    if scorer:
                        goals.append(f"{minute} {scorer}".strip())

                spieltage[group_id].append({
                    "id": m.get('matchID'),
                    "home": home_team,
                    "away": away_team,
                    "score": score_str,
                    "status": "FINISHED" if is_finished else "SCHEDULED",
                    "date": date_val,
                    "time": time_val,
                    "goals": goals,
                    "cards": [],
                    "lineups": {"home": [], "away": []}
                })
        except Exception as e:
            print(f"Maçlar çekilirken hata: {e}")

        # 3. Puan Durumu (Tabelle)
        tabelle = []
        try:
            current_year = datetime.now().year
            table_res = requests.get(f"https://api.openligadb.de/getbltable/{league_code}/{current_year}", timeout=10).json()
            for entry in table_res:
                tabelle.append({
                    "name": entry.get('teamName', ''),
                    "points": entry.get('points', 0),
                    "goalDiff": entry.get('goalDiff', 0)
                })
        except Exception as e:
            print(f"Puan durumu çekilirken hata: {e}")

        output_data = {
            "current_spieltag": current_week,
            "spieltage": spieltage,
            "tabelle": tabelle
        }

        with open(f"{league_key}_data.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"[{league_key.upper()}] İşlem tamam! {len(spieltage)} adet hafta yüklendi.")

if __name__ == "__main__":
    run_scraper()
