import requests
import json
import os

def sidhu_style_fetch():
    # Ensure data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GEOINT-App/3.0"}
    
    # 1. FETCH AERIAL (adsb.lol)
    try:
        # Fetching the full feed but saving only a stable subset
        r = requests.get("https://api.adsb.lol/v2/all", headers=headers, timeout=20)
        if r.status_code == 200:
            all_ac = r.json().get('ac', [])
            # Only save planes with valid coordinates to save space
            valid_ac = [ac for ac in all_ac if ac.get('lat') and ac.get('lon')]
            with open("data/aircraft.json", "w") as f:
                json.dump(valid_ac[:400], f) # Cap at 400 for map performance
            print(f"Success: Saved {len(valid_ac[:400])} aircraft.")
    except Exception as e:
        print(f"Aerial Recon Failed: {e}")

    # 2. FETCH ORBITAL (CelesTrak)
    try:
        r = requests.get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle", timeout=20)
        if r.status_code == 200:
            with open("data/satellites.txt", "w") as f:
                f.write(r.text)
            print("Success: Saved Orbital TLE data.")
    except Exception as e:
        print(f"Orbital Recon Failed: {e}")

if __name__ == "__main__":
    sidhu_style_fetch()
