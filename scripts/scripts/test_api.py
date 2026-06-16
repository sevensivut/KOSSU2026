#!/usr/bin/env python3
"""
Test API-Football connection and see what data is available
"""

import os
import json
import requests
from datetime import datetime

API_KEY = os.getenv('RAPIDAPI_KEY')

def test_api():
    print('🔍 Testing API-Football Connection')
    print('=' * 50)
    
    if not API_KEY:
        print('❌ No RAPIDAPI_KEY found!')
        return
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Test 1: Check available leagues
    print('\n📊 Checking available leagues...')
    try:
        response = requests.get('https://v3.football.api-sports.io/leagues', 
                               headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ API is working! Status: {response.status_code}')
            print(f'📊 Total leagues in response: {len(data.get("response", []))}')
            
            # Look for World Cup
            world_cup = None
            for league in data.get('response', []):
                league_data = league.get('league', {})
                if 'world' in league_data.get('name', '').lower() or 'cup' in league_data.get('name', '').lower():
                    print(f"  Found: {league_data.get('name')} (ID: {league_data.get('id')})")
                    if 'FIFA World Cup' in league_data.get('name', ''):
                        world_cup = league_data
                        break
            
            if world_cup:
                print(f"\n✅ Found FIFA World Cup! ID: {world_cup.get('id')}")
            else:
                print("\n⚠️ Could not find FIFA World Cup in leagues list")
        else:
            print(f'❌ API error: {response.status_code}')
            print(f'Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Request failed: {e}')
    
    # Test 2: Check matches for today
    print(f'\n📅 Checking matches for {datetime.utcnow().strftime("%Y-%m-%d")}...')
    try:
        params = {
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'league': '1'  # Try FIFA World Cup ID 1
        }
        response = requests.get('https://v3.football.api-sports.io/fixtures', 
                               headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('response', [])
            print(f'✅ Found {len(matches)} matches for today')
            if matches:
                for match in matches[:3]:
                    home = match.get('teams', {}).get('home', {}).get('name', '')
                    away = match.get('teams', {}).get('away', {}).get('name', '')
                    status = match.get('status', {}).get('short', '')
                    print(f"  - {home} vs {away} ({status})")
            else:
                print('  ℹ️ No matches today')
        else:
            print(f'❌ API error: {response.status_code}')
    except Exception as e:
        print(f'❌ Request failed: {e}')
    
    # Test 3: Check live matches
    print('\n🔴 Checking live matches...')
    try:
        response = requests.get('https://v3.football.api-sports.io/fixtures', 
                               headers=headers, 
                               params={'live': 'all'}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('response', [])
            print(f'✅ Found {len(matches)} live matches')
            if matches:
                for match in matches[:3]:
                    home = match.get('teams', {}).get('home', {}).get('name', '')
                    away = match.get('teams', {}).get('away', {}).get('name', '')
                    goals = match.get('goals', {})
                    print(f"  - {home} {goals.get('home', 0)} - {goals.get('away', 0)} {away}")
        else:
            print(f'❌ API error: {response.status_code}')
    except Exception as e:
        print(f'❌ Request failed: {e}')
    
    # Test 4: Check if FIFA World Cup 2026 exists
    print('\n⚽ Checking FIFA World Cup 2026...')
    try:
        params = {
            'league': '1',
            'season': '2026'
        }
        response = requests.get('https://v3.football.api-sports.io/fixtures', 
                               headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('response', [])
            print(f'✅ Found {len(matches)} matches for World Cup 2026')
            if matches:
                for match in matches[:3]:
                    home = match.get('teams', {}).get('home', {}).get('name', '')
                    away = match.get('teams', {}).get('away', {}).get('name', '')
                    date = match.get('fixture', {}).get('date', '')[:10]
                    print(f"  - {home} vs {away} ({date})")
        else:
            print(f'❌ API error: {response.status_code}')
    except Exception as e:
        print(f'❌ Request failed: {e}')
    
    print('\n' + '=' * 50)
    print('✅ Test complete!')

if __name__ == '__main__':
    test_api()
