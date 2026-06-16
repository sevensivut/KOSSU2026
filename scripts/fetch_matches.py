#!/usr/bin/env python3
"""
Fetch real-time match data from the worldcup26.ir API
for the FIFA World Cup 2026.
"""

import os
import json
import requests
import urllib3
from datetime import datetime
from pathlib import Path

# Disable SSL warnings (if you're using verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_BASE_URL = 'https://worldcup26.ir'
DATA_ENDPOINT = '/get/games'
OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'matches.json'

# Create data directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_matches():
    """Fetch match data from worldcup26.ir API."""
    
    url = f'{API_BASE_URL}{DATA_ENDPOINT}'
    
    print(f'🔄 Fetching match data from {url}...')
    
    try:
        # Try with SSL verification disabled
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
        
        data = response.json()
        matches = data.get('games', [])
        
        if not matches:
            print('⚠️ No matches found in response')
            return []
        
        print(f'✓ Successfully fetched {len(matches)} matches')
        return matches
        
    except requests.exceptions.SSLError as e:
        print(f'❌ SSL Error: {e}')
        print('💡 Trying with HTTP instead...')
        # Try HTTP as fallback
        try:
            http_url = f'http://worldcup26.ir{DATA_ENDPOINT}'
            response = requests.get(http_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            matches = data.get('games', [])
            print(f'✓ Successfully fetched {len(matches)} matches via HTTP')
            return matches
        except Exception as http_e:
            print(f'❌ HTTP also failed: {http_e}')
            return None
            
    except requests.exceptions.RequestException as e:
        print(f'❌ Request failed: {e}')
        return None
    except json.JSONDecodeError as e:
        print(f'❌ Error parsing JSON: {e}')
        print(f'📡 Response text: {response.text[:200]}...')
        return None

def transform_matches(matches):
    """Transform raw API data into your application's expected format."""
    transformed = []
    
    for match in matches:
        # Handle different possible field names
        home_score = match.get('home_score', match.get('homeScore', 0))
        away_score = match.get('away_score', match.get('awayScore', 0))
        finished = match.get('finished', match.get('status', ''))
        
        # Determine status
        if finished == 'TRUE' or finished == 'true' or finished == 'Finished':
            status = 'FINISHED'
        elif finished == 'LIVE' or finished == 'In Progress':
            status = 'IN_PLAY'
        else:
            status = 'SCHEDULED'
        
        transformed_match = {
            'id': match.get('id', match.get('game_id')),
            'date': match.get('local_date', match.get('date', '')),
            'homeTeam': match.get('home_team_name_en', match.get('homeTeamName', 'Unknown')),
            'homeTeamId': match.get('home_team_id', match.get('homeTeamId')),
            'awayTeam': match.get('away_team_name_en', match.get('awayTeamName', 'Unknown')),
            'awayTeamId': match.get('away_team_id', match.get('awayTeamId')),
            'status': status,
            'score': {
                'home': home_score,
                'away': away_score
            },
            'stage': match.get('type', match.get('stage', 'group')),
            'group': match.get('group', ''),
            'stadium': match.get('stadium_id', match.get('stadium', '')),
            'matchday': match.get('matchday', '')
        }
        
        # Add result based on status and score
        if status == 'FINISHED':
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
            print(f'⚠️ Warning: Could not load existing data: {e}')
    
    return None

def save_matches(matches):
    """Save transformed matches to JSON file."""
    output_data = {
        'updatedAt': datetime.utcnow().isoformat() + 'Z',
        'competitionName': 'FIFA World Cup 2026',
        'matchCount': len(matches),
        'playedCount': len([m for m in matches if m['status'] == 'FINISHED']),
        'inPlayCount': len([m for m in matches if m['status'] == 'IN_PLAY']),
        'upcomingCount': len([m for m in matches if m['status'] not in ['FINISHED', 'IN_PLAY']]),
        'matches': matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f'✓ Saved {len(matches)} matches to {OUTPUT_FILE}')
    print(f'  - Played: {output_data["playedCount"]}')
    print(f'  - In Play: {output_data["inPlayCount"]}')
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
            if (old_match.get('score') != new_match.get('score') or 
                old_match.get('status') != new_match.get('status')):
                updated_scores.append({
                    'match': f"{new_match['homeTeam']} vs {new_match['awayTeam']}",
                    'oldStatus': old_match.get('status', 'UNKNOWN'),
                    'newStatus': new_match.get('status', 'UNKNOWN'),
                    'score': f"{new_match['score']['home']}-{new_match['score']['away']}"
                })
    
    if updated_scores:
        print('\n📊 Updates detected:')
        for update in updated_scores:
            print(f"  • {update['match']}: {update['score']} ({update['oldStatus']} → {update['newStatus']})")
    else:
        print('\n📊 No score updates detected')
    
    return updated_scores

def main():
    """Main execution function."""
    print('🏆 World Cup 2026 - Match Data Fetcher')
    print('=' * 50)
    print(f'Time: {datetime.utcnow().isoformat()}Z')
    print()
    
    # Load existing data for comparison
    old_data = load_existing_data()
    
    # Fetch new data
    matches = fetch_matches()
    
    if matches is None:
        print('\n❌ Failed to fetch match data')
        return False
    
    if not matches:
        print('\n⚠️ No matches returned from API')
        return False
    
    # Transform the data
    transformed_matches = transform_matches(matches)
    
    # Save to file
    new_data = save_matches(transformed_matches)
    
    # Compare and report changes
    if old_data:
        compare_and_report_changes(old_data, new_data)
    
    print('\n✅ Match data update complete!')
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
