#!/usr/bin/env python3
"""
Fetch real-time match data from the worldcup26.ir API
for the FIFA World Cup 2026.
"""

import os
import json
import requests
import urllib3
from datetime import datetime, timedelta
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_KEY = os.getenv('RAPIDAPI_KEY')
API_BASE_URL = 'https://v3.football.api-sports.io'
OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'matches.json'
STATE_FILE = OUTPUT_DIR / 'fetch_state.json'

# Create data directory
OUTPUT_DIR.mkdir(exist_ok=True)

# Sample data for testing (real World Cup teams)
SAMPLE_MATCHES = [
    {
        "id": 1,
        "date": "2026-06-11T16:00:00Z",
        "homeTeam": "USA",
        "homeTeamId": 1,
        "awayTeam": "Mexico",
        "awayTeamId": 2,
        "status": "SCHEDULED",
        "score": {"home": 0, "away": 0},
        "stage": "group",
        "group": "A",
        "stadium": "Stadium A",
        "matchday": "Group Stage"
    },
    {
        "id": 2,
        "date": "2026-06-11T18:00:00Z",
        "homeTeam": "Brazil",
        "homeTeamId": 3,
        "awayTeam": "Argentina",
        "awayTeamId": 4,
        "status": "SCHEDULED",
        "score": {"home": 0, "away": 0},
        "stage": "group",
        "group": "B",
        "stadium": "Stadium B",
        "matchday": "Group Stage"
    },
    {
        "id": 3,
        "date": "2026-06-12T16:00:00Z",
        "homeTeam": "Germany",
        "homeTeamId": 5,
        "awayTeam": "France",
        "awayTeamId": 6,
        "status": "SCHEDULED",
        "score": {"home": 0, "away": 0},
        "stage": "group",
        "group": "C",
        "stadium": "Stadium C",
        "matchday": "Group Stage"
    },
    {
        "id": 4,
        "date": "2026-06-12T18:00:00Z",
        "homeTeam": "England",
        "homeTeamId": 7,
        "awayTeam": "Spain",
        "awayTeamId": 8,
        "status": "SCHEDULED",
        "score": {"home": 0, "away": 0},
        "stage": "group",
        "group": "D",
        "stadium": "Stadium D",
        "matchday": "Group Stage"
    },
    {
        "id": 5,
        "date": "2026-06-13T16:00:00Z",
        "homeTeam": "Italy",
        "homeTeamId": 9,
        "awayTeam": "Netherlands",
        "awayTeamId": 10,
        "status": "SCHEDULED",
        "score": {"home": 0, "away": 0},
        "stage": "group",
        "group": "E",
        "stadium": "Stadium E",
        "matchday": "Group Stage"
    },
    {
        "id": 6,
        "date": "2026-06-13T18:00:00Z",
        "homeTeam": "Portugal",
        "homeTeamId": 11,
        "awayTeam": "Belgium",
        "awayTeamId": 12,
        "status": "SCHEDULED",
        "score": {"home": 0, "away": 0},
        "stage": "group",
        "group": "F",
        "stadium": "Stadium F",
        "matchday": "Group Stage"
    }
]

def fetch_matches():
    """Fetch match data from API-Football."""
    
    if not API_KEY:
        print('⚠️ No API key found, using sample data')
        return None
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Try to fetch World Cup matches
    params = {
        'league': '1',  # FIFA World Cup
        'season': '2026'
    }
    
    url = f'{API_BASE_URL}/fixtures'
    print(f'🔄 Fetching match data from API-Football...')
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('errors'):
            print(f"⚠️ API Error: {data['errors']}")
            return None
        
        matches = data.get('response', [])
        
        if not matches:
            print('⚠️ No matches found from API')
            return None
        
        print(f'✓ Successfully fetched {len(matches)} matches from API')
        return matches
        
    except requests.exceptions.RequestException as e:
        print(f'❌ API request failed: {e}')
        return None
    except json.JSONDecodeError as e:
        print(f'❌ JSON parse error: {e}')
        return None

def transform_matches(api_matches):
    """Transform API matches to our format."""
    transformed = []
    
    if not api_matches:
        return SAMPLE_MATCHES
    
    for match in api_matches:
        try:
            fixture = match.get('fixture', {})
            teams = match.get('teams', {})
            goals = match.get('goals', {})
            status = match.get('status', {})
            
            # Determine status
            status_short = status.get('short', 'SCHED')
            if status_short in ['LIVE', '1H', '2H', 'HT', 'ET', 'PEN']:
                match_status = 'IN_PLAY'
            elif status_short in ['FT', 'AET', 'PEN']:
                match_status = 'FINISHED'
            else:
                match_status = 'SCHEDULED'
            
            transformed_match = {
                'id': fixture.get('id'),
                'date': fixture.get('date', datetime.utcnow().isoformat() + 'Z'),
                'homeTeam': teams.get('home', {}).get('name', 'Unknown'),
                'homeTeamId': teams.get('home', {}).get('id'),
                'awayTeam': teams.get('away', {}).get('name', 'Unknown'),
                'awayTeamId': teams.get('away', {}).get('id'),
                'status': match_status,
                'score': {
                    'home': goals.get('home') if goals else 0,
                    'away': goals.get('away') if goals else 0
                },
                'stage': match.get('league', {}).get('round', 'group'),
                'group': match.get('league', {}).get('group', ''),
                'stadium': fixture.get('venue', {}).get('name', ''),
                'matchday': match.get('league', {}).get('round', '')
            }
            transformed.append(transformed_match)
        except Exception as e:
            print(f'⚠️ Error transforming match: {e}')
            continue
    
    # If no matches transformed, use sample data
    if not transformed:
        print('⚠️ No matches transformed, using sample data')
        return SAMPLE_MATCHES
    
    return transformed

def save_matches(matches):
    """Save matches to JSON file."""
    output_data = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'competitionName': 'FIFA World Cup 2026',
        'matchCount': len(matches),
        'playedCount': len([m for m in matches if m['status'] == 'FINISHED']),
        'inPlayCount': len([m for m in matches if m['status'] == 'IN_PLAY']),
        'upcomingCount': len([m for m in matches if m['status'] == 'SCHEDULED']),
        'matches': matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f'✓ Saved {len(matches)} matches to {OUTPUT_FILE}')
    print(f'  - Played: {output_data["playedCount"]}')
    print(f'  - In Play: {output_data["inPlayCount"]}')
    print(f'  - Upcoming: {output_data["upcomingCount"]}')
    
    return output_data

def main():
    """Main execution function."""
    print('🏆 World Cup 2026 - Match Data Fetcher')
    print('=' * 50)
    print(f'Time: {datetime.utcnow().isoformat()}Z')
    print()
    
    # Try to fetch from API
    api_matches = fetch_matches()
    
    # Transform matches (will use sample data if API fails)
    matches = transform_matches(api_matches)
    
    # Save matches
    save_matches(matches)
    
    print('\n✅ Match data update complete!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
