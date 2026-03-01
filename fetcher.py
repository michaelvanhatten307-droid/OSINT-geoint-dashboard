import requests
import json
import os
import time

def fetch_all_intel():
    if not os.path.exists('data'):
        os.makedirs('data')
    headers = {'User-Agent': 'GEOINT-Dashboard/1.0'}
    status = {'aircraft': False, 'satellites': False}
    to_save = []
    print('Fetching aircraft data...')
    try:
        r = requests.get('https://api.adsb.lol/v2/all', headers=headers, timeout=20)
        r.raise_for_status()
        all_aircraft = r.json().get('ac', [])
        to_save = [a for a in all_aircraft if a.get('lat') is not None and a.get('lon') is not None][:500]
        with open('data/aircraft.json', 'w') as f2:
            json.dump(to_save, f2)
        status['aircraft'] = True
        print(f'  Saved {len(to_save)} aircraft.')
    except Exception as e:
        print(f'  Aircraft failed: {e}')
    tle_path = 'data/satellites.txt'
    tle_age = float('inf')
    if os.path.exists(tle_path):
        tle_age = time.time() - os.path.getmtime(tle_path)
    if tle_age < 10800:
        print(f'Skipping TLE fetch, only {int(tle_age/60)} min old.')
        status['satellites'] = True
    else:
        print('Fetching satellite TLE data...')
        try:
            r = requests.get('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle', timeout=30)
            r.raise_for_status()
            with open(tle_path, 'w') as f2:
                f2.write(r.text)
            status['satellites'] = True
            print('  Saved satellite TLE data.')
        except Exception as e:
            print(f'  Satellites failed: {e}')
    meta = {
        'fetched_at': time.time(),
        'fetched_at_utc': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'aircraft_count': len(to_save),
        'aircraft_ok': status['aircraft'],
        'satellites_ok': status['satellites'],
    }
    with open('data/meta.json', 'w') as f2:
        json.dump(meta, f2, indent=2)
    print(f'Done. Aircraft={status["aircraft"]}, Satellites={status["satellites"]}')
    return status

if __name__ == '__main__':
    fetch_all_intel()
