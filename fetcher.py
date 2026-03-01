import requests
import json
import os
import time

def fetch_all_intel():
# Fetches live aircraft and satellite data and saves it to the /data folder.
# Run this manually first, then let the dashboard handle auto-refreshing.

```
# Make sure the data folder exists
if not os.path.exists('data'):
    os.makedirs('data')

headers = {"User-Agent": "GEOINT-Dashboard/1.0"}
status = {"aircraft": False, "satellites": False}
to_save = []

# -------------------------
# 1. FETCH AIRCRAFT (ADS-B)
# -------------------------
print("Fetching aircraft data...")
try:
    r = requests.get("https://api.adsb.lol/v2/all", headers=headers, timeout=20)
    r.raise_for_status()

    all_aircraft = r.json().get('ac', [])

    # Filter: only keep planes with valid (non-None) coordinates
    valid_aircraft = [
        ac for ac in all_aircraft
        if ac.get('lat') is not None and ac.get('lon') is not None
    ]

    # Cap at 500 for map performance, save to file
    to_save = valid_aircraft[:500]
    with open("data/aircraft.json", "w") as f:
        json.dump(to_save, f)

    status["aircraft"] = True
    print(f"  Success: Saved {len(to_save)} aircraft.")

except Exception as e:
    print(f"  Aircraft fetch failed: {e}")

# ----------------------------
# 2. FETCH SATELLITES (TLE)
# ----------------------------
tle_path = "data/satellites.txt"
tle_age_seconds = float('inf')

if os.path.exists(tle_path):
    tle_age_seconds = time.time() - os.path.getmtime(tle_path)

if tle_age_seconds < 3 * 3600:
    age_minutes = int(tle_age_seconds / 60)
    print(f"Skipping satellite fetch - TLE data is only {age_minutes} min old (refreshes every 3 hrs).")
    status["satellites"] = True
else:
    print("Fetching satellite TLE data from CelesTrak...")
    try:
        r = requests.get(
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
            timeout=30
        )
        r.raise_for_status()

        with open(tle_path, "w") as f:
            f.write(r.text)

        status["satellites"] = True
        print("  Success: Saved satellite TLE data.")

    except Exception as e:
        print(f"  Satellite fetch failed: {e}")

# ----------------------------
# 3. WRITE METADATA SIDECAR
# ----------------------------
meta = {
    "fetched_at": time.time(),
    "fetched_at_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "aircraft_count": len(to_save) if status["aircraft"] else 0,
    "aircraft_ok": status["aircraft"],
    "satellites_ok": status["satellites"],
}
with open("data/meta.json", "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nDone. Aircraft={'OK' if status['aircraft'] else 'FAILED'}, Satellites={'OK' if status['satellites'] else 'FAILED'}")
return status
```

# Run directly with: python fetcher.py

if __name__ == “__main__”:
fetch_all_intel()