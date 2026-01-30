import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import time
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FloodGuard AI - Agentic Flood Defense",
    page_icon="🌊",
    layout="wide"
)

# --- MOCK DATA & AI AGENT CLASS ---
class FloodAgent:
    """
    The Agentic AI Core. 
    It doesn't just read data; it predicts, assesses risk, and formulates actions.
    """
    def __init__(self):
        # Define thresholds for decision making
        self.risk_thresholds = {"Low": 2.0, "Medium": 2.5, "High": 3.0}
    
    def predict_level(self, current_level, rainfall_forecast):
        # Simulation of your ML Model logic
        # In reality, this is where you load your trained .pkl model
        predicted_rise = rainfall_forecast * 0.15 
        future_level = current_level + predicted_rise
        return round(future_level, 2)

    def decide_action(self, predicted_level):
        """The 'Agentic' Logic: Translating numbers into Decisions."""
        if predicted_level > self.risk_thresholds["High"]:
            return {
                "status": "CRITICAL",
                "color": "red",
                "message": f"PREDICTION ({predicted_level}m) EXCEEDS CRITICAL LIMIT.",
                "action": "Trigger Civil Defence Alert + Deploy Sandbags at Zone A",
                "requires_approval": True
            }
        elif predicted_level > self.risk_thresholds["Medium"]:
            return {
                "status": "WARNING",
                "color": "orange",
                "message": f"Rising levels detected ({predicted_level}m).",
                "action": "Notify City Council + Close Lower Roads",
                "requires_approval": True
            }
        else:
            return {
                "status": "NORMAL",
                "color": "green",
                "message": "Levels stable.",
                "action": "Continue Monitoring",
                "requires_approval": False
            }

# --- SIDEBAR: SIMULATION CONTROLS ---
st.sidebar.header("🛠️ Simulation Control Panel")
st.sidebar.info("Use this panel to simulate a storm event for the judges.")

# Simulating Live Sensors
rain_intensity = st.sidebar.slider("Incoming Rainfall Intensity (mm/hr)", 0, 50, 5)
base_water_level = st.sidebar.slider("Current River Lee Level (m)", 1.0, 3.5, 1.8)

# Initialize Agent (CORRECTED LINE)
agent = FloodAgent()

# --- MAIN INTERFACE ---

# HEADER
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🌊 FloodGuard AI")
    st.markdown("**Autonomous Flood Defense System for Ireland**")
with col2:
    # Live Clock
    st.metric(label="System Time", value=datetime.now().strftime("%H:%M:%S"))

st.markdown("---")

# 1. THE AGENTIC LOOP
st.subheader("🤖 The Agentic Workflow")
st.markdown("Unlike traditional dashboards (Passive), FloodGuard (Active) constantly evaluates risk and proposes actions.")

# Run the Agent Logic
prediction = agent.predict_level(base_water_level, rain_intensity)
decision = agent.decide_action(prediction)

# Create 3 columns for the "Thinking Process"
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown("#### 1. SENSE")
    st.markdown(f"**Rainfall:** `{rain_intensity} mm/hr`")
    st.markdown(f"**River Level:** `{base_water_level} m`")
    st.caption("Real-time sensor fusion")

with kpi2:
    st.markdown("#### 2. THINK (ML Prediction)")
    delta = round(prediction - base_water_level, 2)
    st.metric(label="Predicted Level (+24hrs)", value=f"{prediction}m", delta=f"{delta}m rise")
    if decision["status"] == "CRITICAL":
        st.error("⚠️ FLOOD IMMINENT")
    elif decision["status"] == "WARNING":
        st.warning("⚠️ RISK DETECTED")
    else:
        st.success("✅ SAFE")

with kpi3:
    st.markdown("#### 3. ACT (Autonomous Decision)")
    st.markdown(f"**Status:** :{decision['color']}[{decision['status']}]")
    st.info(f"**Proposed Action:**\n\n{decision['action']}")
    
    # Human-in-the-loop Button
    if decision["requires_approval"]:
        if st.button(f"🚨 APPROVE ACTION: {decision['status']}"):
            st.toast(f"Protocol Initiated: {decision['action']}", icon="✅")
            st.balloons()
    else:
        st.button("System Idle", disabled=True)

st.markdown("---")

# 2. COMPARISON & DATA VISUALIZATION
tab_passive, tab_active = st.tabs(["📉 Standard View (Competitors)", "🗺️ Geospatial Intelligence"])

with tab_passive:
    st.write("Current systems (`floodinfo.ie`) only show this:")
    # Generate mock historical data
    chart_data = pd.DataFrame(
        np.random.randn(20, 2) + [rain_intensity, base_water_level],
        columns=['Rainfall', 'Water Level']
    )
    st.line_chart(chart_data)

with tab_active:
    st.write("FloodGuard identifies specific impact zones:")
    
    # Mock Coordinates for Cork City Sensors
    map_data = pd.DataFrame({
        'lat': [51.8985, 51.8950, 51.9000],
        'lon': [-8.4756, -8.4800, -8.4700],
        'risk_level': [prediction * 10, prediction * 50, prediction * 20] # Size based on risk
    })

    # PyDeck Map Layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        map_data,
        get_position='[lon, lat]',
        get_color='[200, 30, 0, 160]',
        get_radius='risk_level',
    )
    
    view_state = pdk.ViewState(latitude=51.8985, longitude=-8.4756, zoom=13)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# --- FOOTER ---
st.caption("Powered by: Met Éireann API • OPW Hydro Data • Scikit-Learn")