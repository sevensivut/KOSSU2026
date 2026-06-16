#!/usr/bin/env python3
"""
Fetch match data and convert CSV to JSON for frontend
"""

import os
import csv
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
CSV_FILE = Path('Kossu 2026 jalkapallon MM (Taulukko).csv')
OUTPUT_FILE = Path('data/matches.json')
API_KEY = 'bf69bdfcf6fe47a2b8eb9de53657bf3c'

def parse_csv():
    """Parse the CSV file and extract match data"""
    players = ['Markus', 'Juuso', 'Pera', 'Lari', 'Erno', 'Elmo', 
               'Petri', 'Tommi', 'Severi', 'Matti H', 'Pasi', 'Matti K']
    
    matches = []
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=',')
            rows = list(reader)
            
            for row in rows:
                if not row or len(row) < 4:
                    continue
                    
                if row[0] and '2026' in row[0] and '.' in row[0]:
                    try:
                        date_str = row[0].strip()
                        home_team = row[1].strip() if len(row) > 1 else ''
                        away_team = row[2].strip() if len(row) > 2 else ''
                        result = row[3].strip() if len(row) > 3 else ''
                        
                        date_parts = date_str.split(' ')
                        date_part = date_parts[0]
                        time_part = date_parts[1] if len(date_parts) > 1 else '00:00'
                        day, month, year = date_part.split('.')
                        date_iso = f"{year}-{month}-{day}T{time_part}:00Z"
                        
                        # Get player predictions
                        player_preds = {}
                        for i, player in enumerate(players):
                            col_idx = 4 + i
                            if col_idx < len(row):
                                pred = row[col_idx].strip()
                                if pred and pred not in ['0.0', 'FALSE', 'TRUE']:
                                    player_preds[player] = pred
                        
                        match = {
                            'id': len(matches) + 1,
                            'date': date_iso,
                            'homeTeam': home_team,
                            'awayTeam': away_team,
                            'result': result,
                            'predictions': player_preds
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

def fetch_api_matches():
    """Fetch real match data from football-data.org"""
    try:
        url = 'https://api.football-data.org/v4/competitions/2000/matches'
        headers = {'X-Auth-Token': API_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            print(f"✅ Fetched {len(matches)} matches from API")
            return matches
        else:
            print(f"⚠️ API returned {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ API error: {e}")
        return []

def merge_data(csv_matches, api_matches, players):
    """Merge CSV predictions with API data"""
    api_map = {}
    for m in api_matches:
        home = m.get('homeTeam', {}).get('name', '')
        away = m.get('awayTeam', {}).get('name', '')
        date = m.get('utcDate', '')[:10]
        key = f"{home}_{away}_{date}"
        api_map[key] = m
    
    merged = []
    for csv_match in csv_matches:
        home = csv_match['homeTeam']
        away = csv_match['awayTeam']
        date = csv_match['date'][:10]
        key = f"{home}_{away}_{date}"
        
        api_match = api_map.get(key)
        
        if api_match:
            score = api_match.get('score', {}).get('fullTime', {})
            csv_match['score'] = {
                'home': score.get('home', 0),
                'away': score.get('away', 0)
            }
            csv_match['status'] = api_match.get('status', 'SCHEDULED')
            csv_match['realResult'] = api_match.get('result', {})
        else:
            csv_match['score'] = {'home': 0, 'away': 0}
            csv_match['status'] = 'FINISHED' if csv_match['result'] else 'SCHEDULED'
        
        merged.append(csv_match)
    
    return merged

def main():
    print('🔄 Processing KOSSU 2026 data...')
    
    csv_matches, players = parse_csv()
    if not csv_matches:
        print('❌ No data found in CSV!')
        return False
    
    api_matches = fetch_api_matches()
    merged_matches = merge_data(csv_matches, api_matches, players)
    
    output_data = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'matchCount': len(merged_matches),
        'players': players,
        'matches': merged_matches
    }
    
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(merged_matches)} matches to {OUTPUT_FILE}")
    print('🎉 Done!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
