#!/usr/bin/env python3
"""
Fetch real-time match data with smart scheduling.
Only fetches when matches are live or about to start.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration
API_KEY = os.getenv('RAPIDAPI_KEY')  # Your new API-Football key
API_BASE_URL = 'https://v3.football.api-sports.io'
OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'matches.json'
STATE_FILE = OUTPUT_DIR / 'fetch_state.json'  # Track fetch counts

# Track fetch counts
MAX_FETCHES_PER_DAY = 48
OUTPUT_DIR.mkdir(exist_ok=True)

def get_fetch_state():
    """Get current fetch state (counts and timestamps)"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Initialize state
    return {
        'date': datetime.utcnow().date().isoformat(),
        'fetches_today': 0,
        'last_fetch': None,
        'matches_tracked': []
    }

def save_fetch_state(state):
    """Save fetch state"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def can_fetch_now():
    """Check if we can make a new fetch request"""
    state = get_fetch_state()
    
    # Reset daily counter if new day
    today = datetime.utcnow().date().isoformat()
    if state['date'] != today:
        state['date'] = today
        state['fetches_today'] = 0
        save_fetch_state(state)
    
    # Check if we've hit the daily limit
    if state['fetches_today'] >= MAX_FETCHES_PER_DAY:
        print(f"⚠️ Daily limit reached ({MAX_FETCHES_PER_DAY} fetches)")
        return False
    
    return True

def record_fetch():
    """Record that a fetch was made"""
    state = get_fetch_state()
    state['fetches_today'] += 1
    state['last_fetch'] = datetime.utcnow().isoformat()
    save_fetch_state(state)
    print(f"📊 Fetch #{state['fetches_today']}/{MAX_FETCHES_PER_DAY} today")

def check_for_live_matches():
    """Check if there are any live or upcoming matches"""
    
    if not API_KEY:
        print('❌ Error: RAPIDAPI_KEY environment variable not set')
        return False
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Check for matches today
    today = datetime.utcnow().strftime('%Y-%m-%d')
    params = {
        'league': '1',  # FIFA World Cup
        'season': '2026',
        'date': today
    }
    
    try:
        response = requests.get(f'{API_BASE_URL}/fixtures', 
                               headers=headers, 
                               params=params, 
                               timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('errors'):
            print(f"⚠️ API Error: {data['errors']}")
            return False
        
        matches = data.get('response', [])
        
        if not matches:
            print("📅 No matches scheduled for today")
            return False
        
        # Check for live or upcoming matches (within next 2 hours)
        now = datetime.utcnow()
        has_live = False
        
        for match in matches:
            status = match.get('status', {})
            fixture_time = match.get('fixture', {}).get('date')
            
            # Check if match is live
            if status.get('short') in ['LIVE', '1H', '2H', 'HT', 'ET', 'PEN']:
                has_live = True
                print(f"🔴 LIVE: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
                break
            
            # Check if match is starting soon (within 2 hours)
            if fixture_time:
                match_time = datetime.fromisoformat(fixture_time.replace('Z', '+00:00'))
                time_diff = (match_time - now).total_seconds() / 3600
                if 0 < time_diff <= 2:
                    has_live = True
                    print(f"⏳ Starting soon: {match['teams']['home']['name']} vs {match['teams']['away']['name']} (in {time_diff:.1f}h)")
                    break
        
        return has_live
        
    except Exception as e:
        print(f"⚠️ Error checking for matches: {e}")
        return False

def fetch_matches():
    """Fetch match data from API-Football"""
    
    if not API_KEY:
        print('❌ Error: RAPIDAPI_KEY environment variable not set')
        return None
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Fetch today's matches
    today = datetime.utcnow().strftime('%Y-%m-%d')
    params = {
        'league': '1',
        'season': '2026',
        'date': today
    }
    
    url = f'{API_BASE_URL}/fixtures'
    print(f'🔄 Fetching match data from API-Football...')
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('errors'):
            print(f"❌ API Error: {data['errors']}")
            return None
        
        matches = data.get('response', [])
        
        if not matches:
            print('⚠️ No matches found for today')
            return []
        
        print(f'✓ Successfully fetched {len(matches)} matches')
        return matches
        
    except requests.exceptions.RequestException as e:
        print(f'❌ Request failed: {e}')
        return None

def transform_matches(matches):
    """Transform API-Football data into your application's expected format."""
    transformed = []
    
    for match in matches:
        match_data = match.get('fixture', {})
        teams = match.get('teams', {})
        goals = match.get('goals', {})
        status = match.get('status', {})
        
        # Determine match status
        status_short = status.get('short', 'SCHED')
        if status_short in ['LIVE', '1H', '2H', 'HT', 'ET', 'PEN']:
            match_status = 'IN_PLAY'
        elif status_short in ['FT', 'AET', 'PEN']:
            match_status = 'FINISHED'
        else:
            match_status = 'SCHEDULED'
        
        transformed_match = {
            'id': match_data.get('id'),
            'date': match_data.get('date', ''),
            'homeTeam': teams.get('home', {}).get('name', 'Unknown'),
            'homeTeamId': teams.get('home', {}).get('id'),
            'awayTeam': teams.get('away', {}).get('name', 'Unknown'),
            'awayTeamId': teams.get('away', {}).get('id'),
            'status': match_status,
            'score': {
                'home': goals.get('home', 0) if goals else 0,
                'away': goals.get('away', 0) if goals else 0
            },
            'stage': 'group',  # You might want to extract this from league/round info
            'group': match.get('league', {}).get('group', ''),
            'stadium': match_data.get('venue', {}).get('name', ''),
            'matchday': match.get('league', {}).get('round', '')
        }
        
        # Add result based on status and score
        if match_status == 'FINISHED':
            transformed_match['result'] = get_result(transformed_match['score'])
        else:
            transformed_match['result'] = None
            
        transformed.append(transformed_match)
    
    return transformed

def get_result(score):
    """Determine match result (1, X, or 2)."""
    if score.get('home') is None or score.get('away') is None:
        return None
    
    if score['home'] > score['away']:
        return '1'
    elif score['away'] > score['home']:
        return '2'
    else:
        return 'X'

def save_matches(matches):
    """Save transformed matches to JSON file."""
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

def create_sample_data():
    """Create sample data when API fails"""
    print("📋 Creating sample data...")
    
    # Sample matches (you can expand this)
    sample_matches = [
        {
            'id': 1,
            'date': datetime.utcnow().isoformat() + 'Z',
            'homeTeam': 'USA',
            'homeTeamId': 1,
            'awayTeam': 'England',
            'awayTeamId': 2,
            'status': 'SCHEDULED',
            'score': {'home': 0, 'away': 0},
            'stage': 'group',
            'group': 'A',
            'stadium': 'Stadium A',
            'matchday': 'Group Stage',
            'result': None
        },
        # Add more sample matches as needed
    ]
    
    return sample_matches

def main():
    """Main execution function"""
    print('🏆 World Cup 2026 - Smart Match Data Fetcher')
    print('=' * 60)
    print(f'Time: {datetime.utcnow().isoformat()}Z')
    print(f'Daily Limit: {MAX_FETCHES_PER_DAY} fetches')
    print()
    
    # Check if we can fetch
    if not can_fetch_now():
        print('❌ Daily fetch limit reached. Skipping...')
        return True
    
    # Check if there are live matches
    print('🔍 Checking for live matches...')
    has_live = check_for_live_matches()
    
    if not has_live:
        print('📊 No live matches currently. No fetch needed.')
        print('⏰ Next check will be in 15 minutes.')
        return True
    
    # Record that we're making a fetch
    record_fetch()
    
    # Fetch the data
    matches = fetch_matches()
    
    if matches is None:
        print('❌ Failed to fetch match data')
        print('💡 Using sample data as fallback...')
        matches = create_sample_data()
    elif not matches:
        print('⚠️ No matches returned from API')
        print('💡 Using sample data as fallback...')
        matches = create_sample_data()
    
    # Transform and save
    transformed_matches = transform_matches(matches)
    save_matches(transformed_matches)
    
    print('\n✅ Match data update complete!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
