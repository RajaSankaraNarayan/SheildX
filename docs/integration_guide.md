# Sentinel Architecture & Integration Guide

Welcome to the Sentinel project! This document explains how the 4-person team is separated and provides the exact API contracts you need to connect your frontend apps and Voice AI to the backend.

## Architecture Overview

**1. Backend (FastAPI)**
- **Owner:** Backend Lead
- **Role:** The "Brain". Validates payloads, runs the anomaly engine against transactions, updates database state, and broadcasts real-time WebSocket alerts when fraud is detected.

**2. Voice AI Engine**
- **Owner:** Voice AI Engineer
- **Role:** The "Voice". Converses with the user and uses LLM Function Calling to execute actions on the Backend API. When a transaction is blocked for fraud, it reads the `ai_instruction` returned by the backend to know exactly what to say to the user.

**3. Visual App / Dashboard**
- **Owner:** Frontend/Mobile Developer
- **Role:** The "Face". Connects to the `/ws/alerts` WebSocket to display red warning banners in real-time if a background transaction is flagged. Uses REST APIs to render account balances.

**4. Data / Prompts**
- **Owner:** Prompt/Data Engineer
- **Role:** Refines the anomaly engine's Python heuristic rules and tunes the system prompts for the Voice AI to handle the `ai_instruction` strings correctly.

---

## API Contracts for Integration

The backend is running locally at `http://127.0.0.1:8000`.

### 1. Execute a Transaction (For Voice AI)
The Voice AI uses this endpoint when the user asks to transfer money.
**Endpoint:** `POST /api/v1/transaction`

**Request Payload:**
```json
{
  "account_id": "ACC_1001",
  "amount": 10000,
  "recipient": "IRS Payments",
  "device_ip": "192.168.1.5",
  "is_new_device": false,
  "memo": "Paying back taxes"
}
```

**Response Payload (Normal - No Fraud):**
```json
{
  "message": "Transaction processed",
  "transaction_id": "uuid-here",
  "status": "COMPLETED",
  "risk_score": 0.1,
  "reasons": [],
  "ai_instruction": null
}
```

**Response Payload (Fraud Detected):**
*Note the `ai_instruction` field! Your LLM should read this string and speak it to the user.*
```json
{
  "message": "Transaction processed",
  "transaction_id": "uuid-here",
  "status": "PENDING_REVIEW",
  "risk_score": 0.9,
  "reasons": ["ROUND_NUMBER_LARGE", "SUSPICIOUS_KEYWORD"],
  "ai_instruction": "Refuse the transfer. Gently explain that scammers often use these keywords, and ask if someone is pressuring them."
}
```

---

### 2. Check Account Balance (For Voice AI & Frontend)
Used to greet the user with their balance and language preference.
**Endpoint:** `GET /api/v1/account/{account_id}`

**Response Payload:**
```json
{
  "balance": 150000.0,
  "status": "NORMAL",
  "language_pref": "EN"
}
```

---

### 3. Real-Time Alert Broadcasts (For Frontend App)
The visual app should silently connect to this WebSocket in the background. If a fraud event occurs anywhere, this socket will instantly receive a JSON payload.
**WebSocket URL:** `ws://127.0.0.1:8000/ws/alerts`

**Incoming Payload:**
```json
{
  "event": "FRAUD_ALERT",
  "account_id": "ACC_1001",
  "transaction_id": "uuid-here",
  "vector": "SUSPICIOUS_KEYWORD",
  "reasons": ["ROUND_NUMBER_LARGE", "SUSPICIOUS_KEYWORD"]
}
```

---

### 4. Save Call Transcripts (For Voice AI)
After the phone call ends, the Voice AI pushes the transcript and voice stress score here for auditing.
**Endpoint:** `POST /api/v1/audit/log`

**Request Payload:**
```json
{
  "account_id": "ACC_1001",
  "transaction_id": "uuid-here",
  "transcript": "User sounded panicked and mentioned the IRS...",
  "identified_vector": "IRS_SCAM",
  "voice_stress_score": 0.85
}
```
