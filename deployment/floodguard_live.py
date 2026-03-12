"""
FloodGuard AI — Production Deployment v2.0
Cork City Pilot | Agentic Flood Defense System

Structure mirrors floodguardv2.py exactly.
Additions:
  - Real ML model (flood_model_5y.pkl)
  - Live OPW + Open-Meteo data with cross-verification panel
  - All 4 station coordinates verified from OPW hydro-data (March 2026)
  - Audit trail
"""

import os
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import joblib
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG  — mirrors floodguardv2.py
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FloodGuard AI - Final Prototype",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# STYLING  — mirrors floodguardv2.py exactly
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #003366; font-family: 'Helvetica Neue', sans-serif; }
    .stAlert { border-left: 5px solid #003366; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    .agent-log { font-family: 'Courier New', monospace; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "flood_model_5y.pkl")
AUDIT_LOG    = os.path.join(os.path.dirname(__file__), "deployment_audit_log.csv")
FEATURE_COLS = ['lag_1h','lag_3h','lag_6h','lag_12h','lag_24h','lag_48h',
                'rise_1h','rise_3h','rise_6h','roll_mean_6h','roll_mean_24h',
                'roll_std_6h','roll_max_24h','temp','hour_sin','hour_cos','month_sin','month_cos']

# Verified station metadata — used for the map and info table
STATION_META = pd.DataFrame([
    {"id": "19102", "name": "Waterworks Weir",    "lat": 51.893989, "lon": -8.510053,
     "type": "Level & Flow", "waterbody": "Lee",        "catchment_km2": 1185.0,
     "gauge_datum": "2.000 m Malin Head"},
    {"id": "19162", "name": "Fitzgerald's Park",  "lat": 51.896472, "lon": -8.498278,
     "type": "Level",        "waterbody": "Lee",        "catchment_km2": 1185.0,
     "gauge_datum": "0.151 m Malin Head"},
    {"id": "19164", "name": "Mercy Hospital",     "lat": 51.900050, "lon": -8.483830,
     "type": "Tidal",        "waterbody": "Lee",        "catchment_km2": 0.0,
     "gauge_datum": "-2.954 m Malin Head"},
    {"id": "19113", "name": "County Hall",         "lat": 51.892643, "lon": -8.509638,
     "type": "Level",        "waterbody": "Curragheen", "catchment_km2": 47.62,
     "gauge_datum": "0.886 m Malin Head"},
])

# ─────────────────────────────────────────────
# AGENTIC CORE  — mirrors FloodAgentFinal
# ─────────────────────────────────────────────
class FloodAgentDeployment:
    def __init__(self):
        self.thresholds  = {"Alert": 2.2, "Flood": 2.8, "Critical": 3.4}
        self._estimator  = None
        self.model_meta  = {}
        self.is_real_ml  = False
        if os.path.exists(MODEL_PATH):
            payload = joblib.load(MODEL_PATH)
            # Support both new dict payload and legacy raw estimator
            if isinstance(payload, dict):
                self._estimator = payload['model']
                self.model_meta = {k: v for k, v in payload.items() if k != 'model'}
            else:
                self._estimator = payload
            self.is_real_ml = True

    def predict(self, current_level: float, rain: float = 0.0,
                tide: float = 1.0, water_temp: float = None,
                rise_rate_1h: float = 0.0) -> float:
        if self.is_real_ml:
            now      = datetime.now(__import__("datetime").timezone.utc)
            h, m     = now.hour, now.month
            l1       = current_level
            l3       = current_level - rise_rate_1h * 3
            l6       = current_level - rise_rate_1h * 6
            l12      = current_level - rise_rate_1h * 12
            l24      = current_level - rise_rate_1h * 24
            l48      = current_level - rise_rate_1h * 48
            rise_1h  = rise_rate_1h
            rise_3h  = rise_rate_1h * 3
            rise_6h  = rise_rate_1h * 6
            mean_6h  = current_level - rise_rate_1h * 3
            mean_24h = current_level - rise_rate_1h * 12
            std_6h   = abs(rise_rate_1h) * 2 + 0.01
            max_24h  = max(current_level, current_level - rise_rate_1h * 24)
            temp_val = water_temp if water_temp is not None else 11.0

            # Build value dict — use actual feature list from saved model
            val_map = {
                'lag_1h': l1, 'lag_3h': l3, 'lag_6h': l6,
                'lag_12h': l12, 'lag_24h': l24, 'lag_48h': l48,
                'rise_1h': rise_1h, 'rise_3h': rise_3h, 'rise_6h': rise_6h,
                'roll_mean_6h': mean_6h, 'roll_mean_24h': mean_24h,
                'roll_std_6h': std_6h, 'roll_max_24h': max_24h,
                'temp': temp_val,
                'hour_sin': np.sin(2*np.pi*h/24), 'hour_cos': np.cos(2*np.pi*h/24),
                'month_sin': np.sin(2*np.pi*m/12), 'month_cos': np.cos(2*np.pi*m/12),
                'precip_mm': rain,   # included when model was trained with rainfall
            }
            # Use exactly the features the model was trained on
            model_features = self.model_meta.get('features', FEATURE_COLS)
            X = pd.DataFrame([[val_map[f] for f in model_features]], columns=model_features)
            return round(float(self._estimator.predict(X)[0]), 2)
        # Formula fallback
        return round(current_level + (rain * 0.05) + (tide * 0.15), 2)

    def audit(self, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(AUDIT_LOG, "a") as f:
            f.write(f"{ts},{message}\n")

    def generate_response_log(self, status: str) -> dict:
        logs = {"infra": [], "emergency": [], "sectors": []}
        t    = datetime.now().strftime("%H:%M")

        if status == "Normal":
            logs["infra"].append(f"[{t}] 🟢 SYSTEM CHECK -> Inniscarra Dam SCADA: Connection Active.")
            logs["infra"].append(f"[{t}] 🟢 SYSTEM CHECK -> Uisce Éireann Sensors: Quality Optimal.")
            logs["sectors"].append(f"[{t}] 🟢 MONITORING -> Business Zone: No threats detected.")
            logs["sectors"].append(f"[{t}] 🟢 MONITORING -> Community Alerts: Standby Mode.")
            logs["emergency"].append(f"[{t}] 🟢 MONITORING -> HSE Vulnerable Register: 142 Registered in Zone A")

        elif status == "High Risk":
            msg = "COMMAND SENT 'Open_Discharge_20%'"
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Inniscarra Dam: {msg}.")
            self.audit(f"INFRA: {msg}")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Cork City Council: Auto-deployed 'AquaDam' barriers (Morrison's Island).")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> SCATS Traffic Control: Overrode signals to RED at Lee Road.")
            msg2 = "Dispatched SMS Mobilization Order (Unit 4)"
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> Civil Defence HQ: {msg2}.")
            self.audit(f"EMERGENCY: {msg2}")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> An Garda Síochána: Updated Digital Road Signs 'FLOOD AHEAD - DIVERT'.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> Public Health Nurse: Automated call list generated for check-ins.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> HSE Database Query: Identified 12 'Category A' (Mobility Impaired) in Flood Zone.")
            logs["sectors"].append(f"[{t}] 🤖 AGENT ACTION -> Twilio API: Voice Call initiated to Shop Owners (Zone A).")
            logs["sectors"].append(f"[{t}] 📞 CALL TRANSCRIPT: 'FloodGuard Alert. Water breaching in 45 mins. Deploy gates now.'")

        elif status == "Critical":
            msg = "COMMAND SENT 'EMERGENCY_DUMP_100%'"
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Inniscarra Dam: {msg}.")
            self.audit(f"CRITICAL_INFRA: {msg}")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> ESB Networks: REMOTE DISCONNECT executed for Substation G21.")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Uisce Éireann: 'DO NOT CONSUME' Protocol auto-published to website.")
            msg2 = "Secure Link established. Requesting 6x6 Troop Carriers"
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> DEFENCE FORCES: {msg2}.")
            self.audit(f"CRITICAL_EMERGENCY: {msg2}")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> Fire Brigade Control: Re-routed High Volume Pumps to City Hall.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> HSE Operations: Triage Tent location identified at UCC (Higher Ground).")
            logs["emergency"].append(f"[{t}] 📍 TARGET: Eircode T12 XY44 (Patient: Oxygen Dependent / 3rd Floor).")
            logs["emergency"].append(f"[{t}] 📍 TARGET: Eircode T12 AB99 (Patient: High-Risk Pregnancy).")
            logs["sectors"].append(f"[{t}] 🤖 AGENT ACTION -> Blockchain Ledger: 'Force Majeure' event recorded for Instant Payout.")
            logs["sectors"].append(f"[{t}] 🤖 AGENT ACTION -> Iarnród Éireann: Signal 402 set to STOP (Glounthaune Line).")

        return logs


# ─────────────────────────────────────────────
# SIDEBAR  — mirrors floodguardv2.py structure
# ─────────────────────────────────────────────
st.sidebar.image(
    "County_Cork_arms.png",
    width=80,
)
st.sidebar.header("🕹️ Scenario Control")

mode = st.sidebar.radio("Mode:", ["Presentation (Preset)", "Judge Sandbox (Manual)", "🔴 Live Deployment"])

rain_input  = 0.0
river_input = 1.2
tide_input  = 1.0
live_data   = None

if mode == "Presentation (Preset)":
    scenario = st.sidebar.selectbox(
        "Select Event:",
        ("Sunny Day (Normal)", "Storm Babet (High Risk)", "The 100-Year Flood (Critical)")
    )
    if scenario == "Sunny Day (Normal)":
        rain_input, river_input, tide_input = 0.0, 1.2, 1.0
    elif scenario == "Storm Babet (High Risk)":
        rain_input, river_input, tide_input = 18.0, 2.0, 2.0
    else:
        rain_input, river_input, tide_input = 60.0, 2.9, 4.5

elif mode == "Judge Sandbox (Manual)":
    st.sidebar.warning("⚠️ Manual Override")
    rain_input  = st.sidebar.slider("Rainfall (mm/hr)",        0.0, 100.0, 10.0)
    river_input = st.sidebar.slider("Current River Level (m)", 1.0, 4.0,   1.8)
    tide_input  = st.sidebar.slider("Tide Surge (m)",          0.0, 5.0,   1.0)

else:  # Live Deployment
    st.sidebar.info("Fetches live OPW water levels + Open-Meteo weather.")
    if st.sidebar.button("🔌 Fetch Live Data"):
        with st.spinner("Connecting to Cork City sensors..."):
            try:
                from fetch_real_data import get_full_verification_data
                live_data   = get_full_verification_data()
                river_input = live_data["primary_level"]
                if live_data["weather"]:
                    rain_input = live_data["weather"].get("precip_mm_hr", 0.0) or 0.0
                st.session_state["live_data"] = live_data
            except ImportError:
                st.sidebar.error("fetch_real_data.py not found.")

    if "live_data" in st.session_state:
        live_data   = st.session_state["live_data"]
        river_input = live_data["primary_level"]
        if live_data["weather"]:
            rain_input = live_data["weather"].get("precip_mm_hr", 0.0) or 0.0
        st.sidebar.success(f"📡 {river_input:.3f}m @ {live_data['primary_name']}")
        st.sidebar.caption(f"Fetched: {live_data['fetched_at']}")

    st.sidebar.caption("Simulate storm surge on top of live baseline:")
    surge       = st.sidebar.slider("Storm Surge (+m)", 0.0, 4.0, 0.0, 0.05)
    river_input = round(river_input + surge, 3)

# ─────────────────────────────────────────────
# INFERENCE
# ─────────────────────────────────────────────
agent = FloodAgentDeployment()

# Pass water temp + rise rate from live data when available
_water_temp   = None
_rise_rate_1h = 0.0
if live_data:
    for s in live_data.get("stations", []):
        if s.get("name") == live_data.get("primary_name"):
            _water_temp = s.get("water_temp_c")
            break

prediction = agent.predict(river_input, rain_input, tide_input,
                           water_temp=_water_temp, rise_rate_1h=_rise_rate_1h)

if prediction > agent.thresholds["Critical"]:
    status = "Critical"
elif prediction > agent.thresholds["Flood"]:
    status = "High Risk"
else:
    status = "Normal"

# ─────────────────────────────────────────────
# HEADER  — mirrors floodguardv2.py
# ─────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ FloodGuard AI")
    st.markdown("**National Agentic Flood Defense System | Cork City Pilot**")
with col2:
    st.metric("System Status", status.upper())
    if mode == "🔴 Live Deployment":
        if agent.is_real_ml:
            st.markdown("🧠 **ML Model** :green[✅ Active]")
        else:
            st.markdown("⚠️ **ML Model** :red[Fallback — run train_5year_model.py]")
    elif mode == "Presentation (Preset)":
        st.markdown("🎭 **Mode** :blue[Preset Scenario]")
    else:
        st.markdown("🕹️ **Mode** :orange[Manual Sandbox]")

# KPI Row — mirrors floodguardv2.py exactly
k1, k2, k3, k4 = st.columns(4)
k1.metric("Predicted Level",    f"{prediction}m",      f"{(prediction - river_input):.2f}m rise")
k2.metric("Rainfall Intensity", f"{rain_input} mm/h")
k3.metric("Tide Surge",         f"{tide_input}m")
k4.metric(
    "Active Agents",
    "4" if status == "Normal" else "16" if status == "High Risk" else "32",
    delta="Online",
)

st.divider()

# ─────────────────────────────────────────────
# DATA VERIFICATION PANEL
# ─────────────────────────────────────────────
with st.expander(
    "🔬 Live Data Verification — OPW Sensors × Open-Meteo Cross-Check",
    expanded=(mode == "🔴 Live Deployment" and live_data is not None),
):
    if live_data is None:
        if mode == "🔴 Live Deployment":
            st.warning("Click **'🔌 Fetch Live Data'** in the sidebar to load real sensor readings.")
        else:
            st.info(
                "In **Presentation** and **Sandbox** modes the inputs are simulated. "
                "Switch to **🔴 Live Deployment** and click 'Fetch Live Data' to see real-time cross-verification."
            )
    else:
        st.caption(f"Last fetched: **{live_data['fetched_at']}**")

        # ── Source 1: OPW Stations Table ───────────────────────────────────
        st.markdown("### 💧 Source 1 — OPW WaterLevel.ie")
        st.caption(
            "All four Cork City stations polled in real-time. "
            "Station IDs and coordinates verified from waterlevel.ie/hydro-data."
        )

        # Build display table from live results
        station_rows = []
        for s in live_data["stations"]:
            station_rows.append({
                "Station":      s["name"],
                "ID":           s["station_id"],
                "Type":         s["type"],
                "Waterbody":    s["waterbody"],
                "Level (m)":    f"{s['level_m']:.3f}" if s["level_m"] is not None else "—",
                "Flow (m³/s)":  f"{s['flow_m3s']:.2f}" if s.get("flow_m3s") else "—",
                "Water Temp":   f"{s['water_temp_c']}°C" if s.get("water_temp_c") else "—",
                "Timestamp":    s["timestamp"],
                "Gauge Datum":  s["gauge_datum"],
                "Catchment":    f"{s['catchment_km2']} km²",
                "API Status":   s["api_status"],
            })

        st.dataframe(
            pd.DataFrame(station_rows),
            width="stretch",
            hide_index=True,
        )

        # KPI highlights from primary station
        primary_row = next((s for s in live_data["stations"] if s["level_m"] is not None), None)
        if primary_row:
            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("Primary Level",      f"{primary_row['level_m']:.3f}m",
                       help="Waterworks Weir (19102) — main flood indicator")
            pc2.metric("Flow Rate",
                       f"{primary_row['flow_m3s']:.2f} m³/s" if primary_row.get("flow_m3s") else "N/A",
                       help="Only Waterworks Weir measures flow")
            pc3.metric("Water Temp",
                       f"{primary_row['water_temp_c']}°C" if primary_row.get("water_temp_c") else "N/A")
            pc4.metric("Last Reading", primary_row["timestamp"])

        st.divider()

        # ── Source 2: Open-Meteo Weather ──────────────────────────────────
        st.markdown("### 🌧️ Source 2 — Open-Meteo Weather (Cork City)")
        weather = live_data.get("weather")
        if weather:
            wc1, wc2, wc3, wc4 = st.columns(4)
            wc1.metric("Current Rain",    f"{weather['rain_mm_hr']} mm/hr",
                       help="Matches 'rain' field — liquid precipitation only")
            wc2.metric("Air Temperature", f"{weather['temp_air_c']}°C")
            wc3.metric("Wind Speed",      f"{weather['wind_kmh']} km/h")
            wc4.metric("Humidity",        f"{weather['humidity_pct']}%")
            st.caption(f"Source: {weather['source']} | Reading time: {weather['timestamp']}")

            # Hourly rain forecast bar chart
            if weather["hourly_precip"]:
                precip_df = pd.DataFrame(
                    weather["hourly_precip"],
                    columns=["Hour", "Precipitation (mm)"]
                )
                precip_df["Hour"] = precip_df["Hour"].astype(str).str[11:16]
                st.markdown("**Today's Hourly Precipitation Forecast:**")
                st.bar_chart(precip_df.set_index("Hour"), height=160)
        else:
            st.warning("Open-Meteo feed unavailable — check network connection.")

        st.divider()

        # ── Cross-Verification Result ─────────────────────────────────────
        st.markdown("### ✅ Cross-Verification Result")
        for note in live_data["cross_check"]["notes"]:
            if "✅" in note:
                st.success(note)
            elif "⚠️" in note:
                st.error(note)
            else:
                st.info(note)

# ─────────────────────────────────────────────
# AGENTIC ACTION LOG  — mirrors floodguardv2.py
# ─────────────────────────────────────────────
st.subheader(f"🤖 Agentic Action Log: {status} Protocol")
st.caption("Real-time feed of autonomous decisions executed by the AI.")

logs = agent.generate_response_log(status)

tab1, tab2, tab3 = st.tabs([
    "🏗️ Infrastructure (Hard Control)",
    "🚑 Emergency Services (Blue Light)",
    "🏭 Economy & Community",
])

with tab1:
    st.markdown("**Target Systems:** Inniscarra Dam, SCATS Traffic, Uisce Éireann Plants")
    for log in logs["infra"]:
        if status == "Normal":      st.info(log)
        elif status == "High Risk": st.warning(log)
        else:                       st.error(log)

with tab2:
    st.markdown("**Target Agencies:** Gardaí, Fire Brigade, Defence Forces")
    for log in logs["emergency"]:
        if status == "Normal":      st.info(log)
        elif status == "High Risk": st.warning(log)
        else:                       st.error(log)
    if status == "High Risk":
        st.progress(60, text="Civil Defence Mobilization: 60%")
    elif status == "Critical":
        st.progress(100, text="Defence Forces Full Mobilization: 100%")

with tab3:
    st.markdown("**Target Sectors:** Retail Owners, Insurance API, Transport")
    for log in logs["sectors"]:
        st.info(log)

st.divider()

# ─────────────────────────────────────────────
# GEOSPATIAL MAP
# Uses verified OPW coordinates — NOT the old
# placeholder coordinates from floodguardv2.py
# ─────────────────────────────────────────────
st.subheader("📍 Live Risk Map (Cork City)")

# Merge live levels into station metadata if available
map_df = STATION_META.copy()
if live_data:
    level_lookup = {s["station_id"]: s["level_m"] for s in live_data["stations"] if s["level_m"]}
    map_df["live_level"] = map_df["id"].map(level_lookup).fillna(river_input)
else:
    map_df["live_level"] = river_input

map_df["risk_radius"] = map_df["live_level"] * 35

if status == "Normal":      color = [0, 200, 80, 150]
elif status == "High Risk": color = [255, 165, 0, 170]
else:                       color = [220, 30, 0, 200]

layer = pdk.Layer(
    "ScatterplotLayer",
    map_df,
    get_position='[lon, lat]',
    get_color=color,
    get_radius='risk_radius',
    pickable=True,
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(latitude=51.896, longitude=-8.500, zoom=14.0),
    tooltip={"text": "{name}\nType: {type}\nWaterbody: {waterbody}"},
))

# ─────────────────────────────────────────────
# AUDIT LOG VIEWER
# ─────────────────────────────────────────────
if os.path.exists(AUDIT_LOG):
    with st.expander("🔒 Deployment Audit Trail", expanded=False):
        try:
            audit_df = pd.read_csv(AUDIT_LOG, names=["Timestamp", "Action"], on_bad_lines="skip")
            st.dataframe(audit_df.tail(20), use_container_width=True, hide_index=True)
        except Exception:
            st.warning("Audit log exists but could not be parsed.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.caption(
    "Powered by: OPW WaterLevel.ie · Open-Meteo · Scikit-Learn  |  "
    "© 2026 Kouros Zanbouri — All Rights Reserved"
)
