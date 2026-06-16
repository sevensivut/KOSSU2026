#!/usr/bin/env python3
"""
Fetch real-time match data from football-data.org API
and save it as JSON for the web interface.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY')
COMPETITION_ID = 2180  # FIFA World Cup 2026
API_BASE_URL = 'https://api.football-data.org/v4'
OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'matches.json'

# Create data directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_matches():
    """Fetch match data from football-data.org API."""
    
    if not FOOTBALL_API_KEY:
        print('❌ Error: FOOTBALL_API_KEY environment variable not set')
        print('Please set the FOOTBALL_API_KEY secret in GitHub Actions settings')
        return None
    
    headers = {
        'X-Auth-Token': FOOTBALL_API_KEY
    }
    
    url = f'{API_BASE_URL}/competitions/{COMPETITION_ID}/matches'
    
    print(f'🔄 Fetching match data from {url}...')
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f'✓ Successfully fetched {len(data["matches"])} matches')
        
        return data['matches']
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            print('❌ Error: Invalid or expired API key')
        elif response.status_code == 404:
            print('❌ Error: Competition not found')
        else:
            print(f'❌ HTTP Error: {response.status_code} - {e}')
        return None
        
    except requests.exceptions.RequestException as e:
        print(f'❌ Request failed: {e}')
        return None
    except json.JSONDecodeError:
        print('❌ Error: Invalid JSON response')
        return None

def transform_matches(matches):
    """Transform raw match data into our format."""
    
    transformed = []
    
    for match in matches:
        transformed_match = {
            'id': match['id'],
            'date': match['utcDate'],
            'homeTeam': match['homeTeam']['name'],
            'homeTeamId': match['homeTeam']['id'],
            'awayTeam': match['awayTeam']['name'],
            'awayTeamId': match['awayTeam']['id'],
            'status': match['status'],
            'score': {
                'home': match['score']['fullTime']['home'],
                'away': match['score']['fullTime']['away']
            },
            'result': get_result(match['score']['fullTime'])
        }
        
        # Add stage/group info if available
        if 'stage' in match:
            transformed_match['stage'] = match['stage']
        if 'group' in match:
            transformed_match['group'] = match['group']
            
        transformed.append(transformed_match)
    
    return transformed

def get_result(score):
    """Determine match result (1, X, or 2)."""
    
    if score['home'] is None or score['away'] is None:
        return None
    
    if score['home'] > score['away']:
        return '1'  # Home team wins
    elif score['away'] > score['home']:
        return '2'  # Away team wins
    else:
        return 'X'  # Draw

def load_existing_data():
    """Load existing matches data if it exists."""
    
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f'✓ Loaded {len(data["matches"])} existing matches')
                return data
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f'⚠ Warning: Could not load existing data: {e}')
    
    return None

def save_matches(matches):
    """Save transformed matches to JSON file."""
    
    output_data = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'competitionId': COMPETITION_ID,
        'competitionName': 'FIFA World Cup 2026',
        'matchCount': len(matches),
        'playedCount': len([m for m in matches if m['status'] == 'FINISHED']),
        'upcomingCount': len([m for m in matches if m['status'] != 'FINISHED']),
        'matches': matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f'✓ Saved {len(matches)} matches to {OUTPUT_FILE}')
    print(f'  - Played: {output_data["playedCount"]}')
    print(f'  - Upcoming: {output_data["upcomingCount"]}')
    
    return output_data

def compare_and_report_changes(old_data, new_data):
    """Compare old and new data to identify changes."""
    
    if not old_data:
        return
    
    old_matches = {m['id']: m for m in old_data['matches']}
    new_matches = {m['id']: m for m in new_data['matches']}
    
    # Find matches with updated scores
    updated_scores = []
    for match_id, new_match in new_matches.items():
        if match_id in old_matches:
            old_match = old_matches[match_id]
            if old_match['status'] != new_match['status']:
                updated_scores.append({
                    'match': f"{new_match['homeTeam']} vs {new_match['awayTeam']}",
                    'oldStatus': old_match['status'],
                    'newStatus': new_match['status'],
                    'score': f"{new_match['score']['home']}-{new_match['score']['away']}"
                })
    
    if updated_scores:
        print('\n📊 Score updates detected:')
        for update in updated_scores:
            print(f"  • {update['match']}: {update['score']} ({update['oldStatus']} → {update['newStatus']})")
    
    return updated_scores

def main():
    """Main execution function."""
    
    print('🍾 KOSSU 2026 - Match Data Fetcher')
    print('=' * 50)
    print(f'Fetching matches for FIFA World Cup 2026')
    print(f'Time: {datetime.utcnow().isoformat()}Z')
    print()
    
    # Load existing data for comparison
    old_data = load_existing_data()
    
    # Fetch new data from API
    matches = fetch_matches()
    
    if matches is None:
        print('\n❌ Failed to fetch match data')
        # Try to use existing data if available
        if old_data:
            print('⚠ Using existing cached data')
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(old_data, f, indent=2, ensure_ascii=False)
        return False
    
    # Transform the data
    transformed_matches = transform_matches(matches)
    
    # Save to file
    new_data = save_matches(transformed_matches)
    
    # Compare and report changes
    if old_data:
        compare_and_report_changes(old_data, new_data)
    
    print('\n✓ Match data update complete!')
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
