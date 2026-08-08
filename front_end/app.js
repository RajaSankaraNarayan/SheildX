// The backend is running locally on port 8000
const API_BASE_URL = "http://127.0.0.1:8000";

document.addEventListener('DOMContentLoaded', () => {
    // 1. Connect to the Sentinel WebSocket for instant alerts
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/alerts`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "FRAUD_ALERT") {
            // FRAUD DETECTED! Trigger the UI blur overlay
            const rulesStr = data.reasons ? data.reasons.join('\n• ') : 'Unknown Anomaly';
            document.getElementById('fraudReason').innerText = `• ${rulesStr}`;
            document.getElementById('fraudOverlay').classList.add('active');

            // Play the AI Auto-Alert!
            const alertText = data.ai_instruction || "Alert! Suspicious activity detected. I have blocked this transaction.";
            fetch(`${API_BASE_URL}/api/v1/tts_alert`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: alertText })
            })
            .then(res => res.blob())
            .then(blob => {
                const audio = new Audio(URL.createObjectURL(blob));
                audio.play();
            }).catch(e => console.error("Auto-alert TTS failed", e));
        }
    };

    ws.onopen = () => {
        console.log("Sentinel SDK WebSocket Connected & Armed.");
    };

    // 2. Handle the Transfer Form Submission
    document.getElementById('transferForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const isTor = document.getElementById('isTor').checked;
        const amount = parseFloat(document.getElementById('amount').value);
        const recipient = document.getElementById('recipient').value;
        const memo = document.getElementById('memo').value;
        const statusEl = document.getElementById('statusMessage');

        statusEl.innerText = "Processing secure transfer...";
        statusEl.style.color = "#94a3b8";

        const payload = {
            account_id: "ACC_IND_001",
            amount: amount,
            recipient: recipient,
            memo: memo,
            device_ip: isTor ? "89.187.160.0" : "192.168.1.10", // Mock IP. 89.187.160.0 is a known Tor node in our DB
            is_new_device: isTor,
            is_tor: isTor,
            merchant_country: isTor ? "RU" : "IN",
            currency: "INR"
        };

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/transaction`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.status === "COMPLETED") {
                statusEl.innerText = "Transfer Successful!";
                statusEl.style.color = "#34d399"; // Green

                // Reset form
                setTimeout(() => {
                    document.getElementById('transferForm').reset();
                    statusEl.innerText = "";
                }, 3000);
            } else if (data.status === "PENDING_REVIEW") {
                statusEl.innerText = "Transaction Blocked by Sentinel.";
                statusEl.style.color = "#ef4444"; // Red
                // The WebSocket will handle the visual overlay
            }
        } catch (error) {
            console.error("Error connecting to backend:", error);
            statusEl.innerText = "Network Error. Could not reach Secure Bank Servers.";
            statusEl.style.color = "#ef4444";
        }
    });
});

// Function to close the alert box
window.dismissAlert = function () {
    document.getElementById('fraudOverlay').classList.remove('active');
    document.getElementById('statusMessage').innerText = "";
    document.getElementById('transferForm').reset();
}

// --- WALKIE TALKIE LOGIC ---
let mediaRecorder;
let audioChunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            sendAudioToAI(audioBlob);
        };
    })
    .catch(err => console.error("Mic error:", err));

function sendAudioToAI(audioBlob) {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");
    
    // Update both modal and FAB status
    const modalText = document.getElementById('aiStatusText');
    const fabText = document.querySelector('.fab-text');
    
    if (modalText) modalText.innerText = "Processing...";
    if (fabText) fabText.innerText = "Processing...";
    
    fetch(`${API_BASE_URL}/api/v1/support_voice`, {
        method: "POST",
        body: formData
    })
    .then(res => res.blob())
    .then(blob => {
        if (modalText) modalText.innerText = "AI is speaking...";
        if (fabText) fabText.innerText = "AI is speaking...";
        
        const audio = new Audio(URL.createObjectURL(blob));
        audio.play();
        audio.onended = () => {
            if (modalText) modalText.innerText = "Standing by.";
            if (fabText) fabText.innerText = "Hold to Ask AI";
        };
    })
    .catch(err => {
        console.error("AI call failed:", err);
        if (modalText) modalText.innerText = "AI Server Offline.";
        if (fabText) fabText.innerText = "AI Server Offline.";
    });
}

const acceptBtn = document.getElementById('acceptCallBtn');
if (acceptBtn) {
    // Reset to "Hold to Talk" style
    acceptBtn.innerText = "Hold to Talk to AI";
    
    acceptBtn.addEventListener('mousedown', () => {
        document.getElementById('aiStatusText').innerText = "Listening...";
        if (mediaRecorder && mediaRecorder.state === "inactive") {
            audioChunks = [];
            mediaRecorder.start();
        }
    });

    acceptBtn.addEventListener('mouseup', () => {
        document.getElementById('aiStatusText').innerText = "Processing...";
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
    });
}

// Global Voice Chat FAB
const voiceFab = document.getElementById('voiceChatFab');
if (voiceFab) {
    const fabText = document.querySelector('.fab-text');
    if (fabText) fabText.innerText = "Hold to Ask AI";
    
    voiceFab.addEventListener('mousedown', (e) => {
        e.preventDefault();
        if (mediaRecorder && mediaRecorder.state === "inactive") {
            audioChunks = [];
            mediaRecorder.start();
            voiceFab.classList.add('recording');
            if (fabText) fabText.innerText = "Listening...";
        }
    });

    voiceFab.addEventListener('mouseup', (e) => {
        e.preventDefault();
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            voiceFab.classList.remove('recording');
            if (fabText) fabText.innerText = "Hold to Ask AI";
        }
    });
}
