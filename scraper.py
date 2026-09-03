import json
import requests

def get_match_details(league_code, event_id):
    """Oynanmış maçların gol, kart ve kadro detaylarını çeker."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/summary?event={event_id}"
    try:
        res = requests.get(url, timeout=8)
        if res.status_code != 200:
            return {}, [], []
        data = res.json()
        
        goals = []
        cards = []
        
        for event in data.get('keyEvents', []):
            clock = event.get('clock', {}).get('displayValue', '')
            text = event.get('text', '')
            event_type = event.get('type', {}).get('text', '').lower()
            
            if 'goal' in event_type:
                goals.append(f"{clock}' {text}")
            elif 'card' in event_type:
                card_type = "🟨" if "yellow" in event_type or "yellow" in text.lower() else "🟥"
                cards.append(f"{clock}' {card_type} {text}")

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
                        if subbed_out:
                            sub_events = [e for e in data.get('keyEvents', []) if e.get('type', {}).get('text', '').lower() == 'substitution']
                            for sub in sub_events:
                                if athlete.get('id') in str(sub):
                                    clock = sub.get('clock', {}).get('displayValue', '')
                                    sub_info = f" (🔄 {clock}' Çıktı)"
                        lineups[team_key].append(f"{name}{sub_info}")

        return lineups, goals, cards
    except Exception as e:
        return {}, [], []

def run_scraper():
    leagues = {
        "bl1": "ger.1",
        "bl2": "ger.2"
    }

    for league_key, league_code in leagues.items():
        print(f"[{league_key.upper()}] Tüm haftaların fikstürü ve verileri çekiliyor...")
        
        # Aktif haftayı tespit et
        main_sb_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        main_res = requests.get(main_sb_url).json()
        current_week = main_res.get('week', {}).get('number', 1)
        
        matches_by_week = {}

        # Bundesliga 1 ve 2 liglerinde toplam 34 hafta taranır
        for w in range(1, 35):
            week_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard?week={w}"
            try:
                w_res = requests.get(week_url, timeout=8).json()
                events = w_res.get('events', [])
                
                if not events:
                    continue

                week_matches = []
                for event in events:
                    event_id = event.get('id')
                    competition = event.get('competitions', [{}])[0]
                    status = event.get('status', {}).get('type', {}).get('state', '')
                    
                    competitors = competition.get('competitors', [])
                    if len(competitors) < 2:
                        continue
                        
                    home_team = competitors[0]['team']['displayName']
                    away_team = competitors[1]['team']['displayName']
                    
                    score_str = ""
                    if status in ['post', 'in']:
                        home_score = competitors[0].get('score', '0')
                        away_score = competitors[1].get('score', '0')
                        score_str = f"{home_score} - {away_score}"
                    
                    date_time = competition.get('date', '').split('T')
                    date_val = date_time[0] if len(date_time) > 0 else ""
                    time_val = date_time[1][:5] if len(date_time) > 1 else ""

                    # Detaylar sadece oynanmış/oynanmakta olan maçlar için çekilir
                    lineups, goals, cards = {}, [], []
                    if status in ['post', 'in']:
                        lineups, goals, cards = get_match_details(league_code, event_id)

                    week_matches.append({
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
                    })

                matches_by_week[str(w)] = week_matches
            except Exception as e:
                print(f"{w}. Hafta çekilirken hata oluştu: {e}")

        # Puan Durumu (Tabelle)
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
            print(f"Puan durumu hatası: {e}")

        output_data = {
            "current_spieltag": current_week,
            "spieltage": matches_by_week,
            "tabelle": tabelle
        }

        with open(f"{league_key}_data.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"[{league_key.upper()}] {league_key}_data.json tamamlandı.")

if __name__ == "__main__":
    run_scraper()
