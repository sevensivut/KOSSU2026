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

# Team name mapping (Finnish -> English)
TEAM_MAPPING = {
    'Meksiko': 'Mexico',
    'Etelä-Afrikka': 'South Africa',
    'Etelä-Korea': 'South Korea',
    'Tšekki': 'Czech Republic',
    'Kanada': 'Canada',
    'Bosnia ja Hertsegovina': 'Bosnia and Herzegovina',
    'USA': 'United States',
    'Paraguay': 'Paraguay',
    'Qatar': 'Qatar',
    'Sveitsi': 'Switzerland',
    'Brasilia': 'Brazil',
    'Marokko': 'Morocco',
    'Haiti': 'Haiti',
    'Skotlanti': 'Scotland',
    'Australia': 'Australia',
    'Turkki': 'Turkey',
    'Saksa': 'Germany',
    'Curaçao': 'Curacao',
    'Hollanti': 'Netherlands',
    'Japani': 'Japan',
    'Norsunluurannikko': 'Ivory Coast',
    'Ecuador': 'Ecuador',
    'Ruotsi': 'Sweden',
    'Tunisia': 'Tunisia',
    'Espanja': 'Spain',
    'Kap Verde': 'Cape Verde',
    'Belgia': 'Belgium',
    'Egypti': 'Egypt',
    'Saudi-Arabia': 'Saudi Arabia',
    'Uruguay': 'Uruguay',
    'Iran': 'Iran',
    'Uusi-Seelanti': 'New Zealand',
    'Ranska': 'France',
    'Senegal': 'Senegal',
    'Irak': 'Iraq',
    'Norja': 'Norway',
    'Argentiina': 'Argentina',
    'Algeria': 'Algeria',
    'Itävalta': 'Austria',
    'Jordania': 'Jordan',
    'Portugali': 'Portugal',
    'Kongon dem. tasavalta': 'Congo DR',
    'Englanti': 'England',
    'Kroatia': 'Croatia',
    'Ghana': 'Ghana',
    'Panama': 'Panama',
    'Uzbekistan': 'Uzbekistan',
    'Kolumbia': 'Colombia',
    'Kongon dem. tv': 'Congo DR',
}

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
    
    for path in possible_paths:
        if path.exists():
            for file in path.glob('*.csv'):
                if 'kossu' in str(file).lower() or '2026' in str(file):
                    print(f"✅ Found CSV at: {file}")
                    return file
    
    return None

def parse_csv(csv_file):
    """Parse the CSV file and extract match data with weights"""
    players = ['Markus', 'Juuso', 'Pera', 'Lari', 'Erno', 'Elmo', 
               'Petri', 'Tommi', 'Severi', 'Matti H', 'Pasi', 'Matti K']
    
    matches = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=',')
            rows = list(reader)
            
            # Find header row to locate weight columns
            header_row = None
            for i, row in enumerate(rows):
                if row and len(row) > 0:
                    if 'Pvm ja klo' in str(row) or 'Peli' in str(row):
                        header_row = i
                        break
            
            # Find weight column indices
            weight_1_idx = None
            weight_2_idx = None
            weight_x_idx = None
            
            if header_row is not None and header_row < len(rows):
                header = rows[header_row]
                for i, cell in enumerate(header):
                    if cell:
                        cell_lower = str(cell).lower()
                        if 'painoarvo 1' in cell_lower or 'painoarvo1' in cell_lower:
                            weight_1_idx = i
                        elif 'painoarvo 2' in cell_lower or 'painoarvo2' in cell_lower:
                            weight_2_idx = i
                        elif 'painoarvo x' in cell_lower or 'painoarvox' in cell_lower:
                            weight_x_idx = i
            
            print(f"📊 Weight columns: 1={weight_1_idx}, 2={weight_2_idx}, X={weight_x_idx}")
            
            # Find where data starts (row with a date)
            data_start_row = None
            for i, row in enumerate(rows):
                if row and len(row) > 0:
                    cell = str(row[0]).strip()
                    if '.' in cell and '2026' in cell:
                        data_start_row = i
                        break
            
            if data_start_row is None:
                return [], players
            
            # Process data rows
            for row in rows[data_start_row:]:
                if not row or len(row) < 5:
                    continue
                    
                first_cell = str(row[0]).strip() if len(row) > 0 else ''
                if not first_cell or '.' not in first_cell or '2026' not in first_cell:
                    continue
                
                try:
                    date_str = first_cell
                    date_parts = date_str.split(' ')
                    date_part = date_parts[0]
                    time_part = date_parts[1] if len(date_parts) > 1 else '00:00'
                    
                    day, month, year = date_part.split('.')
                    date_iso = f"{year}-{month}-{day}T{time_part}:00Z"
                    
                    home_team = row[1].strip() if len(row) > 1 else ''
                    away_team = row[3].strip() if len(row) > 3 else ''
                    
                    if not home_team or not away_team:
                        continue
                    
                    # CSV result (from column 4) - only used if API has no data
                    csv_result = row[4].strip() if len(row) > 4 else ''
                    
                    # Get weights from correct columns
                    weight_1 = 0.0
                    weight_2 = 0.0
                    weight_x = 0.0
                    
                    if weight_1_idx is not None and weight_1_idx < len(row):
                        try:
                            val = row[weight_1_idx].strip()
                            if val:
                                weight_1 = float(val)
                        except:
                            pass
                    
                    if weight_2_idx is not None and weight_2_idx < len(row):
                        try:
                            val = row[weight_2_idx].strip()
                            if val:
                                weight_2 = float(val)
                        except:
                            pass
                    
                    if weight_x_idx is not None and weight_x_idx < len(row):
                        try:
                            val = row[weight_x_idx].strip()
                            if val:
                                weight_x = float(val)
                        except:
                            pass
                    
                    player_preds = {}
                    for i, player in enumerate(players):
                        col_idx = 6 + i
                        if col_idx < len(row):
                            pred = row[col_idx].strip()
                            if pred and pred.upper() in ['1', '2', 'X']:
                                player_preds[player] = pred.upper()
                    
                    match = {
                        'id': len(matches) + 1,
                        'date': date_iso,
                        'homeTeam': home_team,
                        'awayTeam': away_team,
                        'homeTeamEn': TEAM_MAPPING.get(home_team, home_team),
                        'awayTeamEn': TEAM_MAPPING.get(away_team, away_team),
                        'csv_result': csv_result.upper() if csv_result.upper() in ['1', '2', 'X'] else None,
                        'weight_1': weight_1,
                        'weight_2': weight_2,
                        'weight_x': weight_x,
                        'predictions': player_preds,
                        'score': {'home': None, 'away': None},
                        'status': 'SCHEDULED'
                    }
                    matches.append(match)
                    
                except Exception as e:
                    print(f"⚠️ Error parsing row: {e}")
                    continue
        
        print(f"✅ Parsed {len(matches)} matches from CSV")
        return matches, players
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return [], []

def fetch_live_matches():
    """Fetch live and recent matches from API-Football for entire World Cup"""
    
    if not API_KEY:
        print('⚠️ No RAPIDAPI_KEY found! Make sure it\'s set in GitHub Secrets')
        return []
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Full World Cup date range: June 11 to July 19, 2026
    all_matches = []
    
    start_date = datetime(2026, 6, 11)
    end_date = datetime(2026, 7, 19)
    
    dates_to_check = []
    current_date = start_date
    while current_date <= end_date:
        dates_to_check.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    print(f"🔄 Checking {len(dates_to_check)} days (June 11 - July 19)...")
    print(f"🔑 Using API key: {API_KEY[:10]}...")
    
    total_matches_found = 0
    
    for date in dates_to_check:
        try:
            url = f'{API_BASE_URL}/fixtures'
            params = {'date': date}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('response', [])
                
                if matches:
                    # Check if any are World Cup matches
                    world_cup_matches = []
                    for match in matches:
                        league_name = match.get('league', {}).get('name', '')
                        if 'world cup' in league_name.lower():
                            world_cup_matches.append(match)
                            all_matches.append(match)
                    
                    if world_cup_matches:
                        print(f"  📅 {date}: {len(world_cup_matches)} World Cup matches")
                        total_matches_found += len(world_cup_matches)
                        
                        # Show first match as example
                        if len(world_cup_matches) > 0:
                            m = world_cup_matches[0]
                            home = m.get('teams', {}).get('home', {}).get('name', '')
                            away = m.get('teams', {}).get('away', {}).get('name', '')
                            goals = m.get('goals', {})
                            status = m.get('status', {}).get('short', '')
                            print(f"    Example: {home} vs {away} - {status} {goals.get('home', '?')}-{goals.get('away', '?')}")
                else:
                    # No matches this day - skip silently
                    pass
                    
            elif response.status_code == 404:
                # No matches - skip silently
                pass
            elif response.status_code == 429:
                print(f"  ⚠️ Rate limit exceeded on {date}!")
                break
            else:
                if response.status_code != 404:
                    print(f"  ⚠️ API error for {date}: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ Request failed for {date}: {e}")
    
    print(f"\n✅ Found {len(all_matches)} World Cup matches in total")
    
    # Show all found matches
    if all_matches:
        print("\n📋 All World Cup matches found:")
        for i, match in enumerate(all_matches[:10]):  # Show first 10
            home = match.get('teams', {}).get('home', {}).get('name', '')
            away = match.get('teams', {}).get('away', {}).get('name', '')
            date = match.get('fixture', {}).get('date', '')[:10]
            status = match.get('status', {}).get('short', '')
            goals = match.get('goals', {})
            print(f"  {i+1}. {home} vs {away} ({date}) - {status} - {goals.get('home', '?')}-{goals.get('away', '?')}")
        if len(all_matches) > 10:
            print(f"  ... and {len(all_matches) - 10} more matches")
    
    return all_matches

def merge_data(csv_matches, api_matches):
    """Merge CSV predictions with live API data - API takes priority"""
    api_map = {}
    for m in api_matches:
        home = m.get('teams', {}).get('home', {}).get('name', '')
        away = m.get('teams', {}).get('away', {}).get('name', '')
        date = m.get('fixture', {}).get('date', '')[:10]
        
        # Add both directions for matching
        key = f"{home}_{away}_{date}"
        api_map[key] = m
        api_map[f"{away}_{home}_{date}"] = m
    
    merged = []
    api_matched = 0
    csv_fallback = 0
    
    for csv_match in csv_matches:
        home_en = csv_match['homeTeamEn']
        away_en = csv_match['awayTeamEn']
        date = csv_match['date'][:10]
        
        # Try with English names first
        key = f"{home_en}_{away_en}_{date}"
        api_match = api_map.get(key)
        
        # Try with Finnish names if English didn't match
        if not api_match:
            key_fi = f"{csv_match['homeTeam']}_{csv_match['awayTeam']}_{date}"
            api_match = api_map.get(key_fi)
        
        if api_match:
            api_matched += 1
            
            goals = api_match.get('goals', {})
            score_home = goals.get('home')
            score_away = goals.get('away')
            
            status_obj = api_match.get('status', {})
            status_short = status_obj.get('short', '')
            
            # Map API status
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
            else:
                csv_match['result'] = None
        else:
            # No API match - use CSV as fallback
            csv_fallback += 1
            if csv_match.get('csv_result'):
                csv_match['result'] = csv_match['csv_result']
                csv_match['status'] = 'FINISHED'
                if csv_match['result'] == '1':
                    csv_match['score'] = {'home': 1, 'away': 0}
                elif csv_match['result'] == '2':
                    csv_match['score'] = {'home': 0, 'away': 1}
                elif csv_match['result'] == 'X':
                    csv_match['score'] = {'home': 1, 'away': 1}
            else:
                csv_match['status'] = 'SCHEDULED'
                csv_match['score'] = {'home': 0, 'away': 0}
        
        merged.append(csv_match)
    
    print(f"\n🔗 Matches: {api_matched} from API, {csv_fallback} from CSV fallback")
    return merged

def calculate_scores(matches, players):
    """Calculate player scores based on correct predictions using weights"""
    scores = {p: 0.0 for p in players}
    
    for match in matches:
        if match['status'] == 'FINISHED' and match['result']:
            result = match['result']
            
            if result == '1':
                weight = match.get('weight_1', 0.0)
            elif result == '2':
                weight = match.get('weight_2', 0.0)
            elif result == 'X':
                weight = match.get('weight_x', 0.0)
            else:
                weight = 0.0
            
            for player, pred in match.get('predictions', {}).items():
                if pred == result:
                    scores[player] = scores.get(player, 0.0) + weight
    
    return scores

def main():
    print('🏆 KOSSU 2026 - Live Match Data Fetcher')
    print('=' * 50)
    print(f'📅 Today: {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')
    print()
    
    csv_file = find_csv_file()
    if not csv_file:
        print('❌ No CSV file found!')
        return False
    
    csv_matches, players = parse_csv(csv_file)
    if not csv_matches:
        print('❌ No data found in CSV!')
        return False
    
    api_matches = fetch_live_matches()
    merged_matches = merge_data(csv_matches, api_matches)
    scores = calculate_scores(merged_matches, players)
    
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
    
    # Show finished matches with scores
    finished_matches = [m for m in merged_matches if m['status'] == 'FINISHED' and m['score']['home'] is not None]
    if finished_matches:
        print(f"\n✅ FINISHED MATCHES ({len(finished_matches)}):")
        for m in finished_matches[:10]:
            print(f"  {m['homeTeam']} {m['score']['home']} - {m['score']['away']} {m['awayTeam']}")
    
    print("\n📊 Player Scores:")
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (player, score) in enumerate(sorted_scores, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"  {medal} {player}: {score:.1f} points")
    
    print('\n🎉 Done!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
