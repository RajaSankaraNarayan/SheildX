# Sentinel SDK - Master Hackathon Workflow

Congratulations on getting the core infrastructure onto GitHub! Now that the Frontend and Backend are bridged, it is time to orchestrate all 4 team members into a single, cohesive workflow for the final hackathon push.

Here is your exact playbook for integrating **Data & Security** and the **Voice AI**.

---

## Phase 1: Local Environment Sync (All Team Members)
Since everything is on GitHub, your team must sync their environments.

1.  **Frontend Team**: Pulls the repo. Opens `app.js` and changes the `NGROK_DOMAIN` back to `localhost:8000`. Runs their HTML UI in the browser.
2.  **Data & Security**: Pulls the repo. Installs `requirements.txt`. Runs `python -m uvicorn main:app --port 8000`.
3.  **You (Lead)**: Pulls the latest commits. You now all have the exact same starting line.

---

## Phase 2: Integrating Data & Security (The 4th Person)
The Data & Security engineer's job is to make the Anomaly Engine hyper-realistic by feeding it actual threat intelligence.

**Their Workflow:**
1.  **Dataset Hunting**: They find datasets of Indian scam numbers, suspicious IPs (e.g., VPNs, Tor nodes), and common scam keywords (CBI, Customs, Digital Arrest).
2.  **The Injection Script**: They write a Python script that reads their CSV datasets and sends them to your backend using the Admin API:
    ```python
    import requests

    # Example injection script for the Data Engineer
    payload = {"threat_type": "UPI_ID", "value": "scammer_mule_99@ybl"}
    requests.post("http://localhost:8000/api/v1/admin/threat", json=payload)
    ```
3.  **Validation**: Once they run their script, those threats are permanently saved in the local `sentinel.db`. The Anomaly Engine will instantly start blocking transactions to those UPI IDs.

---

## Phase 3: Building the Voice AI (The Final Component)
The final piece of the puzzle is the Voice Assistant that calls the user when a transaction is flagged.

### How it works architecturally:
Currently, when a transaction hits "Critical Risk", your backend generates a PDF and outputs an `ai_instruction` (e.g., *"Ask the user why they are sending a large amount"*).
We need to send that instruction to a Cloud Voice AI service, which will physically dial your cell phone.

### The Voice AI Workflow:
1.  **Choose a Provider**: You have three main options for hackathons:
    *   **Bland AI** (Fastest, easiest API for outbound AI calls).
    *   **Vapi.ai** (Extremely realistic, easy to set up).
    *   **Twilio + OpenAI Realtime** (Most powerful, but hardest to build).
2.  **Get the API Keys**: Sign up for one of the services above and get an API key.
3.  **The Backend Integration (Next Step for You)**: We will write a new function in `main.py` called `trigger_voice_call(ai_instruction, phone_number)`.
4.  **The Trigger**: Inside the `evaluate_transaction` block, right after we generate the PDF, we will execute that function. It will send an HTTP request to the Voice API, and your phone will ring 3 seconds later!

---

## Phase 4: The Golden Path Presentation
When the judges come to your table, this is exactly how your team should present the workflow:

1.  **The Setup (Data Engineer)**: Explains how they injected live Threat Intelligence into the SQLite database.
2.  **The Attack (Frontend)**: The Frontend engineer types a malicious transaction into the Mock Bank UI (e.g., sending ₹50,000 from a Tor IP).
3.  **The Intercept (Backend)**: You explain how the Anomaly Engine caught it in milliseconds, scored it 100/100, and fired the WebSocket to block the UI.
4.  **The Wow Factor (Voice AI)**: *Your cell phone instantly starts ringing on the table.* You put it on speaker, and the AI says: *"Hello, I am the Sentinel Security Assistant. I paused a ₹50,000 transfer because it matches a known digital arrest scam. Are you being threatened?"*
5.  **The Hand-off**: You show the judges the beautifully generated PDF Incident Report.

**Boom. Hackathon won.**
