import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
from skyfield.api import load, wgs84

st.set_page_config(layout="wide", page_title="GEOINT Command Center")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- LOCAL DATA LOADER ---
def get_intel():
    air, sats = [], []
    if os.path.exists("data/aircraft.json"):
        with open("data/aircraft.json", "r") as f:
            air = json.load(f)
    if os.path.exists("data/satellites.txt"):
        sats = load.tle_file("data/satellites.txt")
    return air, sats

# --- SIDEBAR (Original Look) ---
with st.sidebar:
    st.title("🛡️ MISSION CTRL")
    show_air = st.toggle("Aerial Intelligence", value=True)
    show_sat = st.toggle("Orbital Intelligence", value=True)
    st.divider()
    st.info("Status: Connected to Cloud Intel")

# --- MAIN DASHBOARD ---
air_data, sat_db = get_intel()
st.title("📡 GLOBAL OPERATIONAL PICTURE")

c1, c2 = st.columns(2)
c1.metric("Live Tracks", len(air_data))
c2.metric("Orbital Assets", len(sat_db))

# --- MAP ENGINE ---
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter", attr="© OSINT")

if show_air and air_data:
    for p in air_data:
        folium.CircleMarker([p['lat'], p['lon']], radius=3, color="#00FFFF", fill=True).add_to(m)

if show_sat and sat_db:
    ts = load.timescale()
    for s in sat_db[:50]: # Show top 50
        try:
            sub = wgs84.latlon_of(s.at(ts.now()))
            folium.RegularPolygonMarker([sub.latitude.degrees, sub.longitude.degrees], 
                                        number_of_sides=3, radius=4, color="#BF40BF").add_to(m)
        except: continue

st_folium(m, width="100%", height=600)
