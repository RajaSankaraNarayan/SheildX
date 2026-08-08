# Sentinel Voice AI Interception Engine

Sentinel is an ultra-low-latency, multilingual Voice AI Interception Engine designed for real-time banking fraud mitigation. Exposing a bidirectional WebSocket server, it enables frontends (like React web applications) to stream microphone audio to the engine, perform real-time verification and fraud mitigation dialogue, and stream synthesized voice back to the user.

## Pipeline Architecture

```
Audio In (PCM) ──> Silero VAD ──> Sarvam STT (saaras:v3) ──> Gemini 1.5 Flash ──> Sarvam TTS (bulbul:v3) ──> Audio Out (PCM)
```

1. **WebSockets (Single Client)**: Exposes a bidirectional connection on port `8765`. Supports modern `SingleClientWebsocketServerTransport`.
2. **Silero VAD**: Analyzes incoming audio frames locally to detect start/stop of user speech.
3. **Sarvam STT**: Low-latency, multi-dialect transcription model supporting English, Hindi, Tamil, Hinglish, and Tanglish.
4. **Gemini 1.5 Flash**: Orchestrates conversational state machine, enforces voice PIN verification, fraud notification, and card freezing logic.
5. **Sarvam TTS**: High-quality multilingual synthesis utilizing regional voices (e.g., `shubh`) to output calm, reassuring speech.
6. **Audit Publisher**: Records transcripts and security events to compile a session audit payload posted to a B2B fraud reporting service upon session completion.

---

## Folder Structure

```
├── agent.py          # WebSocket server runner & event hook bindings
├── pipeline.py       # Pipecat voice pipeline construction (VAD -> STT -> LLM -> TTS)
├── prompts.py        # Enforces Sentinel security persona & protocols
├── audit.py          # In-memory transcript buffer & asynchronous audit reporter
├── config.py         # Configuration validation & credential loader
├── requirements.txt  # Python package dependencies
├── .env.example      # Template for environment variables
└── .gitignore        # Git exclusion rules
```

---

## Installation & Setup

### 1. Create a Python Virtual Environment

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

*   **On Windows (PowerShell)**:
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
*   **On Windows (CMD)**:
    ```cmd
    .\venv\Scripts\activate.bat
    ```
*   **On macOS/Linux**:
    ```bash
    source venv/bin/activate
    ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration (Environment Variables)

1. Copy the `.env.example` to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your API keys:
   - `GEMINI_API_KEY`: Obtained from Google AI Studio.
   - `SARVAM_API_KEY`: Obtained from the Sarvam AI developer portal.

---

## Running the Server

Run the agent script using:

```bash
python agent.py
```

Upon starting, you will see logging confirming the validation of configurations and indicating that the WebSocket server is listening:
```
2026-08-08 03:00:50,000 [INFO] sentinel.config: Sentinel environment configuration validated successfully.
2026-08-08 03:00:50,001 [INFO] sentinel.config: Target WebSocket: ws://0.0.0.0:8765
2026-08-08 03:00:50,002 [INFO] sentinel.agent: Starting Sentinel Voice AI server at ws://0.0.0.0:8765...
```

---

## Verification

To verify that the server is active and listening on port `8765`, run the following command in PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8765
```

Or on CMD/macOS/Linux:
```bash
netstat -an | grep 8765
```

---

## Troubleshooting

- **Missing API Keys**: The application validates configuration on startup. Ensure that both `GEMINI_API_KEY` and `SARVAM_API_KEY` are defined in your `.env`.
- **Port Conflict**: If port `8765` is already in use, you can specify a different port in `.env` (e.g. `PORT=8766`).
- **Connection Stability**: The engine runs a single-client websocket loop. Disconnections are handled gracefully: the session is immediately torn down, the final audit log is pushed to the audit server, and the WebSocket server is freed to accept a new client connection.
