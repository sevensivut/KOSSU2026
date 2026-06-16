#!/usr/bin/env python3
"""
Find the correct FIFA World Cup league ID and matches
"""

import os
import json
import requests
from datetime import datetime

API_KEY = os.getenv('RAPIDAPI_KEY')

def find_world_cup():
    print('🔍 Finding FIFA World Cup in API-Football')
    print('=' * 50)
    
    if not API_KEY:
        print('❌ No RAPIDAPI_KEY found!')
        return
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Search all leagues for World Cup
    print('\n📊 Searching for FIFA World Cup...')
    try:
        response = requests.get('https://v3.football.api-sports.io/leagues', 
                               headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Find World Cup leagues
            world_cup_leagues = []
            for league in data.get('response', []):
                league_data = league.get('league', {})
                name = league_data.get('name', '').lower()
                if 'world cup' in name or 'worldcup' in name:
                    world_cup_leagues.append({
                        'id': league_data.get('id'),
                        'name': league_data.get('name'),
                        'type': league_data.get('type'),
                        'season': league.get('seasons', [{}])[0].get('year') if league.get('seasons') else None
                    })
            
            if world_cup_leagues:
                print(f"\n✅ Found {len(world_cup_leagues)} World Cup leagues:")
                for wc in world_cup_leagues:
                    print(f"  - {wc['name']} (ID: {wc['id']}, Season: {wc['season']})")
            else:
                print("\n❌ No World Cup leagues found!")
                print("   Let's look at all leagues with 'world' in the name:")
                for league in data.get('response', []):
                    league_data = league.get('league', {})
                    if 'world' in league_data.get('name', '').lower():
                        print(f"  - {league_data.get('name')} (ID: {league_data.get('id')})")
        else:
            print(f'❌ API error: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Request failed: {e}')
    
    # Search for 2026 matches directly
    print('\n⚽ Searching for matches with "World Cup" in the name...')
    try:
        response = requests.get('https://v3.football.api-sports.io/fixtures', 
                               headers=headers, 
                               params={'date': '2026-06-17'}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = data.get('response', [])
            print(f'✅ Found {len(matches)} matches for today')
            
            if matches:
                print('\n📋 Today\'s matches:')
                for match in matches:
                    home = match.get('teams', {}).get('home', {}).get('name', '')
                    away = match.get('teams', {}).get('away', {}).get('name', '')
                    league = match.get('league', {}).get('name', '')
                    status = match.get('status', {}).get('short', '')
                    print(f"  - {home} vs {away} ({league}) - Status: {status}")
        else:
            print(f'❌ API error: {response.status_code}')
    except Exception as e:
        print(f'❌ Request failed: {e}')
    
    print('\n' + '=' * 50)

if __name__ == '__main__':
    find_world_cup()
