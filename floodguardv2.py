import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FloodGuard AI - Final Prototype",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #003366; font-family: 'Helvetica Neue', sans-serif; }
    .stAlert { border-left: 5px solid #003366; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    .agent-log { font-family: 'Courier New', monospace; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- AGENTIC CORE ---
class FloodAgentFinal:
    def __init__(self):
        self.thresholds = {"Alert": 2.2, "Flood": 2.8, "Critical": 3.4}
    
    def predict(self, current, rain, tide):
        prediction = current + (rain * 0.05) + (tide * 0.15)
        return round(prediction, 2)

    def generate_response_log(self, status):
        """
        Generates logs that explicitly show the AI COMMANDING other systems.
        """
        logs = {
            "infra": [], 
            "emergency": [], 
            "sectors": []
        }
        
        t = datetime.now().strftime("%H:%M")

        if status == "Normal":
            logs["infra"].append(f"[{t}] 🟢 SYSTEM CHECK -> Inniscarra Dam SCADA: Connection Active.")
            logs["infra"].append(f"[{t}] 🟢 SYSTEM CHECK -> Uisce Éireann Sensors: Quality Optimal.")
            logs["sectors"].append(f"[{t}] 🟢 MONITORING -> Business Zone: No threats detected.")
            logs["sectors"].append(f"[{t}] 🟢 MONITORING -> Community Alerts: Standby Mode.")
            logs["emergency"].append(f"[{t}] 🟢 MONITORING -> HSE Vulnerable Register: 142 Registered in Zone A")

        elif status == "High Risk": # STORM BABET SCENARIO
            # INFRASTRUCTURE (The AI takes control)
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Inniscarra Dam: COMMAND SENT 'Open_Discharge_20%'.")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Cork City Council: Auto-deployed 'AquaDam' barriers (Morrison's Island).")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> SCATS Traffic Control: Overrode signals to RED at Lee Road.")
            

            
            # EMERGENCY
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> Civil Defence HQ: Dispatched SMS Mobilization Order (Unit 4).")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> An Garda Síochána: Updated Digital Road Signs 'FLOOD AHEAD - DIVERT'.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> Public Health Nurse: Automated call list generated for check-ins.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> HSE Database Query: Identified 12 'Category A' (Mobility Impaired) in Flood Zone.")

            
            # SECTORS (Specific Shop Owner Calls)
            logs["sectors"].append(f"[{t}] 🤖 AGENT ACTION -> Twilio API: Voice Call initiated to Shop Owners (Zone A).")
            logs["sectors"].append(f"[{t}] 📞 CALL TRANSCRIPT: 'FloodGuard Alert. Water breaching in 45 mins. Deploy gates now.'")

        elif status == "Critical": # 100-YEAR FLOOD SCENARIO
            # INFRASTRUCTURE
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Inniscarra Dam: COMMAND SENT 'EMERGENCY_DUMP_100%'.")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> ESB Networks: REMOTE DISCONNECT executed for Substation G21.")
            logs["infra"].append(f"[{t}] 🤖 AGENT ACTION -> Uisce Éireann: 'DO NOT CONSUME' Protocol auto-published to website.")
            
            # EMERGENCY
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> DEFENCE FORCES: Secure Link established. Requesting 6x6 Troop Carriers.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> Fire Brigade Control: Re-routed High Volume Pumps to City Hall.")
            logs["emergency"].append(f"[{t}] 🤖 AGENT ACTION -> HSE Operations: Triage Tent location identified at UCC (Higher Ground).")
            logs["emergency"].append(f"[{t}] 📍 TARGET: Eircode T12 XY44 (Patient: Oxygen Dependent / 3rd Floor).")
            logs["emergency"].append(f"[{t}] 📍 TARGET: Eircode T12 AB99 (Patient: High-Risk Pregnancy).")
            
            # SECTORS
            logs["sectors"].append(f"[{t}] 🤖 AGENT ACTION -> Blockchain Ledger: 'Force Majeure' event recorded for Instant Payout.")
            logs["sectors"].append(f"[{t}] 🤖 AGENT ACTION -> Iarnród Éireann: Signal 402 set to STOP (Glounthaune Line).")

        return logs

# --- SIDEBAR ---
# Using official Wikimedia URL
st.sidebar.image("./assets/County_Cork_arms.png", width=80)
st.sidebar.header("🕹️ Scenario Control")

mode = st.sidebar.radio("Mode:", ["Presentation (Preset)", "Judge Sandbox (Manual)"])

if mode == "Presentation (Preset)":
    scenario = st.sidebar.selectbox(
        "Select Event:",
        ("Sunny Day (Normal)", "Storm Babet (High Risk)", "The 100-Year Flood (Critical)")
    )
    if scenario == "Sunny Day (Normal)":
        # Result: ~1.35m (Safe)
        rain_input, river_input, tide_input = 0.0, 1.2, 1.0
        
    elif scenario == "Storm Babet (High Risk)":
        # CHANGED VALUES HERE
        # Calculation: 2.0 + (18 * 0.05) + (2.0 * 0.15) = 3.2m
        # 3.2m is > 2.8 (Flood) but < 3.4 (Critical) -> Correctly "High Risk"
        rain_input, river_input, tide_input = 18.0, 2.0, 2.0
        
    else:
        # Result: > 6.0m (Critical)
        rain_input, river_input, tide_input = 60.0, 2.9, 4.5
else:
    st.sidebar.warning("⚠️ Manual Override")
    rain_input = st.sidebar.slider("Rainfall (mm/hr)", 0.0, 100.0, 10.0)
    river_input = st.sidebar.slider("Current River Level (m)", 1.0, 4.0, 1.8)
    tide_input = st.sidebar.slider("Tide Surge (m)", 0.0, 5.0, 1.0)

# Initialize Agent
agent = FloodAgentFinal()
prediction = agent.predict(river_input, rain_input, tide_input)

# Determine Risk Status
if prediction > agent.thresholds["Critical"]:
    status = "Critical"
    alert_color = "error"
elif prediction > agent.thresholds["Flood"]:
    status = "High Risk"
    alert_color = "warning"
else:
    status = "Normal"
    alert_color = "success"

# --- MAIN DASHBOARD ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ FloodGuard AI")
    st.markdown("**National Agentic Flood Defense System | Cork City Pilot**")
with col2:
    st.metric("System Status", status.upper())

# KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Predicted Level", f"{prediction}m", f"{(prediction-river_input):.2f}m rise")
k2.metric("Rainfall Intensity", f"{rain_input} mm/h")
k3.metric("Tide Surge", f"{tide_input}m")
#k4.metric("Active Agents", "4" if status == "Normal" else "32", delta="Online")
k4.metric(
    "Active Agents",
    "4" if status == "Normal" else "16" if status == "High Risk" else "32",
    delta="Online"
)


st.divider()

# --- THE AGENTIC ACTS ---
st.subheader(f"🤖 Agentic Action Log: {status} Protocol")
st.caption("Real-time feed of autonomous decisions executed by the AI.")

logs = agent.generate_response_log(status)

tab1, tab2, tab3 = st.tabs([
    "🏗️ Infrastructure (Hard Control)", 
    "🚑 Emergency Services (Blue Light)", 
    "🏭 Economy & Community"
])

with tab1: 
    st.markdown("**Target Systems:** Inniscarra Dam, SCATS Traffic, Uisce Éireann Plants")
    for log in logs["infra"]:
        if status == "Normal": st.info(log)
        elif status == "High Risk": st.warning(log)
        else: st.error(log)

with tab2:
    st.markdown("**Target Agencies:** Gardaí, Fire Brigade, Defence Forces")
    for log in logs["emergency"]:
        if status == "Normal": st.info(log)
        elif status == "High Risk": st.warning(log)
        else: st.error(log)
    
    if status == "High Risk":
        st.progress(60, text="Civil Defence Mobilization: 60%")
    elif status == "Critical":
        st.progress(100, text="Defence Forces Full Mobilization: 100%")

with tab3:
    st.markdown("**Target Sectors:** Retail Owners, Insurance API, Transport")
    for log in logs["sectors"]:
        st.info(log)

st.divider()

# --- GEOSPATIAL INTELLIGENCE ---
st.subheader("📍 Live Risk Map (Cork City)")

# Dynamic Risk Map Data
map_data = pd.DataFrame({
    'lat': [51.8972, 51.8963, 51.8984, 51.8950], 
    'lon': [-8.4697, -8.4716, -8.4839, -8.4900],
    'name': ["Oliver Plunkett St", "Morrison's Island", "Mercy Hospital", "Waterworks (Lee Rd)"],
    'risk': [prediction * 30, prediction * 40, prediction * 10, prediction * 50]
})

if status == "Normal": color = [0, 255, 0, 140]
elif status == "High Risk": color = [255, 165, 0, 160]
else: color = [255, 0, 0, 200]

layer = pdk.Layer(
    "ScatterplotLayer",
    map_data,
    get_position='[lon, lat]',
    get_color=color,
    get_radius='risk',
    pickable=True,
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(latitude=51.8970, longitude=-8.4750, zoom=13.5),
    tooltip={"text": "{name}\nRisk Index: {risk}"}
))