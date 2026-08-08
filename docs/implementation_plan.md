# Enterprise-Grade Fraud Testing Platform Plan

The requirements sent by your 4th team member are fantastic! They outline a highly realistic, enterprise-grade fraud simulation platform. This is a massive upgrade from our current heuristic engine and will make your hackathon project stand out as extremely professional.

This will require a significant architectural expansion. Here is the step-by-step plan to implement their exact requirements.

## User Review Required

Please review the proposed architecture below. This is a major overhaul of our current codebase.

> [!IMPORTANT]
> **Open Question 1**: To generate the PDF Incident Reports, I will need to install a new Python library like `fpdf2` or `reportlab`. Are you okay with me adding this dependency?
> **Open Question 2**: Should the "Synthetic Data Generator" and "Fraud Scenarios" be a separate Python script (e.g., `simulator.py`) that you run in the terminal to blast fake transactions at the server, or do you want endpoints in the API to trigger them? (I recommend a separate script).

## Proposed Architecture & Phases

### Phase 1: Data Model Expansion
#### [MODIFY] `models.py`
We will massively expand the `TransactionCreate` Pydantic model to include all 40+ required banking fields (MCC, Device Fingerprint, GPS, Network Type, VPN/Tor flags, etc.). We will use `Optional` fields with sensible defaults so we don't break existing tests.

### Phase 2: Threat Intelligence Simulation
#### [NEW] `threat_intel_mock.py`
Instead of just SQLite, we will create a dedicated module containing massive, realistic (but fictional) Python lists/dictionaries of:
- High-risk ASNs and IPs
- Known phishing domains & disposable emails
- Sanctioned regions & High-risk countries
- Known mule account IDs

### Phase 3: Advanced Rule Engine & Scoring
#### [MODIFY] `anomaly_engine.py`
We will rewrite the engine from a simple boolean check into a **Weighted Scoring System (0-100)**:
- Assign point values to indicators (e.g., `TOR exit node` = +60, `Impossible Travel` = +40, `New Beneficiary` = +15).
- Output a classification: **Low, Medium, High, Critical**.
- Output a detailed audit trail of exactly which rules triggered the score.

### Phase 4: PDF Reporting & Advanced Logging
#### [NEW] `report_generator.py`
We will build a module that takes a "Critical Risk" transaction, compiles the Network, Device, Customer, and Rule breakdown, and outputs a professional PDF Incident Report to a `/reports` directory.
#### [MODIFY] `database.py` & `main.py`
Expand the SQLite transaction schema to log all 40+ fields, execution time, the 0-100 risk score, and the backend response.

### Phase 5: Synthetic Scenario Generator
#### [NEW] `fraud_simulator.py`
A standalone Python script utilizing the `Faker` library. It will contain functions for each of the requested scenarios (e.g., `simulate_sim_swap()`, `simulate_impossible_travel()`). When run, it will generate highly realistic fake payloads and HTTP POST them to our live FastAPI server to demonstrate the engine catching them in real-time.

## Verification Plan
1. I will sequentially execute these 5 phases.
2. I will install `Faker` and `fpdf2`.
3. After completing the backend updates, I will run `fraud_simulator.py` to fire 5 different complex fraud scenarios (like Account Takeover and Impossible Travel) into the live server.
4. We will verify that the terminal outputs a 0-100 score, the WebSocket triggers, and a PDF is generated in the `/reports` folder.
