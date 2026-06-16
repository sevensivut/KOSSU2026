#!/usr/bin/env python3
"""
Fetch live match data from API-Football and merge with CSV predictions
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
API_KEY = os.getenv('RAPIDAPI_KEY')
API_BASE_URL = 'https://v3.football.api-sports.io'
OUTPUT_FILE = Path('data/matches.json')

def find_csv_file():
    """Find the KOSSU CSV file"""
    possible_names = [
        'Kossu 2026 jalkapallon MM (Taulukko).csv',
        'Kossu_2026_jalkapallon_MM_Taulukko.csv',
        'kossu_2026.csv',
        'Kossu2026.csv'
    ]
    
    possible_paths = [Path('.'), Path('data'), Path('scripts')]
    
    for path in possible_paths:
        if not path.exists():
            continue
        for name in possible_names:
            full_path = path / name
            if full_path.exists():
                print(f"✅ Found CSV at: {full_path}")
                return full_path
    
    # Try to find any CSV file
    for path in possible_paths:
        if path.exists():
            for file in path.glob('*.csv'):
                if 'kossu' in str(file).lower() or '2026' in str(file):
                    print(f"✅ Found CSV at: {file}")
                    return file
    
    return None

def parse_csv(csv_file):
    """Parse the CSV file and extract match data"""
    players = ['Markus', 'Juuso', 'Pera', 'Lari', 'Erno', 'Elmo', 
               'Petri', 'Tommi', 'Severi', 'Matti H', 'Pasi', 'Matti K']
    
    matches = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=',')
            rows = list(reader)
            
            # Find where data starts (row with a date)
            data_start_row = None
            for i, row in enumerate(rows):
                if row and len(row) > 0:
                    cell = str(row[0]).strip()
                    if '.' in cell and '2026' in cell:
                        data_start_row = i
                        print(f"✅ Found data starting at row {i+1}")
                        break
            
            if data_start_row is None:
                print("❌ No data rows found!")
                return [], players
            
            # Process data rows
            for row in rows[data_start_row:]:
                if not row or len(row) < 5:
                    continue
                    
                first_cell = str(row[0]).strip() if len(row) > 0 else ''
                if not first_cell or '.' not in first_cell or '2026' not in first_cell:
                    continue
                
                try:
                    # Parse date
                    date_str = first_cell
                    date_parts = date_str.split(' ')
                    date_part = date_parts[0]
                    time_part = date_parts[1] if len(date_parts) > 1 else '00:00'
                    
                    if len(date_part.split('.')) != 3:
                        continue
                        
                    day, month, year = date_part.split('.')
                    date_iso = f"{year}-{month}-{day}T{time_part}:00Z"
                    
                    # IMPORTANT: Column 1 = Home team, Column 3 = Away team (column 2 is empty)
                    home_team = row[1].strip() if len(row) > 1 else ''
                    away_team = row[3].strip() if len(row) > 3 else ''
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Column 4 = Result
                    result = row[4].strip() if len(row) > 4 else ''
                    
                    # Player predictions start at column 6 (index 6)
                    # Columns: 0=date, 1=home, 2=empty, 3=away, 4=result, 5=points, 6+=predictions
                    player_preds = {}
                    for i, player in enumerate(players):
                        col_idx = 6 + i  # Start at column 6
                        if col_idx < len(row):
                            pred = row[col_idx].strip()
                            if pred and pred.upper() in ['1', '2', 'X']:
                                player_preds[player] = pred.upper()
                    
                    match = {
                        'id': len(matches) + 1,
                        'date': date_iso,
                        'homeTeam': home_team,
                        'awayTeam': away_team,
                        'result': result.upper() if result.upper() in ['1', '2', 'X'] else None,
                        'predictions': player_preds,
                        'score': {'home': None, 'away': None},
                        'status': 'SCHEDULED'
                    }
                    matches.append(match)
                    print(f"  ✅ Parsed: {home_team} vs {away_team} ({date_str})")
                    
                except Exception as e:
                    print(f"⚠️ Error parsing row: {e}")
                    continue
        
        print(f"\n✅ Parsed {len(matches)} matches from CSV")
        return matches, players
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return [], []

def fetch_live_matches():
    """Fetch live and recent matches from API-Football"""
    
    if not API_KEY:
        print('⚠️ No RAPIDAPI_KEY found!')
        return []
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    all_matches = []
    
    for date in [today, yesterday]:
        params = {
            'date': date,
            'league': '1',
            'season': '2026'
        }
        
        try:
            url = f'{API_BASE_URL}/fixtures'
            print(f"🔄 Fetching matches for {date}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    all_matches.extend(data['response'])
                    print(f"  ✅ Found {len(data['response'])} matches")
                else:
                    print(f"  ℹ️ No matches for {date}")
            else:
                print(f"  ⚠️ API error: {response.status_code}")
                if response.status_code == 401:
                    print("  🔑 Invalid API key!")
                
        except Exception as e:
            print(f"  ⚠️ Request failed: {e}")
    
    return all_matches

def merge_data(csv_matches, api_matches):
    """Merge CSV predictions with live API data"""
    api_map = {}
    for m in api_matches:
        home = m.get('teams', {}).get('home', {}).get('name', '')
        away = m.get('teams', {}).get('away', {}).get('name', '')
        date = m.get('fixture', {}).get('date', '')[:10]
        
        key = f"{home}_{away}_{date}"
        api_map[key] = m
        api_map[f"{away}_{home}_{date}"] = m
    
    merged = []
    for csv_match in csv_matches:
        home = csv_match['homeTeam']
        away = csv_match['awayTeam']
        date = csv_match['date'][:10]
        key = f"{home}_{away}_{date}"
        
        api_match = api_map.get(key)
        
        if api_match:
            goals = api_match.get('goals', {})
            score_home = goals.get('home')
            score_away = goals.get('away')
            
            status_obj = api_match.get('status', {})
            status_short = status_obj.get('short', '')
            
            if status_short in ['FT', 'AET', 'PEN']:
                status = 'FINISHED'
            elif status_short in ['LIVE', '1H', '2H', 'HT', 'ET']:
                status = 'IN_PLAY'
            else:
                status = 'SCHEDULED'
            
            csv_match['score'] = {
                'home': score_home if score_home is not None else 0,
                'away': score_away if score_away is not None else 0
            }
            csv_match['status'] = status
            
            if status == 'FINISHED' and score_home is not None and score_away is not None:
                if score_home > score_away:
                    csv_match['result'] = '1'
                elif score_away > score_home:
                    csv_match['result'] = '2'
                else:
                    csv_match['result'] = 'X'
        
        merged.append(csv_match)
    
    return merged

def calculate_scores(matches, players):
    """Calculate player scores based on correct predictions"""
    scores = {p: 0 for p in players}
    
    for match in matches:
        if match['status'] == 'FINISHED' and match['result']:
            for player, pred in match.get('predictions', {}).items():
                if pred == match['result']:
                    scores[player] = scores.get(player, 0) + 1
    
    return scores

def main():
    print('🏆 KOSSU 2026 - Live Match Data Fetcher')
    print('=' * 50)
    
    # Find CSV
    csv_file = find_csv_file()
    if not csv_file:
        print('❌ No CSV file found!')
        return False
    
    # Parse CSV
    csv_matches, players = parse_csv(csv_file)
    if not csv_matches:
        print('❌ No data found in CSV!')
        return False
    
    # Fetch live matches
    api_matches = fetch_live_matches()
    
    # Merge data
    merged_matches = merge_data(csv_matches, api_matches)
    
    # Calculate scores
    scores = calculate_scores(merged_matches, players)
    
    # Save to JSON
    output_data = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'matchCount': len(merged_matches),
        'players': players,
        'scores': scores,
        'matches': merged_matches
    }
    
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(merged_matches)} matches to {OUTPUT_FILE}")
    
    # Show live matches
    live_matches = [m for m in merged_matches if m['status'] == 'IN_PLAY']
    if live_matches:
        print(f"\n🔴 LIVE MATCHES ({len(live_matches)}):")
        for m in live_matches:
            print(f"  {m['homeTeam']} {m['score']['home']} - {m['score']['away']} {m['awayTeam']}")
    
    # Show scores
    print("\n📊 Player Scores:")
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (player, score) in enumerate(sorted_scores, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"  {medal} {player}: {score} points")
    
    print('\n🎉 Done!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
