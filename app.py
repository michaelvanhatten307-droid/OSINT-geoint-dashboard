import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import json
import os
import time
from skyfield.api import load, wgs84

# —————————————————––

# PAGE CONFIG — must be the very first Streamlit command

# —————————————————––

st.set_page_config(
layout=“wide”,
page_title=“GEOINT Command Center”,
page_icon=“📡”
)

# —————————————————––

# STYLING

# —————————————————––

st.markdown(”””
<style>
@import url(‘https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600&display=swap’);

```
html, body, .stApp {
    background-color: #080C10;
    color: #C8D8E8;
    font-family: 'Exo 2', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #05080B;
    border-right: 1px solid #1A3A5C;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0D1B2A, #0A1628);
    border: 1px solid #1A3A5C;
    border-radius: 8px;
    padding: 16px;
}
[data-testid="stMetricLabel"] { color: #6A9FC0; font-family: 'Share Tech Mono', monospace; font-size: 0.75rem; letter-spacing: 0.1em; }
[data-testid="stMetricValue"] { color: #00D4FF; font-family: 'Share Tech Mono', monospace; }

/* Title */
h1 { font-family: 'Share Tech Mono', monospace; color: #00D4FF; letter-spacing: 0.05em; }
h2, h3 { font-family: 'Exo 2', sans-serif; color: #6A9FC0; }

/* Status badges */
.status-ok   { color: #00FF88; font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; }
.status-fail  { color: #FF4444; font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; }
.status-warn  { color: #FFAA00; font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; }

/* Divider */
hr { border-color: #1A3A5C; }
</style>
```

“””, unsafe_allow_html=True)

# —————————————————––

# AUTO-REFRESH every 60 seconds

# This re-runs the entire app, picking up any new data files.

# —————————————————––

st_autorefresh(interval=60_000, key=“dashboard_refresh”)

# —————————————————––

# DATA LOADERS — cached so they don’t re-run on every

# tiny UI interaction, only on real data changes.

# —————————————————––

@st.cache_data(ttl=55)  # Cache for 55 seconds (slightly under refresh interval)
def load_aircraft():
path = “data/aircraft.json”
if not os.path.exists(path):
return []
with open(path, “r”) as f:
return json.load(f)

@st.cache_data(ttl=3600)  # Cache for 1 hour — TLEs don’t change often
def load_satellites():
path = “data/satellites.txt”
if not os.path.exists(path):
return []
return load.tle_file(path)

@st.cache_data(ttl=55)
def load_meta():
path = “data/meta.json”
if not os.path.exists(path):
return None
with open(path, “r”) as f:
return json.load(f)

# —————————————————––

# SIDEBAR

# —————————————————––

with st.sidebar:
st.markdown(”### 🛡️ MISSION CTRL”)
st.divider()

```
show_air = st.toggle("✈ Aerial Tracks", value=True)
show_sat = st.toggle("🛰 Orbital Assets", value=True)
sat_limit = st.slider("Max satellites to display", 10, 200, 50, step=10)

st.divider()

# Show data freshness from metadata file
meta = load_meta()
if meta:
    age_seconds = int(time.time() - meta.get("fetched_at", 0))
    age_str = f"{age_seconds}s ago" if age_seconds < 120 else f"{age_seconds // 60}m ago"

    ac_status  = "✅ OK" if meta.get("aircraft_ok")  else "❌ FAILED"
    sat_status = "✅ OK" if meta.get("satellites_ok") else "❌ FAILED"

    st.markdown(f"""
    **Data Status**
    - Aircraft feed: `{ac_status}`
    - Satellite feed: `{sat_status}`
    - Last fetched: `{age_str}`
    - Fetched at: `{meta.get('fetched_at_utc', 'Unknown')}`
    """)

    if age_seconds > 300:
        st.warning("⚠️ Data is over 5 minutes old. Run `python fetcher.py` to refresh.")
else:
    st.error("No data found. Run `python fetcher.py` first.")

st.divider()
st.caption("Auto-refreshes every 60 seconds")
```

# —————————————————––

# LOAD DATA

# —————————————————––

air_data = load_aircraft() if show_air else []
sat_db   = load_satellites() if show_sat else []

# —————————————————––

# HEADER + METRICS

# —————————————————––

st.title(“📡 GEOINT COMMAND CENTER”)

col1, col2, col3, col4 = st.columns(4)
col1.metric(“Live Aircraft Tracks”, len(air_data))
col2.metric(“Orbital Assets (DB)”, len(sat_db))
col3.metric(“Satellites Displayed”, min(sat_limit, len(sat_db)))

# Show data age as a metric too

if meta and meta.get(“fetched_at”):
age_m = (time.time() - meta[“fetched_at”]) / 60
col4.metric(“Data Age”, f”{age_m:.1f} min”)
else:
col4.metric(“Data Age”, “Unknown”)

st.divider()

# —————————————————––

# MAP ENGINE

# —————————————————––

m = folium.Map(
location=[20, 0],
zoom_start=2,
tiles=“CartoDB dark_matter”,
attr=“© OSINT Dashboard”
)

# — AIRCRAFT LAYER —

if show_air and air_data:
aircraft_added = 0
for plane in air_data:
try:
lat = plane.get(‘lat’)
lon = plane.get(‘lon’)
if lat is None or lon is None:
continue

```
        # Build a nice popup with available info
        callsign = plane.get('flight', 'Unknown').strip() or 'Unknown'
        altitude  = plane.get('alt_baro', 'N/A')
        speed     = plane.get('gs', 'N/A')       # ground speed in knots
        squawk    = plane.get('squawk', 'N/A')

        popup_html = f"""
        <div style='font-family:monospace; font-size:12px; color:#00FFFF; background:#0D1B2A; padding:8px; border-radius:4px;'>
            <b>✈ {callsign}</b><br>
            Alt: {altitude} ft<br>
            Speed: {speed} kts<br>
            Squawk: {squawk}
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="#00D4FF",
            fill=True,
            fill_color="#00D4FF",
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=callsign,
        ).add_to(m)
        aircraft_added += 1

    except Exception:
        continue  # Skip any bad records silently
```

# — SATELLITE LAYER —

if show_sat and sat_db:
ts = load.timescale()
now = ts.now()
sat_errors = 0

```
for sat in sat_db[:sat_limit]:
    try:
        geocentric = sat.at(now)
        subpoint = wgs84.subpoint(geocentric)
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees

        popup_html = f"""
        <div style='font-family:monospace; font-size:12px; color:#BF40BF; background:#0D1B2A; padding:8px; border-radius:4px;'>
            <b>🛰 {sat.name}</b><br>
            Lat: {lat:.2f}°<br>
            Lon: {lon:.2f}°
        </div>
        """

        folium.RegularPolygonMarker(
            location=[lat, lon],
            number_of_sides=3,
            radius=5,
            color="#BF40BF",
            fill=True,
            fill_color="#BF40BF",
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=sat.name,
        ).add_to(m)

    except Exception:
        sat_errors += 1
        continue

if sat_errors > 0:
    st.warning(f"⚠️ {sat_errors} satellites could not be plotted (stale TLE data or calculation error).")
```

# Render the map — key= prevents viewport reset on rerun

st_folium(m, width=“100%”, height=620, key=“main_map”)

# —————————————————––

# FOOTER

# —————————————————––

st.divider()
st.caption(“GEOINT Dashboard · Data: ADS-B LOL + CelesTrak · Refresh every 60s · Run fetcher.py to update feeds”)