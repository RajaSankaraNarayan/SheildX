# Sentinel SDK - Frontend Integration Guide

Welcome Frontend Team! This guide contains the exact API specifications you need to connect your UI to the Sentinel Anomaly Engine Backend.

## Overview
Our backend is running Python FastAPI. You will interact with it using two protocols:
1. **HTTP POST**: To send transaction payloads when the user clicks "Transfer".
2. **WebSockets (wss://)**: To listen for instant, real-time Fraud Alerts from the server.

> **Important**: Since we are on different networks, the Backend Lead will provide you with an **Ngrok URL** (e.g., `https://a1b2c3d4.ngrok-free.app`). Replace `<NGROK_URL>` in the examples below with the actual URL.

---

## 1. Connecting to the WebSocket (Real-Time Alerts)
You must establish a WebSocket connection as soon as your app loads. If the backend detects a Critical Fraud risk, it will instantly push a JSON alert through this socket.

### Javascript Implementation
```javascript
// Remove 'https://' and replace with 'wss://' for secure WebSockets
const wsUrl = `wss://<NGROK_URL>/ws/alerts`;
const socket = new WebSocket(wsUrl);

socket.onopen = () => {
    console.log("Connected to Sentinel Fraud WebSocket");
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.event === "FRAUD_ALERT") {
        console.error("🚨 FRAUD INTERCEPTED!", data);
        
        // TODO: TRIGGER YOUR UI BLUR/OVERLAY HERE!
        // Display the triggered rules to the user:
        alert(`Transaction Blocked!\nReasons: ${data.reasons.join(', ')}`);
    }
};

socket.onclose = () => {
    console.log("WebSocket connection lost. Reconnecting...");
    // Add reconnect logic here if needed
};
```

---

## 2. Sending a Transaction
When the user submits the transfer form, send an HTTP POST request to the backend. We recently upgraded the system to accept 40+ enterprise metadata fields. Send as many as you can gather from the browser!

### Endpoint
`POST https://<NGROK_URL>/api/v1/transaction`

### Javascript Implementation
```javascript
async function processTransfer() {
    const payload = {
        // Core Fields (Required)
        account_id: "ACC_IND_001",
        amount: 50000.00,
        recipient: document.getElementById('payeeInput').value,
        device_ip: "10.0.0.5", // You can mock this for the demo
        is_new_device: false,
        memo: document.getElementById('memoInput').value,
        
        // Enhanced Metadata (Optional, but makes the AI smarter)
        currency: "INR",
        merchant_country: "IN",
        os: navigator.platform,
        app_version: navigator.userAgent,
        is_vpn: false,
        is_tor: false,
        latitude: 28.6139,
        longitude: 77.2090
    };

    try {
        const response = await fetch(`https://<NGROK_URL>/api/v1/transaction`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        console.log("Backend Response:", result);

        if (result.status === "COMPLETED") {
            // TODO: Show success message in UI
            console.log("Transfer successful! Risk Score:", result.risk_score);
        } else if (result.status === "PENDING_REVIEW") {
            // The WebSocket will also catch this, but you can handle it here too
            console.warn("Transfer flagged for review.");
        }

    } catch (error) {
        console.error("Transaction Error:", error);
    }
}
```

## Hackathon Demo Tip
If you want to trigger the massive red SDK Interception screen for the judges, try sending a payload where `recipient: "fake_cbi_agent@upi"` and `is_tor: true`. The backend will score it 100/100 and fire the WebSocket alert instantly!
