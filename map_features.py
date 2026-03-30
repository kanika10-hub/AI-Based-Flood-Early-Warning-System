import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import requests
from datetime import datetime

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="FloodSense AI · Map",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
#  GLOBAL CSS  (matches app1.py theme)
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Mono', monospace;
    background-color: #060d1a;
    color: #e8f4ff;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.section-label {
    font-size: 0.6rem; letter-spacing: 4px; color: #5a7a9a;
    text-transform: uppercase; margin-bottom: 14px;
    display: flex; align-items: center; gap: 10px;
}
.section-label::after {
    content:''; flex:1; height:1px; background: rgba(0,180,255,0.12);
}

.zone-card {
    background: #0b1628;
    border: 1px solid rgba(0,180,255,0.15);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 14px;
    cursor: pointer;
    transition: all 0.2s;
}
.zone-card:hover {
    border-color: rgba(0,180,255,0.4);
    background: #0f1e35;
}
.zone-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem; font-weight: 700; color: #fff;
}
.zone-sub {
    font-size: 0.65rem; letter-spacing: 1px;
    color: #5a7a9a; margin-top: 4px;
}

.layer-toggle {
    background: #0b1628;
    border: 1px solid rgba(0,180,255,0.1);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}

.stButton > button {
    width: 100%;
    background: transparent !important;
    border: 1px solid #00b4ff !important;
    color: #00b4ff !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 3px !important;
    padding: 12px !important;
    border-radius: 10px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,#00b4ff,#00ffc8) !important;
    color: #000 !important;
    border-color: transparent !important;
}

.info-pill {
    display: inline-block;
    background: rgba(0,180,255,0.08);
    border: 1px solid rgba(0,180,255,0.2);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.6rem;
    letter-spacing: 2px;
    color: #00b4ff;
    margin-bottom: 16px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0b1628; border-radius: 10px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #5a7a9a !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important; letter-spacing: 2px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,180,255,0.1) !important;
    color: #00b4ff !important; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  DATA — CHENNAI ZONES
# ─────────────────────────────────────────
ZONES = {
    "All of Chennai": {
        "center": [13.0827, 80.2707],
        "zoom": 11,
        "desc": "Full city overview"
    },
    "North Chennai": {
        "center": [13.1700, 80.2800],
        "zoom": 12,
        "desc": "Includes Tiruvottiyur, Manali, Ennore"
    },
    "Central Chennai": {
        "center": [13.0827, 80.2707],
        "zoom": 13,
        "desc": "Includes T.Nagar, Egmore, Nungambakkam"
    },
    "South Chennai": {
        "center": [12.9500, 80.2000],
        "zoom": 12,
        "desc": "Includes Velachery, Tambaram, Pallavaram"
    },
    "West Chennai": {
        "center": [13.0600, 80.1800],
        "zoom": 12,
        "desc": "Includes Ambattur, Avadi, Poonamallee"
    },
    "Coastal Belt": {
        "center": [13.0827, 80.2950],
        "zoom": 12,
        "desc": "Marina to Thiruvanmiyur coastline"
    },
}

# ─────────────────────────────────────────
#  DATA — FLOOD RISK ZONES
# ─────────────────────────────────────────
FLOOD_ZONES = [
    # [lat, lon, name, risk_level, color, description]
    [13.0050, 80.2207, "Velachery", "HIGH", "#ff3b3b", "Chronic flooding due to Pallikaranai marsh encroachment"],
    [13.0200, 80.2100, "Mudichur", "HIGH", "#ff3b3b", "Low-lying area near Adyar river tributary"],
    [13.0450, 80.2450, "Adyar", "HIGH", "#ff3b3b", "Adyar river overflow zone — 2015 floods epicentre"],
    [13.0600, 80.2300, "Saidapet", "HIGH", "#ff3b3b", "Adjacent to Adyar river, poor drainage"],
    [13.1100, 80.2850, "Tondiarpet", "HIGH", "#ff3b3b", "Coastal low-lying area, storm surge risk"],
    [13.1300, 80.2900, "Royapuram", "HIGH", "#ff3b3b", "Fishing harbour zone, tidal flooding risk"],
    [13.0900, 80.2400, "Perambur", "MEDIUM", "#ffaa00", "Moderate drainage issues, low-lying pockets"],
    [13.0750, 80.2600, "Kolathur", "MEDIUM", "#ffaa00", "Near Korattur lake, periodic inundation"],
    [13.0300, 80.2600, "Pallikaranai", "HIGH", "#ff3b3b", "Marshland area, severe flood risk"],
    [13.1500, 80.2300, "Ambattur", "MEDIUM", "#ffaa00", "Industrial area with drainage bottlenecks"],
    [13.0827, 80.2707, "Egmore", "LOW", "#00e87a", "Central area, relatively elevated"],
    [13.0600, 80.2700, "T.Nagar", "LOW", "#00e87a", "Commercial hub, moderate elevation"],
    [13.0100, 80.2500, "Tambaram", "MEDIUM", "#ffaa00", "Suburban, seasonal flooding near tanks"],
    [13.1800, 80.2700, "Tiruvottiyur", "HIGH", "#ff3b3b", "Coastal industrial zone, flood prone"],
    [13.0200, 80.2700, "Sholinganallur", "MEDIUM", "#ffaa00", "IT corridor, near Buckingham canal"],
    [13.0680, 80.2785, "Triplicane", "MEDIUM", "#ffaa00", "Near coast, drainage stress during NE monsoon"],
    [12.9800, 80.2200, "Chromepet", "LOW", "#00e87a", "Moderate elevation, decent drainage"],
    [13.1200, 80.2100, "Poonamallee", "LOW", "#00e87a", "Elevated suburb, low flood risk"],
]

# ─────────────────────────────────────────
#  DATA — RESERVOIRS
# ─────────────────────────────────────────
RESERVOIRS = [
    {
        "name": "Chembarambakkam Lake",
        "lat": 13.0050, "lon": 80.0780,
        "capacity_mcm": 3645,
        "current_pct": 72,
        "risk": "MEDIUM",
        "color": "#ffaa00",
        "note": "Primary flood-control reservoir. Major releases led to 2015 Chennai floods."
    },
    {
        "name": "Poondi Reservoir",
        "lat": 13.3500, "lon": 79.9800,
        "capacity_mcm": 3231,
        "current_pct": 58,
        "risk": "LOW",
        "color": "#00e87a",
        "note": "Largest reservoir supplying Chennai. On Kosasthalaiyar river."
    },
    {
        "name": "Red Hills Lake",
        "lat": 13.1950, "lon": 80.1800,
        "capacity_mcm": 3300,
        "current_pct": 65,
        "risk": "LOW",
        "color": "#00e87a",
        "note": "Major drinking water source. Located north of Chennai."
    },
    {
        "name": "Sholavaram Lake",
        "lat": 13.2300, "lon": 80.1900,
        "capacity_mcm": 1485,
        "current_pct": 45,
        "risk": "LOW",
        "color": "#00e87a",
        "note": "Feeds Red Hills. Moderate capacity."
    },
    {
        "name": "Pallikaranai Marsh",
        "lat": 12.9450, "lon": 80.2200,
        "capacity_mcm": None,
        "current_pct": None,
        "risk": "HIGH",
        "color": "#ff3b3b",
        "note": "Protected wetland acting as natural flood buffer. Encroachment has drastically reduced capacity."
    },
]

# ─────────────────────────────────────────
#  DATA — EVACUATION CENTRES
# ─────────────────────────────────────────
EVACUATION_CENTERS = [
    {"name": "Nehru Indoor Stadium", "lat": 13.0827, "lon": 80.2785, "capacity": 5000, "type": "Stadium"},
    {"name": "Jawaharlal Nehru Stadium", "lat": 13.0600, "lon": 80.2500, "capacity": 40000, "type": "Stadium"},
    {"name": "Anna University Campus", "lat": 13.0104, "lon": 80.2340, "capacity": 3000, "type": "University"},
    {"name": "Rajiv Gandhi Govt Hospital", "lat": 13.1000, "lon": 80.2760, "capacity": 1500, "type": "Hospital"},
    {"name": "Coimbatore District School (Tambaram)", "lat": 12.9249, "lon": 80.1000, "capacity": 800, "type": "School"},
    {"name": "Velachery Govt Higher Secondary School", "lat": 13.0050, "lon": 80.2207, "capacity": 600, "type": "School"},
    {"name": "Ambattur Industrial School", "lat": 13.1135, "lon": 80.1548, "capacity": 700, "type": "School"},
    {"name": "Tondiarpet Community Hall", "lat": 13.1300, "lon": 80.2980, "capacity": 500, "type": "Community Hall"},
    {"name": "Sholinganallur Govt School", "lat": 12.9010, "lon": 80.2279, "capacity": 400, "type": "School"},
    {"name": "Perambur Higher Secondary School", "lat": 13.1100, "lon": 80.2384, "capacity": 600, "type": "School"},
]

# ─────────────────────────────────────────
#  RAIN HEATMAP DATA (static representative)
# ─────────────────────────────────────────
RAIN_HEATMAP_POINTS = [
    [13.1800, 80.2700, 0.9],  # Tiruvottiyur — coastal, heavy
    [13.1300, 80.2900, 0.85], # Royapuram
    [13.1100, 80.2850, 0.8],  # Tondiarpet
    [13.0827, 80.2950, 0.75], # Marina Coast
    [13.0680, 80.2785, 0.7],  # Triplicane
    [13.0450, 80.2450, 0.8],  # Adyar
    [13.0050, 80.2207, 0.9],  # Velachery
    [13.0200, 80.2100, 0.85], # Mudichur
    [13.0300, 80.2600, 0.88], # Pallikaranai
    [13.0200, 80.2700, 0.7],  # Sholinganallur
    [13.0900, 80.2400, 0.5],  # Perambur
    [13.0750, 80.2600, 0.55], # Kolathur
    [13.1500, 80.2300, 0.45], # Ambattur
    [13.0827, 80.2707, 0.4],  # Central
    [13.0600, 80.2700, 0.35], # T.Nagar
    [13.0600, 80.2300, 0.45], # Saidapet
    [12.9800, 80.2200, 0.3],  # Chromepet
    [13.1200, 80.2100, 0.25], # Poonamallee
    [13.0100, 80.2500, 0.5],  # Tambaram
    [13.3500, 79.9800, 0.6],  # Poondi area
]

# ─────────────────────────────────────────
#  OPEN-METEO FETCH
# ─────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_rain_today():
    try:
        params = {
            "latitude": 13.0827, "longitude": 80.2707,
            "daily": "precipitation_sum",
            "timezone": "Asia/Kolkata",
            "past_days": 1, "forecast_days": 1,
        }
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        mm = data["daily"]["precipitation_sum"][-1] or 0.0
        return round(mm, 1)
    except:
        return None

# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0b1628,#0f2040);border:1px solid rgba(0,180,255,0.15);
border-radius:16px;padding:24px 32px;margin-bottom:24px;position:relative;overflow:hidden">
<div style="position:absolute;top:0;left:0;right:0;height:2px;
background:linear-gradient(90deg,transparent,#00b4ff,#00ffc8,transparent)"></div>
<div style="font-size:0.6rem;letter-spacing:4px;color:#00b4ff;margin-bottom:6px">◈ FLOOD INTELLIGENCE PLATFORM · MAP MODULE</div>
<div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#fff;line-height:1">
    Flood<span style="color:#00b4ff">Sense</span> <span style="color:#00ffc8">Maps</span>
</div>
<div style="color:#5a7a9a;font-size:0.65rem;letter-spacing:2px;margin-top:6px">
    ZONE SELECTOR · FLOOD RISK · RESERVOIRS · RAIN HEATMAP · EVACUATION ROUTES
</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  LAYOUT
# ─────────────────────────────────────────
sidebar_col, map_col = st.columns([1, 2.8], gap="large")

with sidebar_col:

    # ── STEP 1: ZONE SELECTOR ──
    st.markdown('<div class="section-label">📍 STEP 1 · SELECT ZONE</div>', unsafe_allow_html=True)

    selected_zone = st.selectbox(
        "Choose a zone to focus on",
        list(ZONES.keys()),
        index=0,
        label_visibility="collapsed"
    )

    zone_data = ZONES[selected_zone]
    st.markdown(f"""
    <div style="background:#0f1e35;border:1px solid rgba(0,180,255,0.1);border-radius:10px;
    padding:10px 14px;margin-bottom:20px;font-size:0.7rem;color:#5a7a9a">
        📌 {zone_data['desc']}
    </div>
    """, unsafe_allow_html=True)

    # ── STEP 2: LAYER SELECTOR ──
    st.markdown('<div class="section-label">🗺 STEP 2 · CHOOSE LAYERS</div>', unsafe_allow_html=True)

    show_flood_zones   = st.checkbox("🔴 Flood Risk Zones", value=True)
    show_reservoirs    = st.checkbox("💧 Reservoir Locations", value=False)
    show_rain_heatmap  = st.checkbox("🌧 Live Rain Heatmap", value=False)
    show_evacuation    = st.checkbox("🚨 Evacuation Centres", value=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── LEGEND ──
    if show_flood_zones or show_reservoirs:
        st.markdown('<div class="section-label">🎨 LEGEND</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#0b1628;border:1px solid rgba(0,180,255,0.1);border-radius:10px;padding:14px 16px;font-size:0.68rem;line-height:2">
            <div><span style="color:#ff3b3b">●</span> HIGH RISK / CRITICAL</div>
            <div><span style="color:#ffaa00">●</span> MEDIUM RISK</div>
            <div><span style="color:#00e87a">●</span> LOW RISK / SAFE</div>
            <div><span style="color:#00b4ff">●</span> EVACUATION CENTRE</div>
            <div><span style="color:#00ffc8">💧</span> RESERVOIR</div>
        </div>
        """, unsafe_allow_html=True)

    # ── LIVE RAIN ──
    st.markdown("<br>", unsafe_allow_html=True)
    rain_mm = fetch_rain_today()
    if rain_mm is not None:
        rain_color = "#ff3b3b" if rain_mm > 100 else "#ffaa00" if rain_mm > 40 else "#00e87a"
        st.markdown(f"""
        <div style="background:#0b1628;border:1px solid rgba(0,180,255,0.1);border-radius:10px;
        padding:14px 16px;text-align:center">
            <div style="font-size:0.55rem;letter-spacing:3px;color:#5a7a9a;margin-bottom:4px">LIVE · CHENNAI RAINFALL</div>
            <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:{rain_color}">{rain_mm} mm</div>
            <div style="font-size:0.55rem;color:#5a7a9a;margin-top:2px">TODAY · OPEN-METEO</div>
        </div>
        """, unsafe_allow_html=True)

with map_col:
    st.markdown('<div class="section-label">🗺 INTERACTIVE MAP</div>', unsafe_allow_html=True)

    # Build folium map
    m = folium.Map(
        location=zone_data["center"],
        zoom_start=zone_data["zoom"],
        tiles="CartoDB dark_matter",
        control_scale=True
    )

    # ── LAYER: FLOOD RISK ZONES ──
    if show_flood_zones:
        flood_group = folium.FeatureGroup(name="Flood Risk Zones")
        for zone in FLOOD_ZONES:
            lat, lon, name, risk, color, desc = zone
            radius = 900 if risk == "HIGH" else 700 if risk == "MEDIUM" else 500
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius / 100,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.35,
                popup=folium.Popup(
                    f"""<div style='font-family:monospace;font-size:12px;min-width:180px'>
                    <b style='color:{color}'>{name}</b><br>
                    <span style='color:#888;font-size:10px'>RISK LEVEL</span><br>
                    <b style='color:{color};font-size:14px'>{risk}</b><br>
                    <hr style='margin:4px 0'>
                    <span style='font-size:10px'>{desc}</span>
                    </div>""",
                    max_width=220
                ),
                tooltip=f"{name} · {risk} RISK"
            ).add_to(flood_group)
        flood_group.add_to(m)

    # ── LAYER: RESERVOIRS ──
    if show_reservoirs:
        res_group = folium.FeatureGroup(name="Reservoirs")
        for r in RESERVOIRS:
            cap_text = f"{r['current_pct']}% full · {r['capacity_mcm']} MCM" if r['capacity_mcm'] else "Wetland buffer"
            folium.Marker(
                location=[r["lat"], r["lon"]],
                popup=folium.Popup(
                    f"""<div style='font-family:monospace;font-size:12px;min-width:200px'>
                    <b style='color:{r['color']}'>💧 {r['name']}</b><br>
                    <span style='color:#888;font-size:10px'>CAPACITY STATUS</span><br>
                    <b style='font-size:13px;color:{r['color']}'>{cap_text}</b><br>
                    <hr style='margin:4px 0'>
                    <span style='font-size:10px'>{r['note']}</span>
                    </div>""",
                    max_width=240
                ),
                tooltip=f"💧 {r['name']}",
                icon=folium.Icon(
                    color="red" if r["risk"] == "HIGH" else "orange" if r["risk"] == "MEDIUM" else "blue",
                    icon="tint",
                    prefix="fa"
                )
            ).add_to(res_group)
        res_group.add_to(m)

    # ── LAYER: RAIN HEATMAP ──
    if show_rain_heatmap:
        heat_group = folium.FeatureGroup(name="Rain Heatmap")
        # Scale intensity by today's rain
        multiplier = min((rain_mm or 10) / 50, 2.0)
        scaled_points = [[p[0], p[1], min(p[2] * multiplier, 1.0)] for p in RAIN_HEATMAP_POINTS]
        HeatMap(
            scaled_points,
            radius=35,
            blur=25,
            min_opacity=0.3,
            gradient={0.2: "#00b4ff", 0.5: "#ffaa00", 0.8: "#ff3b3b", 1.0: "#ff0000"}
        ).add_to(heat_group)
        heat_group.add_to(m)

    # ── LAYER: EVACUATION CENTRES ──
    if show_evacuation:
        evac_group = folium.FeatureGroup(name="Evacuation Centres")
        for ec in EVACUATION_CENTERS:
            folium.Marker(
                location=[ec["lat"], ec["lon"]],
                popup=folium.Popup(
                    f"""<div style='font-family:monospace;font-size:12px;min-width:180px'>
                    <b style='color:#00b4ff'>🚨 {ec['name']}</b><br>
                    <span style='color:#888;font-size:10px'>TYPE · CAPACITY</span><br>
                    <b>{ec['type']}</b> · <b style='color:#00ffc8'>{ec['capacity']:,} people</b>
                    </div>""",
                    max_width=220
                ),
                tooltip=f"🚨 {ec['name']} ({ec['capacity']:,})",
                icon=folium.Icon(color="green", icon="home", prefix="fa")
            ).add_to(evac_group)
        evac_group.add_to(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # Render map
    st_folium(m, width=None, height=580, returned_objects=[])

    # ── ZONE STATS BELOW MAP ──
    st.markdown("<br>", unsafe_allow_html=True)
    if show_flood_zones:
        zone_lat_range = (zone_data["center"][0] - 0.15, zone_data["center"][0] + 0.15)
        zone_lon_range = (zone_data["center"][1] - 0.15, zone_data["center"][1] + 0.15)
        visible_zones = [
            z for z in FLOOD_ZONES
            if zone_lat_range[0] <= z[0] <= zone_lat_range[1]
            and zone_lon_range[0] <= z[1] <= zone_lon_range[1]
        ]

        if visible_zones:
            high = sum(1 for z in visible_zones if z[3] == "HIGH")
            med  = sum(1 for z in visible_zones if z[3] == "MEDIUM")
            low  = sum(1 for z in visible_zones if z[3] == "LOW")

            c1, c2, c3, c4 = st.columns(4)
            for col, label, val, color in [
                (c1, "ZONES IN VIEW", len(visible_zones), "#00b4ff"),
                (c2, "HIGH RISK", high, "#ff3b3b"),
                (c3, "MEDIUM RISK", med, "#ffaa00"),
                (c4, "LOW RISK", low, "#00e87a"),
            ]:
                with col:
                    st.markdown(f"""
                    <div style="background:#0f1e35;border:1px solid rgba(0,180,255,0.1);
                    border-radius:10px;padding:14px;text-align:center">
                        <div style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:{color}">{val}</div>
                        <div style="font-size:0.55rem;letter-spacing:2px;color:#5a7a9a;margin-top:2px">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;font-size:0.65rem;color:#2a4a6a;letter-spacing:2px;padding:8px 0">
    FLOODSENSE AI · MAP MODULE · BUILT BY KANIKA 💙 · DATA: OPEN-METEO + MANUAL SURVEY
</div>
""", unsafe_allow_html=True)