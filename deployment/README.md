#  FloodGuard AI: Deployment Candidate (v2.0)

> **Status:** Production Ready | **Data:** Real-Time OPW Feed | **Model:** 5-Year Historical Training

##  Key Improvements (from Hackathon Prototype)

This deployment build represents a **40% technical leap** from the initial prototype. We have moved from simulated environments to real-world infrastructure integration.

### 1.  From Hardcoded Logic to Real Machine Learning
- **Old:** Rules-based thresholds (If water > 2m, then alert).
- **New:** Random Forest Regressor trained on **1,825 days** of verified daily tidal data from **Mercy University Hospital (Station 19164)**.
- **Capability:** The model now detects "Rising Trends" and predicts tomorrow's peak risk based on 3-day autoregressive lag patterns.

### 2. From Static CSVs to Live API Connection
- **Old:** Static sliders for demonstration.
- **New:** Live connection to the **OPW WaterLevel.ie API**. The system now fetches the exact water level in Cork City in real-time (15-min latency).

### 3. Critical Infrastructure Focus
- We shifted focus from generic river points to **Mercy Hospital**, ensuring our AI protects the most vulnerable medical infrastructure in the city.

---

##  How to Run This Build

1. **Train the AI Model:**
   (This generates the `flood_model_5y.pkl` brain file)
   ```bash
   python train_5year_model.py

2.   **Launch the Live Command Center:**
    
    Bash
    
    ```
    streamlit run floodguard_live.py
    
    ```
    
3.   **Verify Live Data:**
    
    -   In the sidebar, click **"🔌 Connect to Live Sensor"**.
        
    -   Watch the dashboard update with the actual real-time water level from Cork City.