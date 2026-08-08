# Enterprise-Grade Fraud Platform Walkthrough

I have completely upgraded the backend to match the 4th team member's requirements. The system is now a highly realistic, enterprise-grade fraud testing platform!

## 1. Massive Data Model Expansion
The transaction endpoint (`POST /api/v1/transaction`) now accepts over 40+ real-world banking metadata fields (e.g., `device_fingerprint`, `is_vpn`, `failed_logins_24h`, `latitude`). All of these are optional, so it is fully backwards-compatible with any existing tests.

## 2. Realistic Threat Intelligence
I created `threat_intel_mock.py` which contains realistic (fictional) datasets for:
- Blacklisted IPs
- Suspicious ASNs and Tor Exit Nodes
- Known Mule Accounts and Phishing Domains
- High-Risk Merchant Categories

## 3. Advanced 0-100 Rule Engine
The `anomaly_engine.py` was completely rewritten. It now uses a **Weighted Scoring System**. 
Instead of a simple "Fraud/Not Fraud", it now:
- Computes a Risk Score from `0` to `100`.
- Classifies the transaction into `Low Risk`, `Medium Risk`, `High Risk`, or `Critical Risk`.
- Returns an exhaustive list of exactly which rules triggered the score (e.g., `["NEW_DEVICE_LOGIN", "BLACKLISTED_IP_DETECTED", "ACCOUNT_DRAIN_ATTEMPT"]`).

## 4. PDF Incident Reporting
Whenever a transaction is flagged as **Critical Risk**, the backend automatically generates a beautiful PDF Incident Report in the new `/reports` folder, detailing the transaction, the network fingerprint, and the triggered rules.

## 5. The Fraud Simulator
I built `fraud_simulator.py`. You can run this file to instantly fire multiple realistic scenarios at the backend.

### How to demo this during your hackathon:
Open your terminal and run:
```powershell
.\venv\Scripts\python.exe fraud_simulator.py
```
This will automatically simulate:
1. **Normal Transaction** (Passes through clean)
2. **Social Engineering / Digital Arrest** (Caught via keywords and high round values)
3. **Impossible Travel** (Caught via foreign IP, Tor network, and new device)
4. **Account Takeover** (Caught via blacklisted IP, VPN, 5 failed logins, and account drain attempt)

You will see exactly how the new engine breaks down and scores these attacks in the terminal output, and you can show the judges the generated PDFs in the `/reports` directory!
