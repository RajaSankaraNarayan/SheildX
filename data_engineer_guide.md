# Sentinel SDK - Data & Security Engineer Guide

Welcome to the Sentinel project! This guide will explain how the anomaly engine and threat intelligence backend are structured, how to run the simulations, and how you can inject your own data models and threat intel into the system.

## 1. Project Setup
To run the backend locally on your machine:
```powershell
# Create a virtual environment and activate it
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install fpdf2 Faker requests

# Start the server
python -m uvicorn main:app --port 8000
```
*Note: If you need to wipe the database clean, just delete the `sentinel.db` file and restart the server.*

## 2. Threat Intelligence Integration
You have two ways to inject your data (like Kaggle datasets, survey insights, or known scammer lists) into the Anomaly Engine:

### Option A: The Mock Lists (Static)
Open `threat_intel_mock.py`. Here you will find hardcoded Python lists containing:
- `BLACKLISTED_IPS`
- `SUSPICIOUS_ASNS`
- `KNOWN_PHISHING_DOMAINS`
- `KNOWN_MULE_ACCOUNTS` (UPI IDs)

You can manually paste your datasets into these lists. The `anomaly_engine.py` reads from this file on every transaction.

### Option B: The Live Threat DB (Dynamic)
We have a live SQLite `threat_intelligence` table that the engine checks in real-time. You can write your own Python/Jupyter scripts to push data directly to the live server using our Admin API.

**Endpoint:** `POST http://127.0.0.1:8000/api/v1/admin/threat`
**Payload:**
```json
{
  "threat_type": "UPI_ID", // Can be "UPI_ID", "KEYWORD", or "IP_ADDRESS"
  "value": "fake_cbi_agent@upi"
}
```

## 3. The Anomaly Engine (0-100 Scoring)
Open `anomaly_engine.py`. This is where your logic shines!
- The `evaluate_transaction()` function checks 40+ metadata fields (VPN usage, Device Trust Score, Velocity, MCC codes, etc.).
- It assigns point values (e.g., `+90` for Tor Network, `+60` for scam keywords).
- **Your Job:** You can tweak these weights based on your statistical analysis or ML models.
- If the score is > 60, it triggers an AI intervention and generates a PDF Incident Report in the `/reports` folder.

## 4. Running the Fraud Simulator
We built a synthetic data generator using `Faker` to demonstrate realistic fraud scenarios for the hackathon judges.

While the server is running in one terminal, open a second terminal and run:
```powershell
python fraud_simulator.py
```
This will automatically generate and fire 4 different payloads:
1. Normal Transaction
2. Social Engineering (Digital Arrest scam)
3. Impossible Travel (Tor network & foreign IP)
4. Account Takeover (Account drain with VPN)

You can open `fraud_simulator.py` to add even more scenarios (like Card Testing, BEC, or SIM Swaps) using the expansive 40-field payload structure.

---
**Happy Threat Hunting!** Let the Backend Lead know if you need any new fields added to the `models.py` payload to support your machine learning features.
