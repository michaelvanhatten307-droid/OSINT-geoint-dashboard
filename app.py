import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import json, os, time
from skyfield.api import load, wgs84

st.set_page_config(layout='wide', page_title='GEOINT', page_icon='G')
st_autorefresh(interval=60_000, key='dashboard_refresh')

@st.cache_data(ttl=55)
def load_aircraft():
    if not os.path.exists('data/aircraft.json'): return []
    with open('data/aircraft.json') as f: return json.load(f)

@st.cache_data(ttl=3600)
def load_satellites():
    if not os.path.exists('data/satellites.txt'): return []
    return load.tle_file('data/satellites.txt')

@st.cache_data(ttl=55)
def load_meta():
    if not os.path.exists('data/meta.json'): return None
    with open('data/meta.json') as f: return json.load(f)

meta = load_meta()
air_data = load_aircraft()
sat_db = load_satellites()

with st.sidebar:
    st.title('MISSION CTRL')
    show_air = st.toggle('Aerial Tracks', value=True)
    show_sat = st.toggle('Orbital Assets', value=True)
    sat_limit = st.slider('Satellites', 10, 200, 60, step=10)
    st.divider()
    if meta:
        age_s = int(time.time() - meta.get('fetched_at', 0))
        age_str = f'{age_s}s ago' if age_s < 120 else f'{age_s//60}m ago'
        st.write('Aircraft OK:', meta.get('aircraft_ok', False))
        st.write('Satellites OK:', meta.get('satellites_ok', False))
        st.write('Updated:', age_str)
        if age_s > 300: st.warning('Data stale - run fetcher.py')
    else:
        st.error('No data - run fetcher.py')

st.title('GEOINT COMMAND CENTER')
c1,c2,c3,c4 = st.columns(4)
c1.metric('LIVE AIRCRAFT', len(air_data) if show_air else 0)
c2.metric('ORBITAL ASSETS', len(sat_db) if show_sat else 0)
c3.metric('SATS DISPLAYED', min(sat_limit, len(sat_db)) if show_sat else 0)
if meta and meta.get('fetched_at'):
    c4.metric('DATA AGE', f"{(time.time()-meta['fetched_at'])/60:.1f} MIN")
else:
    c4.metric('DATA AGE', 'UNKNOWN')
st.divider()
map_col, panel_col = st.columns([3,1])
with map_col:
    m = folium.Map(location=[30,0], zoom_start=2, tiles='CartoDB dark_matter', attr='GEOINT')
    if show_air and air_data:
        for plane in air_data:
            try:
                lat,lon = plane.get('lat'), plane.get('lon')
                if lat is None or lon is None: continue
                cs = plane.get('flight','???').strip() or '???'
                alt = plane.get('alt_baro','N/A')
                spd = plane.get('gs','N/A')
                folium.CircleMarker(location=[lat,lon], radius=3, color='#00FF41',
                    fill=True, fill_color='#00FF41', fill_opacity=0.9,
                    tooltip=cs).add_to(m)
            except: continue
    if show_sat and sat_db:
        ts = load.timescale()
        now = ts.now()
        for sat in sat_db[:sat_limit]:
            try:
                sp = wgs84.subpoint(sat.at(now))
                folium.RegularPolygonMarker(
                    location=[sp.latitude.degrees, sp.longitude.degrees],
                    number_of_sides=3, radius=5, color='#00FFD1',
                    fill=True, fill_color='#00FFD1', fill_opacity=0.8,
                    tooltip=sat.name).add_to(m)
            except: continue
    st_folium(m, width='100%', height=580, key='main_map')
with panel_col:
    st.subheader('LIVE TRACKS')
    if air_data:
        featured = sorted([a for a in air_data if a.get('flight','').strip()],
            key=lambda x: x.get('alt_baro',0) if isinstance(x.get('alt_baro'),(int,float)) else 0,
            reverse=True)[:20]
        for plane in featured:
            cs = plane.get('flight','???').strip()
            alt = plane.get('alt_baro','?')
            spd = plane.get('gs','?')
            st.markdown(f'**{cs}** | {alt}ft | {spd}kts')
            st.divider()
    else:
        st.warning('No tracks - run fetcher.py')
st.caption('GEOINT v2.0 | ADSB.LOL + CELESTRAK | PASSIVE OSINT')
