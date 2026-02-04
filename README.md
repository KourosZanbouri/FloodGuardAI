> ⚠️ **LEGAL NOTICE: INTELLECTUAL PROPERTY & COPYRIGHT**
>
> **© 2026 Kouros Zanbouri. All Rights Reserved.**
>
> This software, "FloodGuard AI," and its associated documentation, concepts, and algorithms are the exclusive intellectual property of the author.
>
> **Access Condition:**
> This repository is made public solely for the purpose of evaluation by the judges of the **AI for Ireland Quest**.
>
> **Restrictions:**
> 1. **No Commercial Use:** You may not use this code, concept, or any derivative works for commercial purposes, startup formation, or funding proposals without explicit written permission.
> 2. **No Unauthorized Copying:** Redistribution or modification of this code is strictly prohibited.
> 3. **Prior Art:** This repository serves as a timestamped public disclosure of the "Agentic Flood Defense" concept, establishing Prior Art under Irish and EU Intellectual Property Law.
>
> For licensing inquiries or partnership proposals, please contact: k.zanbouri [AT] cs [DOT] ucc [DOT] ie

---


# 🛡️ FloodGuard AI: Ireland's First Agentic Flood Defense System

> **"From Passive Monitoring to Active Protection."**
> 


## 🚨 The Problem

Flooding is Ireland's most frequent and costly natural disaster. Current systems (like `floodinfo.ie`) are **passive**:

-   They display data but do not **act**.
    
-   They rely on human operators to see a warning and make a phone call.
    
-   By the time the human reacts, the water is often already in the house.
    

**The Gap:** There is no autonomous system that connects **Prediction** (Met Éireann) to **Action** (ESB Dams, Council Traffic Systems, Civil Defence).

## 💡 The Solution: FloodGuard AI

FloodGuard is an **Agentic AI** that autonomously manages flood defense. It doesn't just predict the water level; it **orchestrates the response** across infrastructure, emergency services, and the economy.

**Core Innovation:**

Instead of a dashboard that waits for you, FloodGuard is an **Autonomous Agent** that:

1.  **SENSES:** Fuses real-time data from Met Éireann (Rain), OPW (River Levels), and Tide Tables.
    
2.  **THINKS:** Uses a Machine Learning model to predict flood depth 24 hours in advance with high precision.
    
3.  **ACTS:** Triggers real-world protocols via API simulations (SCADA for dams, Twilio for SMS alerts, Blockchain for insurance).
    
----------
### **Technical Novelty: The Shift to Agentic AI**

**1. From Passive Dashboard to Closed-Loop Control** The primary innovation of FloodGuard is the architectural shift from a "Human-in-the-Loop" visualization tool to a **"Human-on-the-Loop" autonomous agent**.

-   **Current Standard:** Traditional systems (like FloodInfo.ie) are **Open-Loop**. They ingest data and display it, relying entirely on a human operator to notice the anomaly, interpret the risk, and manually initiate a response protocol.
    
-   **FloodGuard Novelty:** We implemented a **Closed-Loop Control System**. The Agent ingests data (Sense), evaluates risk against a dynamic state machine (Think), and autonomously triggers actuators (Act). This reduces the "Reaction Gap" from hours to milliseconds, creating a self-correcting defense system that operates even if human operators are incapacitated or overwhelmed.
    

**2. The "Digital Bridge" Architecture (Cross-Domain Interoperability)** FloodGuard creates a novel interoperability layer that bridges the gap between **Modern Cloud AI** and **Legacy Critical Infrastructure**.

-   We developed a unified control plane that translates high-level AI decisions (e.g., "Mitigate Risk in Zone A") into specific, low-level protocols for disparate systems that currently do not talk to each other:
    
    -   **Industrial:** Simulating SCADA handshake protocols for Dam Sluice Gates.
        
    -   **Analogue Emergency:** Synthesizing digital text alerts into **TETRA Radio Voice Audio** for injection into the National Digital Radio Service (NDRS).
        
    -   **Financial:** Triggering **Smart Contracts** on a blockchain ledger for Parametric Insurance payouts.
        

**3. Socially Aware Resource Optimization** Most flood models optimize for hydraulic flow or economic loss. FloodGuard introduces a **Human-Centric Optimization Layer**.

-   We integrated a combinatorial optimization algorithm (solving the **Knapsack Problem**) to manage scarce resources (e.g., sandbags, ambulances).
    
-   Unlike standard logistics engines, our "Guardian Agent" weights the objective function based on **Social Vulnerability Data** (HSE Registers for oxygen dependency, mobility impairment), ensuring that the AI prioritizes the preservation of human life over property value. This creates an "Ethical AI" framework for crisis management.
----------

## 🏗️ System Architecture

### 1. The Brain (Prediction Engine)

-   **Model:** Random Forest Regressor trained on 5 years of historical OPW & Met Éireann data.
    
-   **Inputs:** Rainfall Intensity (mm/hr), Current River Level (m), Tide Height (m).
    
-   **Outputs:** Predicted River Level (+6hr, +12hr, +24hr).
    

### 2. The Body (Agentic Actions)

The system is divided into three active response layers:

| Layer | Target System | Agent Action (Autonomous) |
| :--- | :--- | :--- |
| **L1: Infrastructure** | **ESB Inniscarra Dam** | *Pre-emptive Discharge:* Releases water 12hrs before a storm to create reservoir capacity. |
| | **Cork City Council** | *Traffic Control:* Overrides SCATS signals to RED on flooded roads (Lee Rd) and reroutes traffic. |
| **L2: Emergency** | **Civil Defence** | *Resource Optimization:* Solves the "Knapsack Problem" to allocate sandbags to critical zones (Hospital > Park). |
| | **Uisce Éireann** | *Water Security:* Detects turbidity and auto-drafts "Boil Water Notices" or deploys tankers. |
| **L3: Economy** | **SME Retail** | *Targeted Alerting:* Calls specific shop owners via Twilio API to deploy flood gates. |
| | **Insurance** | *Parametric Payout:* Triggers a "Force Majeure" blockchain event for instant cash relief. |

----------

## 💻 Tech Stack

-   **Frontend:** Streamlit (Python) - _chosen for rapid prototyping of data apps._
    
-   **Geospatial:** PyDeck & Mapbox - _for 3D visualization of flood risk zones._
    
-   **Data Processing:** Pandas & NumPy.
    
-   **Agent Logic:** Custom Python Class (`FloodAgent`) implementing a Rules-Based Expert System atop ML predictions.
    
-   **APIs (Simulated):** Twilio (SMS), ESB SCADA (Industrial Control), OpenMeteo (Weather).
    

----------

## 🚀 Installation & Setup

To run the prototype locally:

1.  **Clone the repository:**
    
    Bash
    
    ```
    git clone https://github.com/yourusername/floodguard-ai.git
    cd floodguard-ai
    
    ```
    
2.  **Install dependencies:**
    
    Bash
    
    ```
    pip install streamlit pandas numpy pydeck
    
    ```
    
3.  **Run the application:**
    
    Bash
    
    ```
    streamlit run floodguard_final.py
    
    ```
    
4.  **Explore the Demo:**
    
    -   Use the **Sidebar** to switch between "Sunny Day", "Storm Babet" (High Risk), and "100-Year Flood" (Critical).
        
    -   Watch the **Agent Action Log** generate distinct commands for each scenario.
        

----------

## 📸 Screenshots

### 1. The Dashboard (Normal vs. Critical)

_The interface shifts from Green (Monitoring) to Red (Command Center) instantly._

### 2. The Agentic Log

_Showing the AI autonomously commanding the Dam and alerting shop owners._

Plaintext

```
[14:30] 🤖 AGENT ACTION -> Inniscarra Dam: COMMAND SENT 'EMERGENCY_DUMP_100%'.
[14:30] 🤖 AGENT ACTION -> An Garda Síochána: Updated Digital Road Signs 'FLOOD AHEAD'.

```

### 3. Geospatial Risk Map

_Pinpointing exact impact zones like Oliver Plunkett St and Mercy Hospital._

----------

## 🌍 Impact & Scalability

-   **Scalability:** The model is location-agnostic. It can be deployed to the River Shannon (Limerick) or River Liffey (Dublin) by retraining on local OPW station data.
    
-   **Economic Value:** By triggering "Parametric Insurance" payouts instantly, we prevent small businesses from going bankrupt while waiting for claims.
    
-   **Social Good:** Automated "Vulnerable Person" evacuation priorities ensure the elderly are rescued first.
    

## 🏆 Why FloodGuard?

Current tools tell you **what is happening**. FloodGuard tells the infrastructure **what to do**. It is the difference between watching a disaster and managing it.



