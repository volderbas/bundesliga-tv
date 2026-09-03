import json
import requests

def get_match_details(league_code, event_id):
    """Maçın gollerini, kartlarını ve ilk 11 / oyuncu değişikliklerini çeker."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/summary?event={event_id}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return {}, [], []
        data = res.json()
        
        goals = []
        cards = []
        
        # Olaylar (Goller, Kartlar, Değişiklikler)
        for event in data.get('keyEvents', []):
            clock = event.get('clock', {}).get('displayValue', '')
            text = event.get('text', '')
            event_type = event.get('type', {}).get('text', '').lower()
            
            if 'goal' in event_type:
                goals.append(f"{clock}' {text}")
            elif 'card' in event_type:
                card_type = "🟨" if "yellow" in event_type or "yellow" in text.lower() else "🟥"
                cards.append(f"{clock}' {card_type} {text}")

        # Kadrolar ve Oyuncu Değişiklikleri
        lineups = {"home": [], "away": []}
        rosters = data.get('rosters', [])
        
        for idx, team_key in enumerate(["home", "away"]):
            if idx < len(rosters):
                team_roster = rosters[idx]
                for athlete_entry in team_roster.get('roster', []):
                    athlete = athlete_entry.get('athlete', {})
                    name = athlete.get('displayName', '')
                    starter = athlete_entry.get('starter', False)
                    subbed_out = athlete_entry.get('subbedOut', False)
                    
                    if starter:
                        sub_info = ""
                        # Oyuncu çıktıysa yerine gireni bul
                        if subbed_out:
                            sub_events = [e for e in data.get('keyEvents', []) if e.get('type', {}).get('text', '').lower() == 'substitution']
                            for sub in sub_events:
                                if athlete.get('id') in str(sub):
                                    clock = sub.get('clock', {}).get('displayValue', '')
                                    sub_info = f" (🔄 {clock}' Çıktı)"
                        lineups[team_key].append(f"{name}{sub_info}")

        return lineups, goals, cards
    except Exception as e:
        print(f"Maç detay hatası ({event_id}): {e}")
        return {}, [], []

def run_scraper():
    leagues = {
        "bl1": "ger.1",
        "bl2": "ger.2"
    }

    for league_key, league_code in leagues.items():
        print(f"[{league_key.upper()}] Verileri çekiliyor...")
        
        # 1. Fikstür ve Maçlar
        scoreboard_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        res = requests.get(scoreboard_url)
        sb_data = res.json()
        
        current_week = sb_data.get('week', {}).get('number', 1)
        events = sb_data.get('events', [])
        
        matches_by_week = {}
        current_matches = []

        for event in events:
            event_id = event.get('id')
            competition = event.get('competitions', [{}])[0]
            status = event.get('status', {}).get('type', {}).get('state', '')
            
            home_team = competition['competitors'][0]['team']['displayName']
            away_team = competition['competitors'][1]['team']['displayName']
            
            score_str = ""
            if status in ['post', 'in']: # Oynandı veya Oynanıyor
                home_score = competition['competitors'][0].get('score', '0')
                away_score = competition['competitors'][1].get('score', '0')
                score_str = f"{home_score} - {away_score}"
            
            date_time = competition.get('date', '').split('T')
            date_val = date_time[0] if len(date_time) > 0 else ""
            time_val = date_time[1][:5] if len(date_time) > 1 else ""

            # Detaylı veri çekme (Sadece oynanmış veya başlayan maçlar için)
            lineups, goals, cards = {}, [], []
            if status in ['post', 'in']:
                lineups, goals, cards = get_match_details(league_code, event_id)

            match_data = {
                "id": event_id,
                "home": home_team,
                "away": away_team,
                "score": score_str,
                "status": status,
                "date": date_val,
                "time": time_val,
                "goals": goals,
                "cards": cards,
                "lineups": lineups
            }
            current_matches.append(match_data)

        matches_by_week[str(current_week)] = current_matches

        # 2. Puan Durumu (Tabelle)
        standings_url = f"https://site.api.espn.com/apis/v2/sports/soccer/{league_code}/standings"
        std_res = requests.get(standings_url).json()
        
        tabelle = []
        try:
            entries = std_res['children'][0]['standings']['entries']
            for entry in entries:
                team_name = entry['team']['displayName']
                stats = {s['name']: s['displayValue'] for s in entry['stats']}
                tabelle.append({
                    "name": team_name,
                    "points": stats.get('points', '0'),
                    "goalDiff": stats.get('pointDifferential', '0')
                })
        except Exception as e:
            print(f"Puan durumu okuma hatası: {e}")

        # JSON Çıktısı Hazırlama
        output_data = {
            "current_spieltag": current_week,
            "spieltage": matches_by_week,
            "tabelle": tabelle
        }

        with open(f"{league_key}_data.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"[{league_key.upper()}] {league_key}_data.json başarıyla oluşturuldu.")

if __name__ == "__main__":
    run_scraper()
