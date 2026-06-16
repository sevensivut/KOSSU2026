#!/usr/bin/env python3
"""
Convert KOSSU CSV data to JSON format for the frontend
"""

import csv
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
CSV_FILE = Path('Kossu 2026 jalkapallon MM (Taulukko).csv')
OUTPUT_FILE = Path('data/matches.json')
API_KEY = 'bf69bdfcf6fe47a2b8eb9de53657bf3c'  # Your football-data.org key

def parse_csv():
    """Parse the CSV file and extract data"""
    
    players = ['Markus', 'Juuso', 'Pera', 'Lari', 'Erno', 'Elmo', 'Petri', 'Tommi', 'Severi', 'Matti H', 'Pasi', 'Matti K']
    
    matches = []
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=',')
            rows = list(reader)
            
            # Find the data rows (skip headers)
            for row in rows:
                if len(row) < 3:
                    continue
                    
                # Look for rows that look like match data (have a date)
                if row[0] and '2026' in row[0] and '.' in row[0]:
                    try:
                        # Parse the match
                        date_str = row[0].strip()
                        home_team = row[1].strip() if len(row) > 1 else ''
                        away_team = row[2].strip() if len(row) > 2 else ''
                        result = row[3].strip() if len(row) > 3 else ''
                        
                        # Parse date
                        date_parts = date_str.split(' ')
                        date_part = date_parts[0]
                        time_part = date_parts[1] if len(date_parts) > 1 else '00:00'
                        
                        # Convert date format: 11.06.2026 -> 2026-06-11
                        day, month, year = date_part.split('.')
                        date_iso = f"{year}-{month}-{day}T{time_part}:00Z"
                        
                        # Get player predictions
                        predictions = {}
                        for i, player in enumerate(players):
                            col_idx = 4 + i  # Predictions start at column 4
                            if col_idx < len(row):
                                pred = row[col_idx].strip()
                                if pred and pred != '0.0':
                                    predictions[player] = pred
                        
                        match = {
                            'id': len(matches) + 1,
                            'date': date_iso,
                            'homeTeam': home_team,
                            'awayTeam': away_team,
                            'result': result,
                            'predictions': predictions
                        }
                        matches.append(match)
                    except Exception as e:
                        print(f"⚠️ Error parsing row: {e}")
                        continue
        
        print(f"✅ Parsed {len(matches)} matches from CSV")
        return matches
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []

def fetch_real_data():
    """Fetch real match data from football-data.org"""
    
    headers = {'X-Auth-Token': API_KEY}
    url = 'https://api.football-data.org/v4/competitions/2000/matches'  # World Cup
    
    try:
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

def merge_data(csv_matches, api_matches):
    """Merge CSV data with API data"""
    
    # Create a map of API matches by team and date
    api_map = {}
    for match in api_matches:
        home = match.get('homeTeam', {}).get('name', '')
        away = match.get('awayTeam', {}).get('name', '')
        date = match.get('utcDate', '')
        key = f"{home}_{away}_{date[:10]}"
        api_map[key] = match
    
    # Merge with CSV data
    merged = []
    for csv_match in csv_matches:
        home = csv_match['homeTeam']
        away = csv_match['awayTeam']
        date = csv_match['date'][:10]  # Just the date part
        
        # Try to find matching API data
        key = f"{home}_{away}_{date}"
        api_match = api_map.get(key)
        
        if api_match:
            # Use API data for scores and status
            csv_match['status'] = api_match.get('status', 'SCHEDULED')
            score = api_match.get('score', {}).get('fullTime', {})
            csv_match['score'] = {
                'home': score.get('home', 0),
                'away': score.get('away', 0)
            }
            csv_match['realResult'] = api_match.get('result', {})
        else:
            # Use CSV data
            csv_match['status'] = 'FINISHED' if csv_match['result'] else 'SCHEDULED'
            csv_match['score'] = {'home': 0, 'away': 0}
        
        merged.append(csv_match)
    
    return merged

def save_json(data):
    """Save merged data to JSON"""
    
    output = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'matches': data,
        'players': ['Markus', 'Juuso', 'Pera', 'Lari', 'Erno', 'Elmo', 'Petri', 'Tommi', 'Severi', 'Matti H', 'Pasi', 'Matti K']
    }
    
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(data)} matches to {OUTPUT_FILE}")

def main():
    print('🔄 Converting CSV to JSON...')
    
    # Parse CSV
    csv_matches = parse_csv()
    if not csv_matches:
        print('❌ No CSV data found!')
        return False
    
    # Fetch API data
    api_matches = fetch_real_data()
    
    # Merge
    merged = merge_data(csv_matches, api_matches)
    
    # Save
    save_json(merged)
    
    print('✅ Done!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
