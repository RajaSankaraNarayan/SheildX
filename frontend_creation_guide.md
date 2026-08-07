# Sentinel SDK - Frontend Creation & Integration Guide

Welcome to the Frontend Team! Your mission is to build the "Mock Bank UI" and integrate the Sentinel Fraud SDK to intercept bad transactions.

This step-by-step guide will show you exactly how to build the UI from scratch using HTML, CSS, and Vanilla JavaScript, and how to connect it to the Backend.

---

## Step 1: Project Setup (Google Firebase / Project IDX / Local)
Since you are building the frontend, you can use any editor (like VS Code or Google Project IDX) and any host (like Firebase Hosting, Vercel, or simply opening the HTML file in your browser).

Create three files in your project folder:
1. `index.html` (The structure)
2. `styles.css` (The beautiful design)
3. `app.js` (The logic and SDK integration)

---

## Step 2: The HTML Structure (index.html)
Copy this code. It creates a simple banking dashboard with a "Transfer Funds" form, and a hidden "SDK Interception Overlay" that we will trigger when fraud is detected.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bharat Secure Bank</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- The Hidden Sentinel SDK Overlay -->
    <div class="overlay" id="fraudOverlay">
        <div class="alert-box">
            <h1>⚠️ TRANSACTION BLOCKED</h1>
            <p>Sentinel SDK intercepted a suspicious transaction.</p>
            <p id="fraudReason" style="color: #ffcccc; margin-top: 10px;"></p>
            <button onclick="dismissAlert()">Acknowledge</button>
        </div>
    </div>

    <!-- The Mock Bank Dashboard -->
    <nav class="navbar">
        <h2>Bharat Secure Bank</h2>
        <span>Welcome, Rajesh</span>
    </nav>

    <main class="dashboard">
        <div class="card">
            <h3>Available Balance</h3>
            <h1>₹5,50,000.00</h1>
        </div>

        <div class="card">
            <h2>Transfer Funds</h2>
            <form id="transferForm">
                <input type="text" id="recipient" placeholder="Payee UPI ID (e.g., scammer@upi)" required>
                <input type="number" id="amount" placeholder="Amount in ₹" required>
                <input type="text" id="memo" placeholder="Remarks (e.g., KYC Update)">
                <button type="submit">Send Money</button>
            </form>
            <p id="statusMessage"></p>
        </div>
    </main>

    <script src="app.js"></script>
</body>
</html>
```

---

## Step 3: The Styling (styles.css)
Copy this CSS to make the bank look professional, and to make the SDK Interception Overlay look like a premium, blurry "Glassmorphism" alert.

```css
* { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
body { margin: 0; background-color: #f4f7f6; color: #333; }

.navbar { background: #0f172a; color: white; padding: 15px 5%; display: flex; justify-content: space-between; }
.dashboard { padding: 30px 5%; max-width: 800px; margin: auto; }
.card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }

input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; }
button { width: 100%; padding: 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
button:hover { background: #2563eb; }

/* Sentinel SDK Overlay (Hidden by default) */
.overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px); /* The Glass blur effect */
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
    opacity: 0; pointer-events: none; transition: 0.3s;
}
.overlay.active { opacity: 1; pointer-events: all; }

.alert-box {
    background: #ef4444; color: white; padding: 40px;
    border-radius: 16px; text-align: center; max-width: 500px;
}
.alert-box button { background: white; color: #ef4444; margin-top: 20px; font-weight: bold; }
```

---

## Step 4: The Integration Logic (app.js)
This is the most important part. Ask the Backend Lead for their **Ngrok URL** and paste it at the top of this file. This script connects to the backend WebSocket and sends the transfer data.

```javascript
// Ask your backend lead for this URL! Do not include 'http://' or 'https://' here.
const NGROK_DOMAIN = "a1b2c3d4.ngrok-free.app";

document.addEventListener('DOMContentLoaded', () => {
    // 1. Connect to the Sentinel WebSocket for instant alerts
    const ws = new WebSocket(`wss://${NGROK_DOMAIN}/ws/alerts`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "FRAUD_ALERT") {
            // FRAUD DETECTED! Trigger the UI blur overlay
            document.getElementById('fraudReason').innerText = `Rules triggered: ${data.reasons.join(', ')}`;
            document.getElementById('fraudOverlay').classList.add('active');
        }
    };

    // 2. Handle the Transfer Form Submission
    document.getElementById('transferForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            account_id: "ACC_IND_001",
            amount: parseFloat(document.getElementById('amount').value),
            recipient: document.getElementById('recipient').value,
            memo: document.getElementById('memo').value,
            device_ip: "10.0.0.5", // Mock IP
            is_new_device: false,
            is_tor: false, // Set to true to test instant blocking!
            merchant_country: "IN",
            currency: "INR"
        };

        try {
            const response = await fetch(`https://${NGROK_DOMAIN}/api/v1/transaction`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            
            if (data.status === "COMPLETED") {
                document.getElementById('statusMessage').innerText = "Transfer Successful!";
                document.getElementById('statusMessage').style.color = "green";
            }
        } catch (error) {
            console.error("Error connecting to backend:", error);
        }
    });
});

// Function to close the alert box
function dismissAlert() {
    document.getElementById('fraudOverlay').classList.remove('active');
}
```

## Step 5: Test It!
1. Ask the backend lead to start the FastAPI server and Ngrok tunnel.
2. Open your `index.html` file in your browser (or host it on Firebase).
3. Try sending ₹50,000 to `fake_cbi@upi`.
4. The backend will instantly flag it, push a WebSocket message, and your screen will turn into a massive red blur!
