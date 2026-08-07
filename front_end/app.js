// Ask your backend lead for this URL! Do not include 'http://' or 'https://' here.
const NGROK_DOMAIN = "overthrow-giddily-capillary.ngrok-free.dev";

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
            is_tor: true, // Set to true to test instant blocking!
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
